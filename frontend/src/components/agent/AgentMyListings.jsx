import React from 'react';
import { Building2, MapPin } from 'lucide-react';

export const AgentMyListings = ({ listings }) => {
  if (listings.length === 0) {
    return (
      <div className="bg-[#1a1d22] p-12 rounded-xl border border-[#1e2127] text-center text-[#9aa0a6] h-full flex flex-col justify-center">
        <Building2 size={48} className="mx-auto mb-4 opacity-50" />
        <p className="text-lg">You have no active listings.</p>
        <p className="text-sm mt-2 opacity-70">Create a new listing from the sidebar to get started.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {listings.map(listing => (
        <div key={listing.id} className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl overflow-hidden flex flex-col hover:border-[#f59e0b]/50 transition-colors">
          {listing.unit_details?.images?.[0]?.image_url ? (
            <div className="h-48 overflow-hidden relative">
              <img src={listing.unit_details.images[0].image_url} alt="Listing" className="w-full h-full object-cover hover:scale-105 transition-transform duration-500" />
              <div className="absolute top-3 right-3">
                <span className={`text-xs px-2.5 py-1 rounded-full shadow-lg font-medium ${listing.is_listing_verified ? 'bg-emerald-500 text-white' : 'bg-[#111418] text-[#9aa0a6]'}`}>
                  {listing.is_listing_verified ? 'Verified' : 'Pending'}
                </span>
              </div>
            </div>
          ) : (
            <div className="h-48 bg-[#111418] flex items-center justify-center border-b border-[#2a2d33]">
              <Building2 size={32} className="text-[#32363d]" />
            </div>
          )}
          <div className="p-5 flex-1 flex flex-col">
            <h3 className="text-2xl font-bold text-[#e8eaed] mb-1">${listing.rent}<span className="text-sm font-normal text-[#9aa0a6]">/mo</span></h3>
            <p className="text-sm text-[#9aa0a6] flex items-center gap-1.5 mb-2 truncate">
              <MapPin size={14} className="text-[#f59e0b]" /> {listing.unit_address || listing.unit_details?.full_address}
            </p>
            <div className="flex gap-4 text-xs text-[#9aa0a6] mb-5">
              <span>{listing.unit_details?.no_bedrooms} Beds</span>
              <span>{listing.unit_details?.no_bathrooms} Baths</span>
            </div>
            
            <div className="mt-auto pt-4 border-t border-[#1e2127] flex justify-between items-center text-xs text-[#9aa0a6]">
              <span>ID: {listing.id.split('-')[0]}</span>
              <span>Available {new Date(listing.available_date).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
