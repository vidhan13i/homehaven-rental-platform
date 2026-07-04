import React, { useState, useEffect } from 'react';
import { agentApi, applicationApi } from '../../api';
import { LayoutDashboard, Building2, FileText, PlusCircle, Loader2 } from 'lucide-react';
import { AgentOverview } from './AgentOverview';
import { AgentMyListings } from './AgentMyListings';
import { AgentApplications } from './AgentApplications';
import { CreateListingFlow } from './CreateListingFlow';

export const AgentDashboard = ({ user, addToast }) => {
  const [activeTab, setActiveTab] = useState('overview'); // overview, listings, applications, create
  const [listings, setListings] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    if (!user?.isAgent || !user.agentId) return;
    
    setLoading(true);
    try {
      // 1. Fetch Listings
      const listingsResp = await agentApi.getAgentListings(user.agentId);
      const fetchedListings = listingsResp.data.results || [];
      setListings(fetchedListings);
      
      // 2. Fetch Applications for those listings (unit_IDs)
      const allApps = [];
      await Promise.all(fetchedListings.map(async (listing) => {
        if (!listing.unit_ID) return;
        try {
          const appResp = await applicationApi.getApplicationsByUnit(listing.unit_ID);
          // Append listing details to each application for display purposes
          const unitApps = (appResp.data || []).map(app => ({
            ...app,
            listing_address: listing.unit_address || listing.unit_details?.full_address || 'Unknown Address',
            rent: listing.rent
          }));
          allApps.push(...unitApps);
        } catch (e) {
          console.error(`Failed to fetch apps for unit ${listing.unit_ID}`, e);
        }
      }));
      
      // Sort newest first
      setApplications(allApps.sort((a, b) => new Date(b.submitted_at_date) - new Date(a.submitted_at_date)));
    } catch (err) {
      addToast?.('Failed to load agent dashboard data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [user, addToast]);

  const handleApprove = async (appId) => {
    try {
      await applicationApi.approveApplication(appId);
      setApplications(prev => prev.map(a => a.id === appId ? { ...a, application_status: 'A', status_display: 'Approved' } : a));
      addToast?.('Application approved successfully!', 'success');
    } catch (e) {
      addToast?.('Failed to approve application.', 'error');
    }
  };

  const handleReject = async (appId) => {
    try {
      await applicationApi.rejectApplication(appId);
      setApplications(prev => prev.map(a => a.id === appId ? { ...a, application_status: 'R', status_display: 'Rejected' } : a));
      addToast?.('Application rejected.', 'success');
    } catch (e) {
      addToast?.('Failed to reject application.', 'error');
    }
  };

  const handleCreationComplete = () => {
    fetchData();
    setActiveTab('listings');
  };

  if (loading && activeTab !== 'create') {
    return (
      <div className="flex-1 flex items-center justify-center h-full text-[#9aa0a6] bg-[#111418]">
        <Loader2 className="animate-spin mr-2" size={24} /> Loading dashboard...
      </div>
    );
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <AgentOverview listings={listings} applications={applications} />;
      case 'listings':
        return <AgentMyListings listings={listings} />;
      case 'applications':
        return <AgentApplications applications={applications} handleApprove={handleApprove} handleReject={handleReject} />;
      case 'create':
        return <CreateListingFlow user={user} addToast={addToast} onComplete={handleCreationComplete} />;
      default:
        return <AgentOverview listings={listings} applications={applications} />;
    }
  };

  return (
    <div className="flex h-full bg-[#111418] overflow-hidden">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-[#1a1d22] border-r border-[#2a2d33] flex flex-col pt-8 pb-6 px-4">
        <h2 className="text-xl font-bold text-[#e8eaed] mb-8 px-2">Agent Portal</h2>
        
        <nav className="flex flex-col gap-2 flex-1">
          <button 
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium ${activeTab === 'overview' ? 'bg-[#f59e0b]/10 text-[#f59e0b]' : 'text-[#9aa0a6] hover:bg-[#2a2d33] hover:text-[#e8eaed]'}`}
          >
            <LayoutDashboard size={18} /> Overview
          </button>
          
          <button 
            onClick={() => setActiveTab('listings')}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium ${activeTab === 'listings' ? 'bg-[#f59e0b]/10 text-[#f59e0b]' : 'text-[#9aa0a6] hover:bg-[#2a2d33] hover:text-[#e8eaed]'}`}
          >
            <Building2 size={18} /> My Listings
            <span className="ml-auto bg-[#2a2d33] text-[#e8eaed] text-xs py-0.5 px-2 rounded-full">{listings.length}</span>
          </button>
          
          <button 
            onClick={() => setActiveTab('applications')}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium ${activeTab === 'applications' ? 'bg-[#f59e0b]/10 text-[#f59e0b]' : 'text-[#9aa0a6] hover:bg-[#2a2d33] hover:text-[#e8eaed]'}`}
          >
            <FileText size={18} /> Applications
            {applications.length > 0 && (
              <span className="ml-auto bg-[#2a2d33] text-[#e8eaed] text-xs py-0.5 px-2 rounded-full">{applications.length}</span>
            )}
          </button>
        </nav>

        <div className="mt-auto pt-6">
          <button 
            onClick={() => setActiveTab('create')}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all text-sm font-semibold shadow-lg ${activeTab === 'create' ? 'bg-[#f59e0b] text-white shadow-[#f59e0b]/20 scale-[0.98]' : 'bg-gradient-to-r from-[#f59e0b] to-[#d97706] text-white hover:shadow-[#f59e0b]/20 hover:-translate-y-0.5'}`}
          >
            <PlusCircle size={18} /> Create Listing
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto bg-gradient-to-br from-[#111418] to-[#0e1114]">
        <div className="p-10 max-w-7xl mx-auto h-full">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};
