import React, { useState } from 'react';
import { agentApi } from '../../api';
import { Building2, UploadCloud, FileText, CheckCircle2, ChevronRight, Loader2 } from 'lucide-react';

export const CreateListingFlow = ({ user, addToast, onComplete }) => {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Unit Data
  const [address, setAddress] = useState('');
  const [unitNo, setUnitNo] = useState('');
  const [beds, setBeds] = useState(1);
  const [baths, setBaths] = useState(1);
  const [desc, setDesc] = useState('');
  const [furnishing, setFurnishing] = useState('unfurnished'); // unfurnished, semi, fully

  // Images Data
  const [images, setImages] = useState([]);
  
  // Listing Data
  const [rent, setRent] = useState('');
  const [deposit, setDeposit] = useState('');
  const [availableDate, setAvailableDate] = useState('');

  const handleImageChange = (e) => {
    if (e.target.files) {
      setImages(Array.from(e.target.files));
    }
  };

  const handleNext = () => setStep(prev => prev + 1);
  const handleBack = () => setStep(prev => prev - 1);

  const handleSubmit = async () => {
    setError('');
    setSubmitting(true);
    
    try {
      const fd = new FormData();
      
      // Unit Data
      fd.append('full_address', address);
      fd.append('unit_no', unitNo);
      fd.append('unit_slug', `unit-${Math.floor(Math.random()*10000)}-${unitNo.toLowerCase()}`);
      fd.append('no_bedrooms', beds);
      fd.append('no_bathrooms', baths);
      fd.append('description', desc);
      fd.append('is_furnished', furnishing === 'fully');
      fd.append('is_semi_furnished', furnishing === 'semi');
      fd.append('agent_ID', user.agentId);

      // Listing Data
      fd.append('rent', parseFloat(rent));
      fd.append('deposit_amount', parseFloat(deposit));
      fd.append('available_date', availableDate);
      fd.append('publish_date', new Date().toISOString().split('T')[0]);
      fd.append('closing_date', new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().split('T')[0]);
      fd.append('is_listing_verified', false);

      // Images
      images.forEach(img => {
        fd.append('images', img); // getlist('images') in django
      });
      
      await agentApi.createFullListing(fd);
      
      addToast('Listing created successfully!', 'success');
      onComplete(); // Triggers refresh and navigates to My Listings
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create listing. Please check your inputs.');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8">
      <h2 className="text-2xl font-bold text-[#e8eaed] mb-6">Create New Listing</h2>
      
      {/* Progress Steps */}
      <div className="flex items-center mb-10 text-sm font-medium">
        <div className={`flex items-center ${step >= 1 ? 'text-[#f59e0b]' : 'text-[#6b7280]'}`}>
          <span className={`w-8 h-8 flex items-center justify-center rounded-full border-2 ${step >= 1 ? 'border-[#f59e0b] bg-[#f59e0b]/10' : 'border-[#2a2d33] bg-[#1a1d22]'} mr-2`}>1</span>
          Unit Details
        </div>
        <div className={`flex-1 border-t-2 mx-4 ${step >= 2 ? 'border-[#f59e0b]' : 'border-[#2a2d33]'}`}></div>
        <div className={`flex items-center ${step >= 2 ? 'text-[#f59e0b]' : 'text-[#6b7280]'}`}>
          <span className={`w-8 h-8 flex items-center justify-center rounded-full border-2 ${step >= 2 ? 'border-[#f59e0b] bg-[#f59e0b]/10' : 'border-[#2a2d33] bg-[#1a1d22]'} mr-2`}>2</span>
          Photos
        </div>
        <div className={`flex-1 border-t-2 mx-4 ${step >= 3 ? 'border-[#f59e0b]' : 'border-[#2a2d33]'}`}></div>
        <div className={`flex items-center ${step >= 3 ? 'text-[#f59e0b]' : 'text-[#6b7280]'}`}>
          <span className={`w-8 h-8 flex items-center justify-center rounded-full border-2 ${step >= 3 ? 'border-[#f59e0b] bg-[#f59e0b]/10' : 'border-[#2a2d33] bg-[#1a1d22]'} mr-2`}>3</span>
          Terms
        </div>
      </div>

      <div className="bg-[#1a1d22] border border-[#2a2d33] rounded-xl p-8">
        {error && <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-sm">{error}</div>}

        {step === 1 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-[#e8eaed] flex items-center gap-2 mb-4">
              <Building2 size={20} className="text-[#f59e0b]" /> Property Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="col-span-full">
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Full Address</label>
                <input type="text" value={address} onChange={e => setAddress(e.target.value)} placeholder="e.g. 123 Main St, New York, NY 10001" className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Unit Number</label>
                <input type="text" value={unitNo} onChange={e => setUnitNo(e.target.value)} placeholder="e.g. Apt 4B" className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Furnishing</label>
                <select value={furnishing} onChange={e => setFurnishing(e.target.value)} className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all">
                  <option value="unfurnished">Unfurnished</option>
                  <option value="semi">Semi-Furnished</option>
                  <option value="fully">Fully Furnished</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Bedrooms</label>
                <input type="number" min="0" value={beds} onChange={e => setBeds(parseInt(e.target.value))} className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Bathrooms</label>
                <input type="number" min="0" step="0.5" value={baths} onChange={e => setBaths(parseFloat(e.target.value))} className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
              <div className="col-span-full">
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Description</label>
                <textarea rows="4" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Describe the property..." className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
            </div>
            <div className="mt-8 flex justify-end">
              <button onClick={handleNext} disabled={!address || !unitNo || !desc} className="bg-[#f59e0b] hover:bg-[#d97706] text-white px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center">
                Next <ChevronRight size={18} className="ml-1" />
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-[#e8eaed] flex items-center gap-2 mb-4">
              <UploadCloud size={20} className="text-[#f59e0b]" /> Property Photos
            </h3>
            <div className="border-2 border-dashed border-[#2a2d33] rounded-xl p-10 text-center bg-[#111418]">
              <UploadCloud size={48} className="mx-auto text-[#6b7280] mb-4" />
              <p className="text-[#9aa0a6] mb-4">Drag and drop photos here, or click to select files.</p>
              <input type="file" multiple accept="image/*" onChange={handleImageChange} className="block w-full text-sm text-[#9aa0a6] file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#f59e0b]/10 file:text-[#f59e0b] hover:file:bg-[#f59e0b]/20 cursor-pointer mx-auto max-w-sm" />
            </div>
            {images.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-[#e8eaed] font-medium mb-2">{images.length} file(s) selected:</p>
                <ul className="text-sm text-[#9aa0a6] list-disc list-inside">
                  {images.map((img, i) => <li key={i}>{img.name}</li>)}
                </ul>
              </div>
            )}
            <div className="mt-8 flex justify-between">
              <button onClick={handleBack} className="bg-[#2a2d33] hover:bg-[#32363d] text-[#e8eaed] px-6 py-2.5 rounded-lg font-medium transition-colors">Back</button>
              <button onClick={handleNext} className="bg-[#f59e0b] hover:bg-[#d97706] text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center">
                Next <ChevronRight size={18} className="ml-1" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-[#e8eaed] flex items-center gap-2 mb-4">
              <FileText size={20} className="text-[#f59e0b]" /> Listing Terms
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Monthly Rent ($)</label>
                <input type="number" min="0" value={rent} onChange={e => setRent(e.target.value)} placeholder="1500" className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Deposit Amount ($)</label>
                <input type="number" min="0" value={deposit} onChange={e => setDeposit(e.target.value)} placeholder="1500" className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
              <div className="col-span-full">
                <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wider">Available Date</label>
                <input type="date" value={availableDate} onChange={e => setAvailableDate(e.target.value)} className="w-full bg-[#111418] border border-[#2a2d33] text-[#e8eaed] rounded-lg px-4 py-2.5 focus:border-[#f59e0b] focus:ring-1 focus:ring-[#f59e0b] outline-none transition-all" required />
              </div>
            </div>
            
            <div className="mt-8 flex justify-between">
              <button onClick={handleBack} disabled={submitting} className="bg-[#2a2d33] hover:bg-[#32363d] text-[#e8eaed] px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50">Back</button>
              <button onClick={handleSubmit} disabled={!rent || !deposit || !availableDate || submitting} className="bg-emerald-500 hover:bg-emerald-600 text-white px-8 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center">
                {submitting ? <><Loader2 className="animate-spin mr-2" size={18} /> Publishing...</> : <><CheckCircle2 size={18} className="mr-2" /> Publish Listing</>}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
