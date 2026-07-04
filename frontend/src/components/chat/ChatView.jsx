import React, { useEffect } from 'react';
import { ConversationList } from './ConversationList';
import { ChatWindow } from './ChatWindow';
import { useChat } from './ChatContext';

export const ChatView = ({ user }) => {
  const { activeConversationId, loadConversations } = useChat();

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-[#1a1d22]">
      {/* Sidebar - hidden on mobile if a conversation is active */}
      <div className={`
        ${activeConversationId ? 'hidden md:flex' : 'flex'} 
        w-full md:w-auto h-full shrink-0
      `}>
        <ConversationList user={user} />
      </div>

      {/* Main Chat Area - hidden on mobile if NO conversation is active */}
      <div className={`
        ${!activeConversationId ? 'hidden md:flex' : 'flex'} 
        flex-1 h-full min-w-0
      `}>
        <ChatWindow user={user} />
      </div>
    </div>
  );
};
