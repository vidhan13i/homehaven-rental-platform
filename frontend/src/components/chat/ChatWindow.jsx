import React, { useEffect, useRef, useState } from 'react';
import { useChat } from './ChatContext';
import { MessageBubble, TypingIndicator } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ChevronLeft, Info, MoreVertical } from 'lucide-react';

export const ChatWindow = ({ user }) => {
  const { 
    activeConversationId, 
    conversations, 
    messages, 
    sendMessage, 
    sendTyping,
    typingUsers,
    onlineUsers,
    loadMessages,
    setActiveConversation
  } = useChat();

  const [replyTo, setReplyTo] = useState(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const activeConversation = conversations.find(c => c.id === activeConversationId);
  const chatMessages = messages[activeConversationId] || [];
  
  // Determine if the other participant is online
  const otherParticipantId = activeConversation 
    ? (activeConversation.owner_id === user.id ? activeConversation.renter_id : activeConversation.owner_id)
    : null;
  const isOtherUserOnline = onlineUsers.has(otherParticipantId);
  const isOtherUserTyping = (typingUsers[activeConversationId] || []).includes(otherParticipantId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Scroll to bottom on initial load and when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [chatMessages.length]);

  const handleScroll = async (e) => {
    const { scrollTop } = e.target;
    // Load more when scrolled to the top
    if (scrollTop === 0 && !loadingMore && chatMessages.length >= page * 50) {
      setLoadingMore(true);
      const prevHeight = chatContainerRef.current.scrollHeight;
      
      try {
        await loadMessages(activeConversationId, page + 1);
        setPage(p => p + 1);
        
        // Restore scroll position after loading previous messages
        setTimeout(() => {
          if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight - prevHeight;
          }
        }, 0);
      } catch (err) {
        console.error('Failed to load more messages', err);
      } finally {
        setLoadingMore(false);
      }
    }
  };

  const handleSend = async (content, replyId) => {
    try {
      await sendMessage(activeConversationId, content, 'text', replyId);
      setReplyTo(null);
    } catch (e) {
      // Error handled by context
    }
  };

  if (!activeConversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[#1a1d22] text-[#9aa0a6]">
        <div className="w-16 h-16 bg-[#15181e] rounded-full flex items-center justify-center mb-4">
          <Info size={24} className="text-[#5f6368]" />
        </div>
        <p>Select a conversation to start messaging</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-[#1a1d22] h-full relative">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#1e2127] bg-[#15181e] flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-4">
          <button 
            className="md:hidden text-[#5f6368] hover:text-[#e8eaed]"
            onClick={() => setActiveConversation(null)}
          >
            <ChevronLeft size={24} />
          </button>
          
          <div>
            <h3 className="font-semibold text-[#e8eaed] text-[15px]">
              {user?.id === activeConversation.renter_id 
                ? `Owner ${activeConversation.owner_id?.slice(0, 8)}`
                : `Renter ${activeConversation.renter_id?.slice(0, 8)}`}
            </h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div className={`w-2 h-2 rounded-full ${isOtherUserOnline ? 'bg-emerald-500' : 'bg-[#5f6368]'}`} />
              <p className="text-[12px] text-[#9aa0a6]">
                {isOtherUserOnline ? 'Online' : 'Offline'}
              </p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="text-[#5f6368] hover:text-[#e8eaed] transition-colors p-2 hover:bg-[#1a1d22] rounded-full">
            <MoreVertical size={20} />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div 
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-6 scroll-smooth"
      >
        {loadingMore && (
          <div className="text-center py-4">
            <div className="inline-block w-5 h-5 border-2 border-[#5f6368] border-t-[#f59e0b] rounded-full animate-spin" />
          </div>
        )}
        
        {chatMessages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-[#5f6368]">
            <p className="text-sm">This is the start of your conversation.</p>
          </div>
        ) : (
          <div className="flex flex-col justify-end min-h-full">
            {chatMessages.map(msg => (
              <MessageBubble 
                key={msg.id} 
                message={msg} 
                isMine={msg.sender_id === user.id} 
              />
            ))}
            
            {isOtherUserTyping && (
              <div className="mb-4 self-start">
                <TypingIndicator />
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <MessageInput 
        onSend={handleSend} 
        onTyping={sendTyping} 
        replyTo={replyTo}
        onCancelReply={() => setReplyTo(null)}
        disabled={activeConversation.is_blocked}
      />
    </div>
  );
};
