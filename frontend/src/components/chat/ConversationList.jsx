import React from 'react';
import { useChat } from './ChatContext';
import { Search, User, Building2, Calendar, MapPin } from 'lucide-react';

const formatTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const isToday = date.getDate() === now.getDate() && date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
  if (isToday) {
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
};

export const ConversationList = ({ user }) => {
  const { conversations, activeConversationId, setActiveConversation } = useChat();

  return (
    <div className="w-full md:w-80 border-r border-[#1e2127] bg-[#15181e] flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-[#1e2127]">
        <h2 className="text-xl font-bold text-[#e8eaed] mb-4">Messages</h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#5f6368]" size={16} />
          <input
            type="text"
            placeholder="Search conversations..."
            className="w-full bg-[#1a1d22] border border-[#2a2d33] rounded-lg pl-9 pr-4 py-2 text-sm text-[#e8eaed] placeholder-[#4a4d55] focus:outline-none focus:border-[#f59e0b] transition-colors"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {conversations.length === 0 ? (
          <div className="p-6 text-center">
            <p className="text-[#9aa0a6] text-sm">No conversations yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-[#1e2127]">
            {conversations.map(conv => (
              <button
                key={conv.id}
                onClick={() => setActiveConversation(conv.id)}
                className={`w-full text-left p-4 hover:bg-[#1a1d22] transition-colors ${
                  activeConversationId === conv.id ? 'bg-[#1a1d22] border-l-2 border-[#f59e0b]' : 'border-l-2 border-transparent'
                }`}
              >
                <div className="flex gap-3">
                  {/* Avatar Placeholder */}
                  <div className="w-12 h-12 rounded-full bg-[#2a2d33] flex items-center justify-center shrink-0">
                    <User size={20} className="text-[#9aa0a6]" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline mb-1">
                      <p className="text-[14px] font-semibold text-[#e8eaed] truncate">
                        {/* We don't have the other user's name directly in the conversation payload yet, so we use a placeholder or listing info */}
                        {user?.id === conv.renter_id 
                          ? `Owner ${conv.owner_id?.slice(0, 8)}`
                          : `Renter ${conv.renter_id?.slice(0, 8)}`}
                      </p>
                      <span className="text-[11px] text-[#5f6368] shrink-0 ml-2">
                        {formatTime(conv.last_message_at)}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <p className={`text-[13px] truncate ${conv.unread_count > 0 ? 'text-[#e8eaed] font-medium' : 'text-[#9aa0a6]'}`}>
                        {conv.last_message || 'No messages yet'}
                      </p>
                      {conv.unread_count > 0 && (
                        <span className="bg-[#f59e0b] text-[#1a1d22] text-[10px] font-bold px-2 py-0.5 rounded-full ml-2">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
