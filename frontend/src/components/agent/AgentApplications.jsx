import React from 'react';
import { FileText, CheckCircle2, XCircle } from 'lucide-react';

export const AgentApplications = ({ applications, handleApprove, handleReject }) => {
  if (applications.length === 0) {
    return (
      <div className="bg-[#1a1d22] p-12 rounded-xl border border-[#1e2127] text-center text-[#9aa0a6] h-full flex flex-col justify-center">
        <FileText size={48} className="mx-auto mb-4 opacity-50" />
        <p className="text-lg">No applications received yet.</p>
        <p className="text-sm mt-2 opacity-70">When renters apply to your listings, they will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {applications.map(app => (
        <div key={app.id} className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6 hover:border-[#f59e0b]/30 transition-colors">
          <div className="flex-1">
            <h3 className="text-[#e8eaed] font-semibold text-lg flex items-center gap-2 mb-1">
              Application for {app.listing_address}
            </h3>
            <p className="text-sm text-[#9aa0a6] mb-4">Submitted on {new Date(app.submitted_at_date).toLocaleDateString()}</p>
            
            <div className="flex flex-wrap gap-3">
              <span className="text-xs bg-[#111418] border border-[#2a2d33] px-3 py-1.5 rounded-full text-[#e8eaed] flex items-center">
                Status: <strong className={`ml-1.5 ${app.application_status === 'A' ? 'text-emerald-400' : app.application_status === 'R' ? 'text-red-400' : 'text-[#f59e0b]'}`}>{app.status_display || app.application_status}</strong>
              </span>
              <span className="text-xs bg-[#111418] border border-[#2a2d33] px-3 py-1.5 rounded-full text-[#e8eaed]">Rent: ${app.rent}/mo</span>
            </div>
          </div>
          
          {app.application_status === 'D' || app.application_status === 'S' || app.application_status === 'submitted' ? (
            <div className="flex gap-3">
              <button onClick={() => handleReject(app.id)} className="flex items-center gap-2 px-5 py-2.5 bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:border-red-500/50 border border-red-500/30 rounded-lg text-sm font-medium transition-all">
                <XCircle size={18} /> Reject
              </button>
              <button onClick={() => handleApprove(app.id)} className="flex items-center gap-2 px-5 py-2.5 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 hover:border-emerald-500/50 border border-emerald-500/30 rounded-lg text-sm font-medium transition-all shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                <CheckCircle2 size={18} /> Approve
              </button>
            </div>
          ) : (
            <div className="text-sm text-[#9aa0a6] bg-[#111418] px-4 py-2 rounded-lg border border-[#2a2d33]">
              Decision Finalized
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
