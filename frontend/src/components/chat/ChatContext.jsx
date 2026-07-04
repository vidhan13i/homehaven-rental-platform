import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { chatApi, getAccessToken } from '../../api';

const ChatContext = createContext(null);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within a ChatProvider');
  return context;
};

export const ChatProvider = ({ children, user, addToast }) => {
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState({}); // { convId: [msg1, msg2] }
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [typingUsers, setTypingUsers] = useState({}); // { convId: [userId1, userId2] }
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);

  // Re-fetch conversations
  const loadConversations = useCallback(async () => {
    if (!user) return;
    try {
      const resp = await chatApi.getConversations(1);
      setConversations(resp.data.results);
      
      // Calculate total unread count
      const totalUnread = resp.data.results.reduce((acc, c) => acc + (c.unread_count || 0), 0);
      setUnreadCount(totalUnread);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }, [user]);

  // Load messages for a conversation
  const loadMessages = useCallback(async (conversationId, page = 1) => {
    try {
      const resp = await chatApi.getMessages(conversationId, page);
      const fetchedMessages = resp.data.results.reverse(); // Newest last for display
      
      setMessages(prev => ({
        ...prev,
        [conversationId]: page === 1 
          ? fetchedMessages 
          : [...fetchedMessages, ...(prev[conversationId] || [])]
      }));
      
      return resp.data;
    } catch (err) {
      console.error('Failed to load messages:', err);
      throw err;
    }
  }, []);

  // WebSocket Connection Manager
  const connectWebSocket = useCallback((conversationId) => {
    if (!user || !conversationId) return;
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // If already connected to THIS conversation, do nothing
      if (wsRef.current.conversationId === conversationId) return;
      // Otherwise, close the old one
      wsRef.current.close();
    }

    const token = getAccessToken();
    if (!token) return;

    const wsUrl = `ws://localhost:8000/ws/chat/${conversationId}/?token=${token}`;
    const ws = new WebSocket(wsUrl);
    ws.conversationId = conversationId;

    ws.onopen = () => {
      console.log(`[WS] Connected to chat ${conversationId}`);
      setIsConnected(true);
      
      // Start heartbeat
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, 30000); // 30s heartbeat
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWsMessage(data, conversationId);
    };

    ws.onclose = (event) => {
      console.log(`[WS] Disconnected (code ${event.code})`);
      setIsConnected(false);
      clearInterval(heartbeatIntervalRef.current);
      
      // Exponential backoff reconnect if not unauthorized
      if (event.code !== 4001 && event.code !== 4003) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket(conversationId);
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, [user]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    setIsConnected(false);
  }, []);

  // Handle incoming WS events
  const handleWsMessage = useCallback((data, conversationId) => {
    switch (data.type) {
      case 'connected':
        if (data.other_user_online) {
          setOnlineUsers(prev => {
            const next = new Set(prev);
            next.add(data.other_user_id);
            return next;
          });
        }
        break;

      case 'receive_message':
        setMessages(prev => {
          const chatMsgs = prev[conversationId] || [];
          // Avoid duplicate appends
          if (chatMsgs.find(m => m.id === data.message.id)) return prev;
          return { ...prev, [conversationId]: [...chatMsgs, data.message] };
        });
        
        // Update conversation list last message
        setConversations(prev => {
          const updated = [...prev];
          const idx = updated.findIndex(c => c.id === conversationId);
          if (idx !== -1) {
            updated[idx] = { 
              ...updated[idx], 
              last_message: data.message.content, 
              last_message_at: data.message.created_at,
              unread_count: (updated[idx].unread_count || 0) + 1
            };
            // Move to top
            const [moved] = updated.splice(idx, 1);
            updated.unshift(moved);
          }
          return updated;
        });

        // Increment total unread if this isn't the active chat
        if (activeConversationId !== conversationId) {
          setUnreadCount(prev => prev + 1);
        } else {
          // If active, mark it as read immediately
          chatApi.markRead(conversationId).catch(console.error);
        }
        break;

      case 'user_typing':
        setTypingUsers(prev => {
          const current = prev[conversationId] || [];
          if (!current.includes(data.user_id)) {
            return { ...prev, [conversationId]: [...current, data.user_id] };
          }
          return prev;
        });
        break;

      case 'user_stop_typing':
        setTypingUsers(prev => {
          const current = prev[conversationId] || [];
          return { ...prev, [conversationId]: current.filter(id => id !== data.user_id) };
        });
        break;

      case 'user_online':
        setOnlineUsers(prev => {
          const next = new Set(prev);
          next.add(data.user_id);
          return next;
        });
        break;

      case 'user_offline':
        setOnlineUsers(prev => {
          const next = new Set(prev);
          next.delete(data.user_id);
          return next;
        });
        break;
        
      case 'message_seen':
        setMessages(prev => {
          const chatMsgs = prev[conversationId] || [];
          const updatedMsgs = chatMsgs.map(m => 
            m.id === data.message_id ? { ...m, seen_at: new Date().toISOString() } : m
          );
          return { ...prev, [conversationId]: updatedMsgs };
        });
        break;

      case 'message_deleted':
        setMessages(prev => {
          const chatMsgs = prev[conversationId] || [];
          const updatedMsgs = chatMsgs.map(m => 
            m.id === data.message_id ? { ...m, is_deleted: true, content: '', display_content: 'This message was deleted.' } : m
          );
          return { ...prev, [conversationId]: updatedMsgs };
        });
        break;

      case 'message_edited':
        setMessages(prev => {
          const chatMsgs = prev[conversationId] || [];
          const updatedMsgs = chatMsgs.map(m => 
            m.id === data.message.id ? data.message : m
          );
          return { ...prev, [conversationId]: updatedMsgs };
        });
        break;
        
      case 'error':
        addToast?.(data.detail, 'error');
        break;
    }
  }, [activeConversationId, addToast]);

  // Send message
  const sendMessage = useCallback((conversationId, content, messageType = 'text', replyToId = null) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addToast?.('Not connected to chat', 'error');
      return;
    }
    
    // We send via REST so we get the full message object back immediately (with ID)
    // Then the WS broadcasts it to others.
    return chatApi.sendMessage({
      conversation: conversationId,
      content,
      message_type: messageType,
      reply_to: replyToId ? { id: replyToId } : null
    }).then(resp => {
      // Add to our own state immediately, but check for duplicates in case WS beat us
      setMessages(prev => {
        const chatMsgs = prev[conversationId] || [];
        if (chatMsgs.find(m => m.id === resp.data.id)) return prev;
        return {
          ...prev,
          [conversationId]: [...chatMsgs, resp.data]
        };
      });
      
      // Update conversation list last message
      setConversations(prev => {
        const updated = [...prev];
        const idx = updated.findIndex(c => c.id === conversationId);
        if (idx !== -1) {
          updated[idx] = { 
            ...updated[idx], 
            last_message: content, 
            last_message_at: resp.data.created_at
          };
          const [moved] = updated.splice(idx, 1);
          updated.unshift(moved);
        }
        return updated;
      });
      return resp.data;
    }).catch(err => {
      addToast?.('Failed to send message', 'error');
      throw err;
    });
  }, [addToast]);

  const sendTyping = useCallback((isTyping) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: isTyping ? 'typing' : 'stop_typing' }));
    }
  }, []);

  const markConversationRead = useCallback(async (conversationId) => {
    try {
      await chatApi.markRead(conversationId);
      
      // Update local unread count
      setConversations(prev => {
        const updated = [...prev];
        const idx = updated.findIndex(c => c.id === conversationId);
        if (idx !== -1 && updated[idx].unread_count > 0) {
          setUnreadCount(count => Math.max(0, count - updated[idx].unread_count));
          updated[idx] = { ...updated[idx], unread_count: 0 };
        }
        return updated;
      });
    } catch (err) {
      console.error('Failed to mark read', err);
    }
  }, []);

  // Set active conversation
  const setActiveConversation = useCallback(async (conversationId) => {
    setActiveConversationId(conversationId);
    if (conversationId) {
      await loadMessages(conversationId, 1);
      markConversationRead(conversationId);
      connectWebSocket(conversationId);
    } else {
      disconnectWebSocket();
    }
  }, [loadMessages, markConversationRead, connectWebSocket, disconnectWebSocket]);

  // Initial load
  useEffect(() => {
    if (user) {
      loadConversations();
    } else {
      setConversations([]);
      setMessages({});
      setActiveConversationId(null);
      setUnreadCount(0);
      disconnectWebSocket();
    }
  }, [user, loadConversations, disconnectWebSocket]);

  // Cleanup on unmount
  useEffect(() => {
    return () => disconnectWebSocket();
  }, [disconnectWebSocket]);

  return (
    <ChatContext.Provider value={{
      conversations,
      messages,
      activeConversationId,
      unreadCount,
      typingUsers,
      onlineUsers,
      isConnected,
      setActiveConversation,
      sendMessage,
      sendTyping,
      loadConversations,
      loadMessages,
      markConversationRead,
      setConversations
    }}>
      {children}
    </ChatContext.Provider>
  );
};
