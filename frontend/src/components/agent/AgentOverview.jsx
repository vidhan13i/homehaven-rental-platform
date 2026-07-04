import React from 'react';
import { Building2, FileText, CheckCircle2, TrendingUp, Users } from 'lucide-react';

export const AgentOverview = ({ listings, applications }) => {
  const approvedApps = applications.filter(a => a.application_status === 'A').length;
  const pendingApps = applications.filter(a => a.application_status === 'D' || a.application_status === 'S' || a.application_status === 'submitted').length;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-[#e8eaed] mb-6">Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Stat Cards */}
        <div className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Building2 size={64} className="text-[#f59e0b]" />
          </div>
          <p className="text-sm text-[#9aa0a6] mb-1 font-medium uppercase tracking-wider">Active Listings</p>
          <p className="text-4xl font-bold text-[#e8eaed]">{listings.length}</p>
        </div>
        
        <div className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <FileText size={64} className="text-blue-500" />
          </div>
          <p className="text-sm text-[#9aa0a6] mb-1 font-medium uppercase tracking-wider">Total Applications</p>
          <p className="text-4xl font-bold text-[#e8eaed]">{applications.length}</p>
        </div>
        
        <div className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <TrendingUp size={64} className="text-[#f59e0b]" />
          </div>
          <p className="text-sm text-[#9aa0a6] mb-1 font-medium uppercase tracking-wider">Pending Review</p>
          <p className="text-4xl font-bold text-[#f59e0b]">{pendingApps}</p>
        </div>
        
        <div className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <CheckCircle2 size={64} className="text-emerald-500" />
          </div>
          <p className="text-sm text-[#9aa0a6] mb-1 font-medium uppercase tracking-wider">Approved Tenants</p>
          <p className="text-4xl font-bold text-emerald-400">{approvedApps}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-[#e8eaed] mb-4 flex items-center gap-2">
            <Building2 size={18} className="text-[#f59e0b]" /> Recent Listings
          </h3>
          <div className="space-y-4">
            {listings.slice(0, 3).map(listing => (
              <div key={listing.id} className="flex items-center gap-4 p-3 hover:bg-[#2a2d33]/50 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-[#2a2d33]">
                <div className="w-16 h-16 rounded-md overflow-hidden bg-[#111418] flex-shrink-0">
                  {listing.unit_details?.images?.[0]?.image_url ? (
                    <img src={listing.unit_details.images[0].image_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center"><Building2 size={16} className="text-[#32363d]" /></div>
                  )}
                </div>
                <div>
                  <p className="text-[#e8eaed] font-medium text-sm truncate">{listing.unit_address || listing.unit_details?.full_address}</p>
                  <p className="text-[#f59e0b] font-semibold text-sm">${listing.rent}/mo</p>
                </div>
              </div>
            ))}
            {listings.length === 0 && <p className="text-sm text-[#9aa0a6] italic">No listings yet.</p>}
          </div>
        </div>

        <div className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-[#e8eaed] mb-4 flex items-center gap-2">
            <Users size={18} className="text-blue-400" /> Recent Applications
          </h3>
          <div className="space-y-4">
            {applications.slice(0, 3).map(app => (
              <div key={app.id} className="flex flex-col gap-1 p-3 hover:bg-[#2a2d33]/50 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-[#2a2d33]">
                <div className="flex justify-between items-start">
                  <p className="text-[#e8eaed] font-medium text-sm truncate pr-4">{app.listing_address}</p>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap ${app.application_status === 'A' ? 'bg-emerald-500/10 text-emerald-400' : app.application_status === 'R' ? 'bg-red-500/10 text-red-400' : 'bg-[#f59e0b]/10 text-[#f59e0b]'}`}>
                    {app.status_display || app.application_status}
                  </span>
                </div>
                <p className="text-xs text-[#9aa0a6]">Submitted {new Date(app.submitted_at_date).toLocaleDateString()}</p>
              </div>
            ))}
            {applications.length === 0 && <p className="text-sm text-[#9aa0a6] italic">No applications yet.</p>}
          </div>
        </div>
      </div>
    </div>
  );
};
