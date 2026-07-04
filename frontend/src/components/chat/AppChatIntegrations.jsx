import React from 'react';
import { Mail, MessageSquare } from 'lucide-react';
import { useChat } from './ChatContext';
import { chatApi, agentApi, profileApi } from '../../api';

export const MessagesNavBtn = ({ currentView, setCurrentView }) => {
  const { unreadCount } = useChat();
  const active = currentView === 'chat';
  
  return (
    <button
      onClick={() => setCurrentView('chat')}
      className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-all ${
        active ? 'bg-[#f59e0b]/10 text-[#f59e0b] font-medium' : 'text-[#6b7280] hover:text-[#e8eaed] hover:bg-[#1e2127]'
      }`}
    >
      <Mail size={16} strokeWidth={active ? 2.5 : 1.75} />
      <span className="flex-1 text-left">Messages</span>
      {unreadCount > 0 && (
        <span className="bg-[#f59e0b] text-[#1a1d22] px-1.5 py-0.5 rounded-full text-[10px] font-bold">
          {unreadCount}
        </span>
      )}
      {active && <span className="w-1 h-1 rounded-full bg-[#f59e0b]" />}
    </button>
  );
};

export const ContactOwnerBtn = ({ listing, user, goToAuth, setCurrentView, addToast }) => {
  const { setActiveConversation } = useChat();

  const handleContact = async () => {
    if (!user) {
      goToAuth();
      return;
    }
    
    const agentId = listing.unit_details?.agent_ID;
    if (!agentId) {
      addToast('Cannot contact owner: No agent assigned.', 'error');
      return;
    }

    try {
      // 1. Fetch agent to get email
      const agentResp = await agentApi.getAgent(agentId);
      const agentEmail = agentResp.data.email;

      // 2. Fetch profile to get User UUID
      const profileResp = await profileApi.getProfileByEmail(agentEmail);
      const ownerId = profileResp.data.id;
      
      if (ownerId === user.id) {
        addToast('You cannot message yourself.', 'error');
        return;
      }

      const resp = await chatApi.createConversation({
        listing_id: listing.id,
        owner_id: ownerId,
        renter_id: user.id
      });
      
      setCurrentView('chat');
      setActiveConversation(resp.data.id);
    } catch (err) {
      console.error(err);
      addToast('Failed to start conversation. Agent may not have a registered profile.', 'error');
    }
  };

  return (
    <button
      onClick={handleContact}
      className="w-full mt-2 text-[13px] text-[#e8eaed] bg-[#f59e0b]/10 border border-[#f59e0b]/30 hover:bg-[#f59e0b]/20 py-2.5 rounded-lg transition-all flex items-center justify-center gap-1.5 font-medium"
    >
      <MessageSquare size={13} className="text-[#f59e0b]" /> Contact Owner
    </button>
  );
};
