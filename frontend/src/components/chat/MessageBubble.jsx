import React from 'react';
import { Check, CheckCheck, Edit2, Reply, Smile, MoreVertical } from 'lucide-react';

const formatTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
};

export const TypingIndicator = () => (
  <div className="flex gap-1 items-center px-4 py-3 bg-[#1e2127] rounded-2xl rounded-tl-sm w-fit">
    <div className="w-1.5 h-1.5 bg-[#5f6368] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
    <div className="w-1.5 h-1.5 bg-[#5f6368] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
    <div className="w-1.5 h-1.5 bg-[#5f6368] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
  </div>
);

export const MessageBubble = ({ message, isMine }) => {
  const isDeleted = message.is_deleted;
  
  return (
    <div className={`flex flex-col w-full mb-4 ${isMine ? 'items-end' : 'items-start'}`}>
      <div className="group relative flex items-center gap-2 max-w-[75%]">
        
        {/* Action Menu (visible on hover) */}
        {isMine && !isDeleted && (
          <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
            <button className="p-1.5 text-[#5f6368] hover:text-[#e8eaed] hover:bg-[#2a2d33] rounded-full transition-colors" title="Reply">
              <Reply size={14} />
            </button>
            <button className="p-1.5 text-[#5f6368] hover:text-[#e8eaed] hover:bg-[#2a2d33] rounded-full transition-colors" title="React">
              <Smile size={14} />
            </button>
            <button className="p-1.5 text-[#5f6368] hover:text-[#e8eaed] hover:bg-[#2a2d33] rounded-full transition-colors" title="More">
              <MoreVertical size={14} />
            </button>
          </div>
        )}

        {/* Message Bubble */}
        <div 
          className={`px-4 py-2.5 rounded-2xl relative ${
            isDeleted
              ? 'bg-[#1e2127] border border-[#2a2d33] text-[#5f6368] italic'
              : isMine 
                ? 'bg-[#f59e0b] text-[#1a1d22] rounded-tr-sm' 
                : 'bg-[#1e2127] text-[#e8eaed] rounded-tl-sm'
          }`}
        >
          {/* Reply Context */}
          {!isDeleted && message.reply_to && (
            <div className={`text-[11px] mb-1 pl-2 border-l-2 opacity-75 truncate ${isMine ? 'border-[#1a1d22]' : 'border-[#f59e0b]'}`}>
              {message.reply_to.content}
            </div>
          )}
          
          <p className="text-[14px] leading-relaxed break-words whitespace-pre-wrap">
            {message.display_content}
          </p>
          
          {/* Attachment Preview (placeholder) */}
          {!isDeleted && message.attachment && (
            <div className="mt-2 text-xs opacity-80 flex items-center gap-1 bg-black/10 p-1.5 rounded">
              📎 {message.attachment_name || 'Attachment'}
            </div>
          )}

          {/* Reactions */}
          {!isDeleted && message.reactions && Object.keys(message.reactions).length > 0 && (
            <div className="absolute -bottom-3 -right-2 flex gap-1 z-10">
              {Object.entries(message.reactions).map(([emoji, users]) => (
                <span key={emoji} className="bg-[#2a2d33] border border-[#1e2127] rounded-full px-1.5 py-0.5 text-[10px] shadow-sm flex items-center gap-1">
                  {emoji} <span className="text-[#9aa0a6]">{users.length}</span>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Action Menu for received messages */}
        {!isMine && !isDeleted && (
          <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
            <button className="p-1.5 text-[#5f6368] hover:text-[#e8eaed] hover:bg-[#2a2d33] rounded-full transition-colors" title="Reply">
              <Reply size={14} />
            </button>
            <button className="p-1.5 text-[#5f6368] hover:text-[#e8eaed] hover:bg-[#2a2d33] rounded-full transition-colors" title="React">
              <Smile size={14} />
            </button>
          </div>
        )}
      </div>

      {/* Meta Info */}
      <div className={`flex items-center gap-1.5 mt-1 mx-1 ${isDeleted ? 'hidden' : ''}`}>
        <span className="text-[11px] text-[#5f6368]">
          {formatTime(message.created_at)}
        </span>
        {message.is_edited && (
          <span className="text-[10px] text-[#5f6368] flex items-center gap-0.5">
            <Edit2 size={10} /> Edited
          </span>
        )}
        {isMine && (
          <span className="text-[#5f6368]">
            {message.seen_at ? (
              <CheckCheck size={14} className="text-blue-400" />
            ) : message.delivered_at ? (
              <CheckCheck size={14} />
            ) : (
              <Check size={14} />
            )}
          </span>
        )}
      </div>
    </div>
  );
};
