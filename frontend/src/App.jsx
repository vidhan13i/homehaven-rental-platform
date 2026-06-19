import React, { useState, useEffect } from 'react';
import { api, getAccessToken, setTokens, clearTokens } from './api';
import {
  Home, ClipboardList, LayoutDashboard, LogOut, AlertCircle,
  ChevronLeft, ChevronRight, SlidersHorizontal, Upload, Star,
  FileText, CheckCircle2, ArrowRight, BadgeCheck, Mail, FileUp, KeyRound
} from 'lucide-react';

const decodeJWT = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64).split('').map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) { return null; }
};

// Small reusable input component so we don't repeat classes everywhere
const Field = ({ label, children }) => (
  <div>
    <label className="block text-sm text-[#9aa0a6] mb-1.5">{label}</label>
    {children}
  </div>
);

const inputCls = "w-full bg-[#1a1d22] border border-[#2a2d33] rounded-lg px-3.5 py-2.5 text-sm text-[#e8eaed] placeholder-[#5f6368] focus:outline-none focus:border-[#f59e0b] transition-colors";

const StatusBadge = ({ status }) => {
  const map = {
    approved:  { color: 'text-emerald-400 bg-emerald-950/50 border-emerald-800/40', label: 'Approved' },
    rejected:  { color: 'text-red-400 bg-red-950/50 border-red-800/40',             label: 'Rejected' },
    submitted: { color: 'text-sky-400 bg-sky-950/50 border-sky-800/40',              label: 'Under Review' },
    draft:     { color: 'text-[#9aa0a6] bg-[#1a1d22] border-[#2a2d33]',             label: 'Draft' },
  };
  const s = map[status] || map.draft;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${s.color}`}>
      {s.label}
    </span>
  );
};

export default function App() {
  const [currentView, setCurrentView] = useState('listings');

  // Auth
  const [user, setUser]             = useState(null);
  const [authMode, setAuthMode]     = useState('login');
  const [authError, setAuthError]   = useState('');
  const [otpEmail, setOtpEmail]     = useState('');
  const [usernameInput, setUsernameInput] = useState('');
  const [emailInput, setEmailInput]       = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [firstNameInput, setFirstNameInput] = useState('');
  const [lastNameInput, setLastNameInput]   = useState('');
  const [otpInput, setOtpInput]     = useState('');
  const [otpMessage, setOtpMessage] = useState('');

  // Listings
  const [listings, setListings]           = useState([]);
  const [listingsCount, setListingsCount] = useState(0);
  const [currentPage, setCurrentPage]     = useState(1);
  const [nextPageUrl, setNextPageUrl]     = useState(null);
  const [prevPageUrl, setPrevPageUrl]     = useState(null);
  const [loadingListings, setLoadingListings] = useState(false);
  const [rentMin, setRentMin]   = useState('');
  const [rentMax, setRentMax]   = useState('');
  const [bedrooms, setBedrooms] = useState('');
  const [bathrooms, setBathrooms] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Wizard
  const [selectedListing, setSelectedListing] = useState(null);
  const [wizardStep, setWizardStep]       = useState(1);
  const [applicantId, setApplicantId]     = useState(null);
  const [wizardError, setWizardError]     = useState('');
  const [employer, setEmployer]           = useState('');
  const [jobTitle, setJobTitle]           = useState('');
  const [creditScore, setCreditScore]     = useState('');
  const [income, setIncome]               = useState('');
  const [savings, setSavings]             = useState('');
  const [moveInDate, setMoveInDate]       = useState('2026-07-01');
  const [reason, setReason]               = useState('');
  const [hasRentedBefore, setHasRentedBefore] = useState(false);
  const [maritalStatus, setMaritalStatus] = useState(false);
  const [leaseTerm, setLeaseTerm]         = useState('12');
  const [residentInfo, setResidentInfo]   = useState('Applicant will reside in unit');
  const [docLabel, setDocLabel]           = useState('Pay Stub');
  const [selectedFile, setSelectedFile]   = useState(null);
  const [uploadedDocs, setUploadedDocs]   = useState([]);
  const [uploadingDoc, setUploadingDoc]   = useState(false);

  // Dashboard
  const [marketStats, setMarketStats]     = useState(null);
  const [reviewStats, setReviewStats]     = useState(null);
  const [myApplications, setMyApplications] = useState([]);
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      const decoded = decodeJWT(token);
      if (decoded && decoded.exp * 1000 > Date.now()) {
        setUser({ id: decoded.user_id, username: decoded.username, email: decoded.email });
      } else { clearTokens(); }
    }
  }, []);

  useEffect(() => { if (currentView === 'listings') fetchListings(); }, [currentView, currentPage]);
  useEffect(() => { if (currentView === 'dashboard' && user) fetchDashboardData(); }, [currentView, user]);

  const fetchListings = async () => {
    setLoadingListings(true);
    try {
      let url = `/api/listings/listings/public/?page=${currentPage}`;
      if (rentMin) url += `&rent_min=${rentMin}`;
      if (rentMax) url += `&rent_max=${rentMax}`;
      if (bedrooms) url += `&bedrooms=${bedrooms}`;
      if (bathrooms) url += `&bathrooms=${bathrooms}`;
      const resp = await api.get(url);
      setListings(resp.data.results);
      setListingsCount(resp.data.count);
      setNextPageUrl(resp.data.next);
      setPrevPageUrl(resp.data.previous);
    } catch (err) { console.error('Failed to fetch listings:', err); }
    finally { setLoadingListings(false); }
  };

  const fetchDashboardData = async () => {
    setLoadingDashboard(true);
    try {
      const [listingStatsResp, reviewStatsResp, appsResp] = await Promise.all([
        api.get('/api/listings/listings/stats/'),
        api.get('/api/reviews/reviews/stats/'),
        api.get('/api/applications/applications/'),
      ]);
      setMarketStats(listingStatsResp.data);
      setReviewStats(reviewStatsResp.data);
      setMyApplications(appsResp.data.results);
    } catch (err) { console.error('Dashboard fetch failed:', err); }
    finally { setLoadingDashboard(false); }
  };

  const handleRegister = async (e) => {
    e.preventDefault(); setAuthError('');
    try {
      const resp = await api.post('/api/auth/register/', {
        username: usernameInput, email: emailInput, password: passwordInput,
        first_name: firstNameInput, last_name: lastNameInput,
      });
      setOtpEmail(emailInput);
      setOtpMessage(resp.data.message);
      setAuthMode('otp');
    } catch (err) { setAuthError(err.response?.data?.error || 'Registration failed. Check your inputs.'); }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault(); setAuthError('');
    try {
      await api.post('/api/profiles/otp/verify_otp/', { email: otpEmail, otp: otpInput });
      setAuthMode('login');
      setOtpMessage('Email verified! You can log in now.');
    } catch (err) { setAuthError(err.response?.data?.error || 'That code didn\'t match. Try again.'); }
  };

  const handleLogin = async (e) => {
    e.preventDefault(); setAuthError('');
    try {
      const resp = await api.post('/api/auth/login/', { username: usernameInput, password: passwordInput });
      const { access, refresh } = resp.data;
      setTokens(access, refresh);
      const decoded = decodeJWT(access);
      setUser({ id: decoded.user_id, username: decoded.username, email: decoded.email });
      setCurrentView('listings');
    } catch (err) {
      setAuthError(
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.detail ||
        'Wrong username or password.'
      );
    }
  };

  const handleLogout = () => {
    clearTokens(); setUser(null); setCurrentView('listings'); setAuthMode('login');
    setUsernameInput(''); setPasswordInput('');
  };

  const handleInitiateApply = (listing) => {
    if (!user) { setAuthMode('login'); setCurrentView('auth'); return; }
    setSelectedListing(listing);
    setWizardStep(1); setApplicantId(null); setUploadedDocs([]); setWizardError('');
    setCurrentView('apply');
  };

  const handleCreateApplicantProfile = async (e) => {
    e.preventDefault(); setWizardError('');
    try {
      const existing = await api.get('/api/applications/applicants/');
      const payload = {
        employer, job_title: jobTitle, credit_score: parseInt(creditScore),
        income: parseFloat(income), savings: parseFloat(savings),
        expected_movein_date: moveInDate, reason, has_rented_before: hasRentedBefore,
        marital_status: maritalStatus, children: false,
        emergency_info: { name: "Emergency Contact", email: "emergency@example.com", phone: "+91-9999999999", relationship: "Relative" }
      };
      let resp;
      if (existing.data.results?.length > 0) {
        resp = await api.put(`/api/applications/applicants/${existing.data.results[0].id}/`, payload);
      } else {
        resp = await api.post('/api/applications/applicants/', payload);
      }
      setApplicantId(resp.data.id);
      setWizardStep(2);
    } catch (err) { setWizardError(JSON.stringify(err.response?.data) || 'Failed to save profile.'); }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!selectedFile) { setWizardError('Pick a file first.'); return; }
    setUploadingDoc(true); setWizardError('');
    try {
      const fd = new FormData();
      fd.append('label', docLabel); fd.append('applicant_ID', applicantId); fd.append('file_field', selectedFile);
      const resp = await api.post('/api/applications/documents/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setUploadedDocs([...uploadedDocs, resp.data]);
      setSelectedFile(null);
      document.getElementById('file-input').value = '';
    } catch (err) { setWizardError('Upload failed. Check file format.'); }
    finally { setUploadingDoc(false); }
  };

  const handleFinalSubmitApplication = async () => {
    setWizardError('');
    try {
      const resp = await api.post('/api/applications/applications/', {
        unit_ID: selectedListing.unit_ID, building_ID: selectedListing.building_ID,
        applicant_ID: applicantId, lease_term: parseInt(leaseTerm), resident_info: residentInfo,
      });
      await api.post(`/api/applications/applications/${resp.data.id}/submit/`);
      setSelectedListing(null); setApplicantId(null); setCurrentView('dashboard');
    } catch (err) { setWizardError('Submission failed. Try again.'); }
  };

  // ─── Sidebar nav item helper ────────────────────────────────────────────────
  const NavBtn = ({ view, icon: Icon, label, onClick }) => {
    const active = currentView === view;
    return (
      <button
        onClick={onClick || (() => setCurrentView(view))}
        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
          active
            ? 'bg-[#f59e0b]/10 text-[#f59e0b] font-medium'
            : 'text-[#9aa0a6] hover:text-[#e8eaed] hover:bg-[#1e2127]'
        }`}
      >
        <Icon size={17} strokeWidth={active ? 2 : 1.5} />
        {label}
      </button>
    );
  };

  return (
    <div className="flex min-h-screen" style={{ background: '#111418', color: '#e8eaed' }}>

      {/* ─── SIDEBAR ─────────────────────────────────────────────────── */}
      <aside style={{ background: '#15181e', borderRight: '1px solid #1e2127', width: 220 }}
             className="flex flex-col justify-between shrink-0">
        <div>
          {/* Logo */}
          <div className="px-5 pt-6 pb-5" style={{ borderBottom: '1px solid #1e2127' }}>
            <div className="flex items-center gap-2.5">
              <div style={{ background: '#f59e0b', borderRadius: 8 }}
                   className="w-7 h-7 flex items-center justify-center shrink-0">
                <span className="text-black font-bold text-sm">H</span>
              </div>
              <div>
                <p className="text-[15px] font-semibold text-[#e8eaed] leading-none">Haven</p>
                <p className="text-[10px] text-[#5f6368] mt-0.5">Rental Portal</p>
              </div>
            </div>
          </div>

          {/* Nav */}
          <nav className="p-3 space-y-0.5 mt-2">
            <NavBtn view="listings" icon={Home} label="Browse" />
            <NavBtn
              view="apply"
              icon={ClipboardList}
              label="Apply"
              onClick={() => handleInitiateApply(null)}
            />
            <NavBtn
              view="dashboard"
              icon={LayoutDashboard}
              label="My Applications"
              onClick={() => { if (!user) { setAuthMode('login'); setCurrentView('auth'); } else setCurrentView('dashboard'); }}
            />
          </nav>
        </div>

        {/* User / Sign in */}
        <div className="p-3" style={{ borderTop: '1px solid #1e2127' }}>
          {user ? (
            <div className="flex items-center gap-2.5 px-1">
              <div style={{ background: '#1e2127', border: '1px solid #2a2d33', borderRadius: 99 }}
                   className="w-7 h-7 flex items-center justify-center text-xs font-semibold text-[#f59e0b] shrink-0">
                {user.username[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-[#e8eaed] truncate">{user.username}</p>
                <p className="text-[10px] text-[#5f6368] truncate">{user.email}</p>
              </div>
              <button onClick={handleLogout} title="Sign out"
                      className="text-[#5f6368] hover:text-[#e8eaed] transition-colors p-1 rounded">
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setAuthMode('login'); setCurrentView('auth'); }}
              style={{ border: '1px solid #2a2d33' }}
              className="w-full text-sm text-[#9aa0a6] hover:text-[#e8eaed] hover:border-[#3a3d44] px-3 py-2 rounded-lg transition-all"
            >
              Sign in
            </button>
          )}
        </div>
      </aside>

      {/* ─── MAIN ────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-8 py-8">

          {/* ═══ BROWSE LISTINGS ═══════════════════════════════════════ */}
          {currentView === 'listings' && (
            <div>
              {/* Header row */}
              <div className="flex items-end justify-between mb-6">
                <div>
                  <h1 className="text-2xl font-semibold text-[#e8eaed]">Find your next place</h1>
                  <p className="text-sm text-[#9aa0a6] mt-0.5">
                    {listingsCount > 0 ? `${listingsCount.toLocaleString()} verified rentals available` : 'Loading listings…'}
                  </p>
                </div>
                <button
                  onClick={() => setShowFilters(f => !f)}
                  style={{ border: '1px solid #2a2d33' }}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm transition-all ${
                    showFilters ? 'text-[#f59e0b] border-[#f59e0b]/40 bg-[#f59e0b]/5' : 'text-[#9aa0a6] hover:text-[#e8eaed] hover:border-[#3a3d44]'
                  }`}
                >
                  <SlidersHorizontal size={15} />
                  Filters
                </button>
              </div>

              {/* Filter panel */}
              {showFilters && (
                <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                     className="p-5 rounded-xl mb-6 flex flex-wrap gap-4 items-end">
                  <Field label="Min rent">
                    <input type="number" value={rentMin} onChange={e => setRentMin(e.target.value)}
                           placeholder="$0" className={inputCls} style={{ maxWidth: 130 }} />
                  </Field>
                  <Field label="Max rent">
                    <input type="number" value={rentMax} onChange={e => setRentMax(e.target.value)}
                           placeholder="No limit" className={inputCls} style={{ maxWidth: 130 }} />
                  </Field>
                  <Field label="Bedrooms">
                    <input type="number" value={bedrooms} onChange={e => setBedrooms(e.target.value)}
                           placeholder="Any" className={inputCls} style={{ maxWidth: 90 }} />
                  </Field>
                  <Field label="Bathrooms">
                    <input type="number" value={bathrooms} onChange={e => setBathrooms(e.target.value)}
                           placeholder="Any" className={inputCls} style={{ maxWidth: 90 }} />
                  </Field>
                  <button
                    onClick={() => { setCurrentPage(1); fetchListings(); }}
                    className="px-4 py-2.5 rounded-lg text-sm font-medium text-black transition-all"
                    style={{ background: '#f59e0b' }}
                  >
                    Search
                  </button>
                  <button
                    onClick={() => { setRentMin(''); setRentMax(''); setBedrooms(''); setBathrooms(''); setCurrentPage(1); fetchListings(); }}
                    className="px-3 py-2.5 rounded-lg text-sm text-[#9aa0a6] hover:text-[#e8eaed] transition-all"
                  >
                    Clear
                  </button>
                </div>
              )}

              {/* Grid */}
              {loadingListings ? (
                <div className="flex items-center justify-center py-24">
                  <div className="w-8 h-8 rounded-full border-2 border-[#2a2d33] border-t-[#f59e0b] animate-spin" />
                </div>
              ) : listings.length === 0 ? (
                <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                     className="py-16 text-center rounded-xl">
                  <p className="text-[#9aa0a6]">No listings match your filters.</p>
                  <button onClick={() => { setRentMin(''); setRentMax(''); setBedrooms(''); setBathrooms(''); fetchListings(); }}
                          className="mt-3 text-sm text-[#f59e0b] hover:underline">
                    Clear filters
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                  {listings.map((l) => (
                    <div key={l.id}
                         style={{ background: '#15181e', border: '1px solid #1e2127' }}
                         className="rounded-xl overflow-hidden hover:border-[#2a2d33] transition-all flex flex-col">
                      <div className="p-5 flex-1">
                        {/* Top row */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0 pr-2">
                            <p className="text-[13px] font-medium text-[#e8eaed] leading-snug">
                              {l.unit_details?.full_address || l.unit_address || 'Address unavailable'}
                            </p>
                          </div>
                          {l.is_listing_verified && (
                            <BadgeCheck size={15} className="text-emerald-400 shrink-0 mt-0.5" />
                          )}
                        </div>

                        {/* Rent */}
                        <div className="mb-4">
                          <span className="text-2xl font-bold text-[#e8eaed]">${parseInt(l.rent).toLocaleString()}</span>
                          <span className="text-sm text-[#5f6368] ml-1">/mo</span>
                        </div>

                        {/* Details row */}
                        <div className="flex items-center gap-3 text-[13px] text-[#9aa0a6]">
                          {l.unit_details?.no_bedrooms != null && (
                            <span>{l.unit_details.no_bedrooms} bed</span>
                          )}
                          {l.unit_details?.no_bathrooms != null && (
                            <><span className="text-[#2a2d33]">·</span>
                            <span>{l.unit_details.no_bathrooms} bath</span></>
                          )}
                          {l.unit_details?.square_footage && (
                            <><span className="text-[#2a2d33]">·</span>
                            <span>{l.unit_details.square_footage} sqft</span></>
                          )}
                        </div>

                        {/* Building / agent */}
                        {(l.unit_details?.building_details?.name || l.unit_details?.agent_details) && (
                          <div className="mt-3 pt-3" style={{ borderTop: '1px solid #1e2127' }}>
                            {l.unit_details?.building_details?.name && (
                              <p className="text-[12px] text-[#5f6368] truncate">{l.unit_details.building_details.name}</p>
                            )}
                            {l.unit_details?.agent_details && (
                              <p className="text-[12px] text-[#5f6368] truncate">
                                Agent: {l.unit_details.agent_details.first_name} {l.unit_details.agent_details.last_name}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      {/* CTA */}
                      <div className="px-5 pb-5">
                        <button
                          onClick={() => handleInitiateApply({
                            id: l.id, unit_ID: l.unit_ID,
                            building_ID: l.unit_details?.building_ID || l.building_ID,
                            address: l.unit_details?.full_address || l.unit_address || 'Selected unit',
                            rent: l.rent
                          })}
                          style={{ background: '#1e2127', border: '1px solid #2a2d33' }}
                          className="w-full text-sm text-[#e8eaed] hover:border-[#f59e0b]/50 hover:text-[#f59e0b] py-2 rounded-lg transition-all flex items-center justify-center gap-1.5"
                        >
                          Apply for this unit <ArrowRight size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {listingsCount > 0 && (
                <div className="flex items-center justify-between pt-4" style={{ borderTop: '1px solid #1e2127' }}>
                  <span className="text-sm text-[#5f6368]">Page {currentPage} of {Math.ceil(listingsCount / 20)}</span>
                  <div className="flex gap-2">
                    <button disabled={!prevPageUrl} onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                            style={{ border: '1px solid #2a2d33' }}
                            className="p-2 rounded-lg text-[#9aa0a6] hover:text-[#e8eaed] disabled:opacity-30 transition-all">
                      <ChevronLeft size={16} />
                    </button>
                    <button disabled={!nextPageUrl} onClick={() => setCurrentPage(p => p + 1)}
                            style={{ border: '1px solid #2a2d33' }}
                            className="p-2 rounded-lg text-[#9aa0a6] hover:text-[#e8eaed] disabled:opacity-30 transition-all">
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ═══ AUTH ═══════════════════════════════════════════════════ */}
          {currentView === 'auth' && (
            <div className="max-w-sm mx-auto py-12">

              {/* REGISTER */}
              {authMode === 'register' && (
                <div>
                  <h1 className="text-xl font-semibold text-[#e8eaed] mb-1">Create an account</h1>
                  <p className="text-sm text-[#9aa0a6] mb-6">You'll need this to apply for listings.</p>

                  {authError && (
                    <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                         className="flex items-start gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-4">
                      <AlertCircle size={15} className="shrink-0 mt-0.5" />
                      {authError}
                    </div>
                  )}

                  <form onSubmit={handleRegister} className="space-y-4">
                    <Field label="Username">
                      <input type="text" required value={usernameInput}
                             onChange={e => setUsernameInput(e.target.value)}
                             placeholder="yourname" className={inputCls} />
                    </Field>
                    <Field label="Email">
                      <input type="email" required value={emailInput}
                             onChange={e => setEmailInput(e.target.value)}
                             placeholder="you@email.com" className={inputCls} />
                    </Field>
                    <div className="grid grid-cols-2 gap-3">
                      <Field label="First name">
                        <input type="text" required value={firstNameInput}
                               onChange={e => setFirstNameInput(e.target.value)}
                               placeholder="Alex" className={inputCls} />
                      </Field>
                      <Field label="Last name">
                        <input type="text" required value={lastNameInput}
                               onChange={e => setLastNameInput(e.target.value)}
                               placeholder="Kim" className={inputCls} />
                      </Field>
                    </div>
                    <Field label="Password">
                      <input type="password" required value={passwordInput}
                             onChange={e => setPasswordInput(e.target.value)}
                             placeholder="At least 8 characters" className={inputCls} />
                    </Field>
                    <button type="submit"
                            className="w-full py-2.5 rounded-lg text-sm font-medium text-black transition-opacity hover:opacity-90"
                            style={{ background: '#f59e0b' }}>
                      Create account
                    </button>
                  </form>

                  <p className="text-sm text-center text-[#5f6368] mt-6">
                    Already have an account?{' '}
                    <button onClick={() => setAuthMode('login')} className="text-[#f59e0b] hover:underline">
                      Sign in
                    </button>
                  </p>
                </div>
              )}

              {/* OTP */}
              {authMode === 'otp' && (
                <div>
                  <div className="mb-6">
                    <div style={{ background: '#1e2127', border: '1px solid #2a2d33', borderRadius: 99 }}
                         className="w-11 h-11 flex items-center justify-center mb-4">
                      <Mail size={20} className="text-[#f59e0b]" />
                    </div>
                    <h1 className="text-xl font-semibold text-[#e8eaed] mb-1">Check your email</h1>
                    <p className="text-sm text-[#9aa0a6]">We sent a code to <span className="text-[#e8eaed]">{otpEmail}</span></p>
                  </div>

                  {otpMessage && (
                    <div style={{ background: '#1e2127', border: '1px solid #2a2d33' }}
                         className="p-3 rounded-lg text-sm text-[#9aa0a6] mb-4">
                      {otpMessage}
                    </div>
                  )}
                  {authError && (
                    <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                         className="flex items-start gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-4">
                      <AlertCircle size={15} className="shrink-0 mt-0.5" /> {authError}
                    </div>
                  )}

                  <form onSubmit={handleVerifyOtp} className="space-y-4">
                    <Field label="Verification code">
                      <input type="text" required value={otpInput}
                             onChange={e => setOtpInput(e.target.value)}
                             placeholder="6-digit code"
                             className={inputCls + " text-center tracking-[0.5em] text-lg font-semibold"} />
                    </Field>
                    <button type="submit"
                            className="w-full py-2.5 rounded-lg text-sm font-medium text-black"
                            style={{ background: '#f59e0b' }}>
                      Verify email
                    </button>
                  </form>
                </div>
              )}

              {/* LOGIN */}
              {authMode === 'login' && (
                <div>
                  <h1 className="text-xl font-semibold text-[#e8eaed] mb-1">Sign in</h1>
                  <p className="text-sm text-[#9aa0a6] mb-6">Good to have you back.</p>

                  {otpMessage && (
                    <div style={{ background: '#1e2127', border: '1px solid #2a2d33' }}
                         className="p-3 rounded-lg text-sm text-emerald-400 mb-4 flex items-center gap-2">
                      <CheckCircle2 size={15} /> {otpMessage}
                    </div>
                  )}
                  {authError && (
                    <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                         className="flex items-start gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-4">
                      <AlertCircle size={15} className="shrink-0 mt-0.5" /> {authError}
                    </div>
                  )}

                  <form onSubmit={handleLogin} className="space-y-4">
                    <Field label="Username">
                      <input type="text" required value={usernameInput}
                             onChange={e => setUsernameInput(e.target.value)}
                             placeholder="yourname" className={inputCls} />
                    </Field>
                    <Field label="Password">
                      <input type="password" required value={passwordInput}
                             onChange={e => setPasswordInput(e.target.value)}
                             placeholder="••••••••" className={inputCls} />
                    </Field>
                    <button type="submit"
                            className="w-full py-2.5 rounded-lg text-sm font-medium text-black"
                            style={{ background: '#f59e0b' }}>
                      Sign in
                    </button>
                  </form>

                  <p className="text-sm text-center text-[#5f6368] mt-6">
                    New here?{' '}
                    <button onClick={() => setAuthMode('register')} className="text-[#f59e0b] hover:underline">
                      Create an account
                    </button>
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ═══ APPLICATION WIZARD ════════════════════════════════════ */}
          {currentView === 'apply' && (
            <div className="max-w-xl mx-auto">
              <div className="mb-6">
                <h1 className="text-2xl font-semibold text-[#e8eaed]">Rental application</h1>
                <p className="text-sm text-[#9aa0a6] mt-0.5">Takes about 5 minutes to complete.</p>
              </div>

              {!selectedListing ? (
                <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                     className="py-12 text-center rounded-xl">
                  <p className="text-[#9aa0a6] text-sm">Pick a listing from the Browse page first.</p>
                  <button onClick={() => setCurrentView('listings')}
                          className="mt-3 text-sm text-[#f59e0b] hover:underline">
                    Go browse listings →
                  </button>
                </div>
              ) : (
                <>
                  {/* Selected listing banner */}
                  <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                       className="flex justify-between items-center p-4 rounded-xl mb-6">
                    <div>
                      <p className="text-xs text-[#5f6368] mb-0.5">Applying for</p>
                      <p className="text-sm font-medium text-[#e8eaed]">{selectedListing.address}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-[#5f6368] mb-0.5">Monthly rent</p>
                      <p className="text-sm font-semibold text-[#f59e0b]">${parseInt(selectedListing.rent).toLocaleString()}</p>
                    </div>
                  </div>

                  {/* Step indicator */}
                  <div className="flex items-center gap-2 mb-6 text-sm">
                    {['Your info', 'Documents', 'Review'].map((label, i) => {
                      const step = i + 1;
                      const done = wizardStep > step;
                      const active = wizardStep === step;
                      return (
                        <React.Fragment key={step}>
                          <div className={`flex items-center gap-1.5 ${active ? 'text-[#e8eaed]' : done ? 'text-emerald-400' : 'text-[#5f6368]'}`}>
                            {done
                              ? <CheckCircle2 size={15} />
                              : <span style={{ width: 20, height: 20, borderRadius: 99, border: `1.5px solid ${active ? '#f59e0b' : '#2a2d33'}`, background: active ? '#f59e0b15' : 'transparent' }}
                                      className="flex items-center justify-center text-xs">{step}</span>
                            }
                            <span className={active ? 'font-medium' : ''}>{label}</span>
                          </div>
                          {i < 2 && <div className="flex-1 h-px" style={{ background: '#1e2127' }} />}
                        </React.Fragment>
                      );
                    })}
                  </div>

                  {/* Error */}
                  {wizardError && (
                    <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                         className="flex items-start gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-4">
                      <AlertCircle size={15} className="shrink-0 mt-0.5" />
                      <span className="break-all">{wizardError}</span>
                    </div>
                  )}

                  {/* STEP 1 */}
                  {wizardStep === 1 && (
                    <form onSubmit={handleCreateApplicantProfile}
                          style={{ background: '#15181e', border: '1px solid #1e2127' }}
                          className="p-6 rounded-xl space-y-4">
                      <div className="grid grid-cols-2 gap-3">
                        <Field label="Employer">
                          <input type="text" required value={employer} onChange={e => setEmployer(e.target.value)}
                                 placeholder="Company name" className={inputCls} />
                        </Field>
                        <Field label="Job title">
                          <input type="text" required value={jobTitle} onChange={e => setJobTitle(e.target.value)}
                                 placeholder="Your role" className={inputCls} />
                        </Field>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <Field label="Annual income ($)">
                          <input type="number" required value={income} onChange={e => setIncome(e.target.value)}
                                 placeholder="75000" className={inputCls} />
                        </Field>
                        <Field label="Savings ($)">
                          <input type="number" required value={savings} onChange={e => setSavings(e.target.value)}
                                 placeholder="10000" className={inputCls} />
                        </Field>
                        <Field label="Credit score">
                          <input type="number" required value={creditScore} onChange={e => setCreditScore(e.target.value)}
                                 placeholder="720" className={inputCls} />
                        </Field>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <Field label="Move-in date">
                          <input type="date" required value={moveInDate} onChange={e => setMoveInDate(e.target.value)}
                                 className={inputCls} />
                        </Field>
                        <div className="flex items-center gap-5 pt-7">
                          <label className="flex items-center gap-2 text-sm text-[#9aa0a6] cursor-pointer">
                            <input type="checkbox" checked={hasRentedBefore} onChange={e => setHasRentedBefore(e.target.checked)}
                                   className="accent-amber-400" />
                            Rented before?
                          </label>
                          <label className="flex items-center gap-2 text-sm text-[#9aa0a6] cursor-pointer">
                            <input type="checkbox" checked={maritalStatus} onChange={e => setMaritalStatus(e.target.checked)}
                                   className="accent-amber-400" />
                            Married?
                          </label>
                        </div>
                      </div>
                      <Field label="Reason for moving (optional)">
                        <textarea rows="2" value={reason} onChange={e => setReason(e.target.value)}
                                  placeholder="e.g. relocating for work, need more space…"
                                  className={inputCls} />
                      </Field>
                      <button type="submit"
                              className="w-full py-2.5 rounded-lg text-sm font-medium text-black"
                              style={{ background: '#f59e0b' }}>
                        Continue to documents
                      </button>
                    </form>
                  )}

                  {/* STEP 2 */}
                  {wizardStep === 2 && (
                    <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                         className="p-6 rounded-xl space-y-5">
                      <div>
                        <p className="text-sm font-medium text-[#e8eaed] mb-1">Upload verification documents</p>
                        <p className="text-sm text-[#5f6368]">Add at least one document before continuing.</p>
                      </div>

                      {uploadedDocs.length > 0 && (
                        <div className="space-y-2">
                          {uploadedDocs.map((doc, idx) => (
                            <div key={idx} style={{ background: '#1a1d22', border: '1px solid #1e2127' }}
                                 className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg">
                              <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                              <span className="text-sm text-[#e8eaed]">{doc.label}</span>
                              <span className="text-xs text-[#5f6368] ml-auto truncate max-w-[160px]">
                                {doc.file_field?.split('/').pop()}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      <form onSubmit={handleUploadDocument}
                            style={{ background: '#1a1d22', border: '1px solid #1e2127' }}
                            className="p-4 rounded-lg space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <Field label="Document type">
                            <select value={docLabel} onChange={e => setDocLabel(e.target.value)} className={inputCls}>
                              <option>Pay Stub</option>
                              <option>Bank Statement</option>
                              <option>ID Proof</option>
                              <option>Tax Return</option>
                            </select>
                          </Field>
                          <Field label="File">
                            <input id="file-input" type="file" required
                                   onChange={e => setSelectedFile(e.target.files[0])}
                                   className="w-full text-xs text-[#9aa0a6] file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-[#2a2d33] file:text-[#e8eaed] hover:file:bg-[#3a3d44] cursor-pointer" />
                          </Field>
                        </div>
                        <button type="submit" disabled={uploadingDoc}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-black disabled:opacity-50"
                                style={{ background: '#f59e0b' }}>
                          <FileUp size={14} />
                          {uploadingDoc ? 'Uploading…' : 'Add document'}
                        </button>
                      </form>

                      <div className="flex gap-3 pt-2">
                        <button onClick={() => setWizardStep(1)}
                                style={{ border: '1px solid #2a2d33' }}
                                className="flex-1 py-2.5 rounded-lg text-sm text-[#9aa0a6] hover:text-[#e8eaed] transition-all">
                          Back
                        </button>
                        <button onClick={() => setWizardStep(3)} disabled={uploadedDocs.length === 0}
                                className="flex-1 py-2.5 rounded-lg text-sm font-medium text-black disabled:opacity-40"
                                style={{ background: '#f59e0b' }}>
                          Continue
                        </button>
                      </div>
                    </div>
                  )}

                  {/* STEP 3 */}
                  {wizardStep === 3 && (
                    <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                         className="p-6 rounded-xl space-y-5">
                      <div>
                        <p className="text-sm font-medium text-[#e8eaed] mb-1">Almost done</p>
                        <p className="text-sm text-[#5f6368]">Review your application before submitting.</p>
                      </div>

                      <div style={{ background: '#1a1d22', border: '1px solid #1e2127' }}
                           className="p-4 rounded-lg space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-[#5f6368]">Employer</span>
                          <span className="text-[#e8eaed]">{employer}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5f6368]">Credit score</span>
                          <span className="text-[#e8eaed]">{creditScore}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#5f6368]">Documents</span>
                          <span className="text-[#e8eaed]">{uploadedDocs.length} attached</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <Field label="Lease length">
                          <select value={leaseTerm} onChange={e => setLeaseTerm(e.target.value)} className={inputCls}>
                            <option value="6">6 months</option>
                            <option value="12">12 months</option>
                            <option value="18">18 months</option>
                            <option value="24">24 months</option>
                          </select>
                        </Field>
                        <Field label="Who will live here?">
                          <input type="text" value={residentInfo} onChange={e => setResidentInfo(e.target.value)}
                                 className={inputCls} />
                        </Field>
                      </div>

                      <div className="flex gap-3 pt-2">
                        <button onClick={() => setWizardStep(2)}
                                style={{ border: '1px solid #2a2d33' }}
                                className="flex-1 py-2.5 rounded-lg text-sm text-[#9aa0a6] hover:text-[#e8eaed] transition-all">
                          Back
                        </button>
                        <button onClick={handleFinalSubmitApplication}
                                className="flex-1 py-2.5 rounded-lg text-sm font-medium text-black"
                                style={{ background: '#f59e0b' }}>
                          Submit application
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* ═══ DASHBOARD ═════════════════════════════════════════════ */}
          {currentView === 'dashboard' && (
            <div>
              <div className="mb-6">
                <h1 className="text-2xl font-semibold text-[#e8eaed]">
                  {user ? `Hi, ${user.username}` : 'Dashboard'}
                </h1>
                <p className="text-sm text-[#9aa0a6] mt-0.5">Your applications and market data.</p>
              </div>

              {loadingDashboard ? (
                <div className="flex justify-center py-16">
                  <div className="w-8 h-8 rounded-full border-2 border-[#2a2d33] border-t-[#f59e0b] animate-spin" />
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Stats row */}
                  <div className="grid grid-cols-2 gap-4">
                    <div style={{ background: '#15181e', border: '1px solid #1e2127' }} className="p-5 rounded-xl">
                      <p className="text-xs text-[#5f6368] mb-3 flex items-center gap-1.5">
                        <Home size={13} /> Market overview
                      </p>
                      {marketStats ? (
                        <div className="space-y-3">
                          <div>
                            <p className="text-2xl font-bold text-[#e8eaed]">{marketStats.total_listings?.toLocaleString()}</p>
                            <p className="text-xs text-[#5f6368]">total listings</p>
                          </div>
                          <div style={{ borderTop: '1px solid #1e2127' }} className="pt-3">
                            <p className="text-lg font-semibold text-[#e8eaed]">${Math.round(marketStats.average_rent || 0).toLocaleString()}</p>
                            <p className="text-xs text-[#5f6368]">average rent</p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-[#5f6368]">Stats unavailable</p>
                      )}
                    </div>

                    <div style={{ background: '#15181e', border: '1px solid #1e2127' }} className="p-5 rounded-xl">
                      <p className="text-xs text-[#5f6368] mb-3 flex items-center gap-1.5">
                        <Star size={13} /> Tenant reviews
                      </p>
                      {reviewStats ? (
                        <div className="space-y-3">
                          <div>
                            <p className="text-2xl font-bold text-[#e8eaed]">{Number(reviewStats.avg_cleanliness || 0).toFixed(1)}<span className="text-sm font-normal text-[#5f6368]">/5</span></p>
                            <p className="text-xs text-[#5f6368]">avg cleanliness</p>
                          </div>
                          <div style={{ borderTop: '1px solid #1e2127' }} className="pt-3">
                            <p className="text-lg font-semibold text-[#e8eaed]">{Math.round(reviewStats.deposit_return_rate || 0)}%</p>
                            <p className="text-xs text-[#5f6368]">deposit return rate</p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-[#5f6368]">Stats unavailable</p>
                      )}
                    </div>
                  </div>

                  {/* My applications */}
                  <div style={{ background: '#15181e', border: '1px solid #1e2127' }} className="rounded-xl overflow-hidden">
                    <div className="px-5 py-4" style={{ borderBottom: '1px solid #1e2127' }}>
                      <p className="text-sm font-medium text-[#e8eaed]">My applications</p>
                    </div>

                    {myApplications.length === 0 ? (
                      <div className="py-12 text-center">
                        <ClipboardList size={28} className="mx-auto text-[#2a2d33] mb-3" />
                        <p className="text-sm text-[#5f6368]">No applications yet.</p>
                        <button onClick={() => setCurrentView('listings')}
                                className="mt-2 text-sm text-[#f59e0b] hover:underline">
                          Browse listings →
                        </button>
                      </div>
                    ) : (
                      <table className="w-full text-sm">
                        <thead>
                          <tr style={{ borderBottom: '1px solid #1e2127' }}>
                            {['ID', 'Submitted', 'Lease', 'Status'].map(h => (
                              <th key={h} className="px-5 py-3 text-left text-xs text-[#5f6368] font-medium">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {myApplications.map((app) => (
                            <tr key={app.id} style={{ borderBottom: '1px solid #1e2127' }}
                                className="hover:bg-[#1a1d22] transition-colors">
                              <td className="px-5 py-3.5 text-xs text-[#5f6368] font-mono">{app.id?.slice(0, 8)}…</td>
                              <td className="px-5 py-3.5 text-[#9aa0a6]">{app.submitted_at_date || '—'}</td>
                              <td className="px-5 py-3.5 text-[#9aa0a6]">{app.lease_term || 12}mo</td>
                              <td className="px-5 py-3.5"><StatusBadge status={app.application_status} /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>

                </div>
              )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
