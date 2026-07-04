import React, { useState, useRef, useEffect } from 'react';
import { Send, Smile, Paperclip, X } from 'lucide-react';

export const MessageInput = ({ onSend, onTyping, disabled = false, replyTo = null, onCancelReply }) => {
  const [content, setContent] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (replyTo && inputRef.current) {
      inputRef.current.focus();
    }
  }, [replyTo]);

  const handleChange = (e) => {
    setContent(e.target.value);
    
    if (!isTyping) {
      setIsTyping(true);
      onTyping(true);
    }
    
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      onTyping(false);
    }, 2000);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!content.trim() || disabled) return;
    
    onSend(content.trim(), replyTo?.id);
    setContent('');
    
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    setIsTyping(false);
    onTyping(false);
  };

  return (
    <div className="border-t border-[#1e2127] bg-[#15181e] p-4">
      {replyTo && (
        <div className="mb-2 px-3 py-2 bg-[#1a1d22] border-l-2 border-[#f59e0b] rounded flex justify-between items-start">
          <div>
            <p className="text-[11px] font-semibold text-[#f59e0b] mb-0.5">Replying to message</p>
            <p className="text-[12px] text-[#9aa0a6] truncate max-w-[300px]">{replyTo.content}</p>
          </div>
          <button onClick={onCancelReply} className="text-[#5f6368] hover:text-[#e8eaed]">
            <X size={14} />
          </button>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <button type="button" className="p-2.5 text-[#5f6368] hover:text-[#e8eaed] hover:bg-[#1a1d22] rounded-full transition-colors mb-0.5" disabled={disabled}>
          <Paperclip size={20} />
        </button>
        
        <div className="flex-1 bg-[#1a1d22] border border-[#2a2d33] rounded-2xl flex items-center px-1 focus-within:border-[#f59e0b] transition-colors">
          <input
            ref={inputRef}
            type="text"
            value={content}
            onChange={handleChange}
            placeholder="Type a message..."
            className="w-full bg-transparent border-none py-3 px-3 text-[14px] text-[#e8eaed] placeholder-[#4a4d55] focus:outline-none focus:ring-0"
            disabled={disabled}
          />
          <button type="button" className="p-2 text-[#5f6368] hover:text-[#f59e0b] transition-colors mr-1" disabled={disabled}>
            <Smile size={20} />
          </button>
        </div>
        
        <button 
          type="submit" 
          disabled={!content.trim() || disabled}
          className="p-3 bg-[#f59e0b] text-[#1a1d22] rounded-full hover:bg-[#d97706] disabled:opacity-50 disabled:cursor-not-allowed transition-colors mb-0.5"
        >
          <Send size={18} className="ml-0.5" />
        </button>
      </form>
    </div>
  );
};
