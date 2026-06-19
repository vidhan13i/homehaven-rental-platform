import React, { useState, useEffect, useCallback } from 'react';
import { api, getAccessToken, setTokens, clearTokens } from './api';
import {
  Home, ClipboardList, LayoutDashboard, LogOut, AlertCircle, X,
  ChevronLeft, ChevronRight, SlidersHorizontal, Star,
  CheckCircle2, ArrowRight, BadgeCheck, Mail, FileUp,
  Building2, Bed, Bath, Ruler, Calendar, TrendingUp,
  Clock, Send, User, Lock, Plus, Trash2, RefreshCw
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

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

const inputCls = "w-full bg-[#1a1d22] border border-[#2a2d33] rounded-lg px-3.5 py-2.5 text-sm text-[#e8eaed] placeholder-[#4a4d55] focus:outline-none focus:border-[#f59e0b] transition-colors";

const Field = ({ label, children, hint }) => (
  <div>
    <label className="block text-xs font-medium text-[#9aa0a6] mb-1.5 uppercase tracking-wide">{label}</label>
    {children}
    {hint && <p className="text-[11px] text-[#5f6368] mt-1">{hint}</p>}
  </div>
);

// ─── Toast notification system ──────────────────────────────────────────────

const Toast = ({ toasts, removeToast }) => (
  <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5" style={{ maxWidth: 340 }}>
    {toasts.map(t => (
      <div key={t.id}
           style={{
             background: t.type === 'success' ? '#0d2b1a' : t.type === 'error' ? '#2a1515' : '#1a1d22',
             border: `1px solid ${t.type === 'success' ? '#166534' : t.type === 'error' ? '#4a1515' : '#2a2d33'}`,
             animation: 'slideUp 0.25s ease'
           }}
           className="flex items-start gap-3 px-4 py-3 rounded-xl shadow-xl">
        {t.type === 'success'
          ? <CheckCircle2 size={16} className="text-emerald-400 shrink-0 mt-0.5" />
          : <AlertCircle size={16} className="text-red-400 shrink-0 mt-0.5" />}
        <p className="text-sm text-[#e8eaed] flex-1">{t.message}</p>
        <button onClick={() => removeToast(t.id)} className="text-[#5f6368] hover:text-[#e8eaed] transition-colors ml-1">
          <X size={14} />
        </button>
      </div>
    ))}
  </div>
);

// ─── Skeleton loader ─────────────────────────────────────────────────────────

const Skeleton = ({ className }) => (
  <div className={`rounded-lg animate-pulse ${className}`}
       style={{ background: 'linear-gradient(90deg, #1a1d22 25%, #22252c 50%, #1a1d22 75%)', backgroundSize: '200% 100%' }} />
);

const ListingCardSkeleton = () => (
  <div style={{ background: '#15181e', border: '1px solid #1e2127' }} className="rounded-xl p-5 space-y-3">
    <Skeleton className="h-4 w-3/4" />
    <Skeleton className="h-8 w-1/2" />
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-3 w-2/3" />
    <div style={{ borderTop: '1px solid #1e2127' }} className="pt-3 mt-3">
      <Skeleton className="h-9 w-full rounded-lg" />
    </div>
  </div>
);

// ─── Status badge ────────────────────────────────────────────────────────────

const StatusBadge = ({ status }) => {
  const map = {
    approved:  { color: 'text-emerald-400 bg-emerald-950/50 border-emerald-800/40', label: 'Approved', dot: 'bg-emerald-400' },
    rejected:  { color: 'text-red-400 bg-red-950/50 border-red-800/40',             label: 'Rejected', dot: 'bg-red-400' },
    submitted: { color: 'text-sky-400 bg-sky-950/50 border-sky-800/40',              label: 'Under Review', dot: 'bg-sky-400' },
    draft:     { color: 'text-[#9aa0a6] bg-[#1a1d22] border-[#2a2d33]',             label: 'Draft', dot: 'bg-[#5f6368]' },
  };
  const s = map[status] || map.draft;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${s.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
};

// ─── Main App ────────────────────────────────────────────────────────────────

export default function App() {
  const [currentView, setCurrentView] = useState('listings');

  // Toast
  const [toasts, setToasts] = useState([]);
  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now();
    setToasts(t => [...t, { id, message, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);
  const removeToast = (id) => setToasts(t => t.filter(x => x.id !== id));

  // Auth
  const [user, setUser]               = useState(null);
  const [authMode, setAuthMode]       = useState('login');
  const [authError, setAuthError]     = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [otpEmail, setOtpEmail]       = useState('');
  const [usernameInput, setUsernameInput]     = useState('');
  const [emailInput, setEmailInput]           = useState('');
  const [passwordInput, setPasswordInput]     = useState('');
  const [firstNameInput, setFirstNameInput]   = useState('');
  const [lastNameInput, setLastNameInput]     = useState('');
  const [otpInput, setOtpInput]       = useState('');
  const [otpMessage, setOtpMessage]   = useState('');

  // Listings
  const [listings, setListings]             = useState([]);
  const [listingsCount, setListingsCount]   = useState(0);
  const [currentPage, setCurrentPage]       = useState(1);
  const [nextPageUrl, setNextPageUrl]       = useState(null);
  const [prevPageUrl, setPrevPageUrl]       = useState(null);
  const [loadingListings, setLoadingListings] = useState(true);
  const [rentMin, setRentMin]     = useState('');
  const [rentMax, setRentMax]     = useState('');
  const [bedrooms, setBedrooms]   = useState('');
  const [bathrooms, setBathrooms] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Wizard
  const [selectedListing, setSelectedListing] = useState(null);
  const [wizardStep, setWizardStep]       = useState(1);
  const [wizardDone, setWizardDone]       = useState(false);
  const [applicantId, setApplicantId]     = useState(null);
  const [wizardError, setWizardError]     = useState('');
  const [submitting, setSubmitting]       = useState(false);
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
  const [marketStats, setMarketStats]         = useState(null);
  const [reviewStats, setReviewStats]         = useState(null);
  const [myApplications, setMyApplications]   = useState([]);
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  // Init auth
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

  // ─── API calls ────────────────────────────────────────────────────────────

  const fetchListings = async () => {
    setLoadingListings(true);
    try {
      let url = `/api/listings/listings/public/?page=${currentPage}`;
      if (rentMin) url += `&rent_min=${rentMin}`;
      if (rentMax) url += `&rent_max=${rentMax}`;
      if (bedrooms) url += `&bedrooms=${bedrooms}`;
      if (bathrooms) url += `&bathrooms=${bathrooms}`;
      const resp = await api.get(url);
      setListings(resp.data.results || []);
      setListingsCount(resp.data.count || 0);
      setNextPageUrl(resp.data.next);
      setPrevPageUrl(resp.data.previous);
    } catch (err) {
      addToast('Could not load listings. Check your connection.', 'error');
    } finally { setLoadingListings(false); }
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
      setMyApplications(appsResp.data.results || []);
    } catch (err) {
      addToast('Could not load dashboard data.', 'error');
    } finally { setLoadingDashboard(false); }
  };

  const handleRegister = async (e) => {
    e.preventDefault(); setAuthError(''); setAuthLoading(true);
    try {
      const resp = await api.post('/api/auth/register/', {
        username: usernameInput, email: emailInput, password: passwordInput,
        first_name: firstNameInput, last_name: lastNameInput,
      });
      setOtpEmail(emailInput);
      setOtpMessage(resp.data.message || 'Check your email for the OTP code.');
      setAuthMode('otp');
    } catch (err) {
      setAuthError(err.response?.data?.error || 'Registration failed. Please check your inputs.');
    } finally { setAuthLoading(false); }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault(); setAuthError(''); setAuthLoading(true);
    try {
      await api.post('/api/profiles/otp/verify_otp/', { email: otpEmail, otp: otpInput });
      setAuthMode('login');
      setOtpMessage('Email verified! You can now sign in.');
      addToast('Email verified successfully!');
    } catch (err) {
      setAuthError(err.response?.data?.message || err.response?.data?.error || "That code didn't match. Try again.");
    } finally { setAuthLoading(false); }
  };

  const handleLogin = async (e) => {
    e.preventDefault(); setAuthError(''); setAuthLoading(true);
    try {
      const resp = await api.post('/api/auth/login/', { username: usernameInput, password: passwordInput });
      const { access, refresh } = resp.data;
      setTokens(access, refresh);
      const decoded = decodeJWT(access);
      const loggedInUser = { id: decoded.user_id, username: decoded.username, email: decoded.email };
      setUser(loggedInUser);
      setCurrentView('listings');
      addToast(`Welcome back, ${decoded.username}!`);
    } catch (err) {
      setAuthError(
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.detail ||
        'Wrong username or password.'
      );
    } finally { setAuthLoading(false); }
  };

  const handleLogout = () => {
    clearTokens(); setUser(null); setCurrentView('listings');
    setUsernameInput(''); setPasswordInput('');
    addToast('Signed out.', 'info');
  };

  const goToAuth = () => { setAuthMode('login'); setAuthError(''); setOtpMessage(''); setCurrentView('auth'); };

  const handleInitiateApply = (listing) => {
    if (!user) { goToAuth(); return; }
    setSelectedListing(listing);
    setWizardStep(1); setWizardDone(false); setApplicantId(null);
    setUploadedDocs([]); setWizardError('');
    setEmployer(''); setJobTitle(''); setCreditScore(''); setIncome('');
    setSavings(''); setReason('');
    setCurrentView('apply');
  };

  const handleCreateApplicantProfile = async (e) => {
    e.preventDefault(); setWizardError(''); setSubmitting(true);
    try {
      const payload = {
        employer, job_title: jobTitle, credit_score: parseInt(creditScore),
        income: parseFloat(income), savings: parseFloat(savings),
        expected_movein_date: moveInDate, reason, has_rented_before: hasRentedBefore,
        marital_status: maritalStatus, children: false,
        emergency_info: { name: "Emergency Contact", email: "emergency@example.com", phone: "+91-9999999999", relationship: "Relative" }
      };
      const existing = await api.get('/api/applications/applicants/');
      let resp;
      if (existing.data.results?.length > 0) {
        resp = await api.put(`/api/applications/applicants/${existing.data.results[0].id}/`, payload);
      } else {
        resp = await api.post('/api/applications/applicants/', payload);
      }
      setApplicantId(resp.data.id);
      setWizardStep(2);
    } catch (err) {
      setWizardError(typeof err.response?.data === 'object'
        ? Object.values(err.response.data).flat().join(' ')
        : 'Failed to save your info. Check all fields.');
    } finally { setSubmitting(false); }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!selectedFile) { setWizardError('Select a file first.'); return; }
    setUploadingDoc(true); setWizardError('');
    try {
      const fd = new FormData();
      fd.append('label', docLabel); fd.append('applicant_ID', applicantId); fd.append('file_field', selectedFile);
      const resp = await api.post('/api/applications/documents/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setUploadedDocs(prev => [...prev, resp.data]);
      setSelectedFile(null);
      const fi = document.getElementById('file-input');
      if (fi) fi.value = '';
      addToast(`"${docLabel}" uploaded.`);
    } catch (err) {
      setWizardError('Upload failed. Make sure the file is a PDF or image.');
    } finally { setUploadingDoc(false); }
  };

  const handleFinalSubmitApplication = async () => {
    setWizardError(''); setSubmitting(true);
    try {
      const resp = await api.post('/api/applications/applications/', {
        unit_ID: selectedListing.unit_ID, building_ID: selectedListing.building_ID,
        applicant_ID: applicantId, lease_term: parseInt(leaseTerm), resident_info: residentInfo,
      });
      await api.post(`/api/applications/applications/${resp.data.id}/submit/`);
      setWizardDone(true);
      setWizardStep(4);
    } catch (err) {
      setWizardError('Submission failed. Please try again or contact support.');
    } finally { setSubmitting(false); }
  };

  // ─── Nav ─────────────────────────────────────────────────────────────────

  const NavBtn = ({ view, icon: Icon, label, onClick }) => {
    const active = currentView === view;
    return (
      <button
        onClick={onClick || (() => setCurrentView(view))}
        className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-all ${
          active ? 'bg-[#f59e0b]/10 text-[#f59e0b] font-medium' : 'text-[#6b7280] hover:text-[#e8eaed] hover:bg-[#1e2127]'
        }`}
      >
        <Icon size={16} strokeWidth={active ? 2.5 : 1.75} />
        {label}
        {active && <span className="ml-auto w-1 h-1 rounded-full bg-[#f59e0b]" />}
      </button>
    );
  };

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="flex min-h-screen" style={{ background: '#111418', color: '#e8eaed', fontFamily: "'Inter', system-ui, sans-serif" }}>
      <Toast toasts={toasts} removeToast={removeToast} />

      {/* ── SIDEBAR ─────────────────────────────────────────────────────── */}
      <aside style={{ background: '#0e1114', borderRight: '1px solid #1e2127', width: 230, position: 'sticky', top: 0, height: '100vh' }}
             className="flex flex-col shrink-0">

        {/* Logo */}
        <div className="px-5 pt-6 pb-5" style={{ borderBottom: '1px solid #1e2127' }}>
          <div className="flex items-center gap-2.5">
            <div style={{ background: '#f59e0b', borderRadius: 10, width: 30, height: 30 }}
                 className="flex items-center justify-center shrink-0">
              <Building2 size={16} color="#000" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-[15px] font-semibold text-[#e8eaed] leading-none">Haven</p>
              <p className="text-[11px] text-[#4a4d55] mt-0.5">Rental Platform</p>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="p-3 space-y-0.5 mt-1 flex-1">
          <p className="text-[10px] text-[#3a3d45] font-semibold uppercase tracking-widest px-3 mb-2 mt-1">Menu</p>
          <NavBtn view="listings" icon={Home} label="Browse" />
          <NavBtn view="apply" icon={ClipboardList} label="Apply"
            onClick={() => handleInitiateApply(null)} />
          <NavBtn view="dashboard" icon={LayoutDashboard} label="My Applications"
            onClick={() => { if (!user) goToAuth(); else setCurrentView('dashboard'); }} />
        </nav>

        {/* Stats pill — always visible */}
        {listingsCount > 0 && (
          <div className="mx-3 mb-3">
            <div style={{ background: '#1a1d22', border: '1px solid #1e2127' }}
                 className="px-3 py-2.5 rounded-lg flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
              <span className="text-xs text-[#6b7280]">
                <span className="text-[#e8eaed] font-medium">{listingsCount.toLocaleString()}</span> listings live
              </span>
            </div>
          </div>
        )}

        {/* User card */}
        <div className="p-3" style={{ borderTop: '1px solid #1e2127' }}>
          {user ? (
            <div style={{ background: '#1a1d22', border: '1px solid #1e2127' }}
                 className="flex items-center gap-2.5 p-2.5 rounded-xl">
              <div style={{ background: '#f59e0b20', border: '1px solid #f59e0b30', borderRadius: 99 }}
                   className="w-8 h-8 flex items-center justify-center text-xs font-bold text-[#f59e0b] shrink-0">
                {user.username[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-[#e8eaed] truncate">{user.username}</p>
                <p className="text-[10px] text-[#4a4d55] truncate">{user.email}</p>
              </div>
              <button onClick={handleLogout} title="Sign out"
                      className="text-[#4a4d55] hover:text-red-400 transition-colors p-1 rounded">
                <LogOut size={13} />
              </button>
            </div>
          ) : (
            <button onClick={goToAuth}
                    style={{ border: '1px solid #2a2d33' }}
                    className="w-full flex items-center justify-center gap-2 text-sm text-[#9aa0a6] hover:text-[#e8eaed] hover:border-[#f59e0b]/40 px-3 py-2.5 rounded-xl transition-all">
              <User size={14} />
              Sign in
            </button>
          )}
        </div>
      </aside>

      {/* ── MAIN ────────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">

        {/* ══ BROWSE ════════════════════════════════════════════════════ */}
        {currentView === 'listings' && (
          <div>
            {/* Hero banner */}
            <div style={{
              background: 'linear-gradient(135deg, #0e1114 0%, #181c22 60%, #1a1a10 100%)',
              borderBottom: '1px solid #1e2127'
            }} className="px-10 pt-12 pb-10">
              <div className="max-w-4xl">
                <p className="text-xs font-semibold text-[#f59e0b] uppercase tracking-widest mb-3">Rental Portal</p>
                <h1 className="text-4xl font-bold text-[#e8eaed] leading-tight mb-3">
                  Find your next home.
                </h1>
                <p className="text-[#6b7280] text-base max-w-lg">
                  Browse verified, agent-backed rentals. Submit an application in minutes — no paperwork needed.
                </p>
                <div className="flex items-center gap-6 mt-6 text-sm text-[#6b7280]">
                  <div className="flex items-center gap-1.5">
                    <BadgeCheck size={15} className="text-emerald-400" />
                    <span>Verified listings</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock size={15} className="text-[#f59e0b]" />
                    <span>5-min application</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Send size={15} className="text-sky-400" />
                    <span>Real-time status</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-10 py-8 max-w-6xl">
              {/* Toolbar */}
              <div className="flex items-center justify-between mb-6">
                <p className="text-sm text-[#6b7280]">
                  {loadingListings ? 'Loading…' : (
                    listingsCount > 0
                      ? <><span className="text-[#e8eaed] font-medium">{listingsCount.toLocaleString()}</span> places available</>
                      : 'No listings match your search'
                  )}
                </p>
                <div className="flex items-center gap-2">
                  {(rentMin || rentMax || bedrooms || bathrooms) && (
                    <button
                      onClick={() => { setRentMin(''); setRentMax(''); setBedrooms(''); setBathrooms(''); setCurrentPage(1); fetchListings(); }}
                      className="text-xs text-[#9aa0a6] hover:text-red-400 flex items-center gap-1 transition-colors"
                    >
                      <X size={12} /> Clear filters
                    </button>
                  )}
                  <button
                    onClick={() => setShowFilters(f => !f)}
                    style={{ border: `1px solid ${showFilters ? '#f59e0b40' : '#2a2d33'}` }}
                    className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm transition-all ${
                      showFilters ? 'text-[#f59e0b] bg-[#f59e0b]/5' : 'text-[#9aa0a6] hover:text-[#e8eaed] hover:border-[#3a3d44]'
                    }`}
                  >
                    <SlidersHorizontal size={14} />
                    Filters {(rentMin || rentMax || bedrooms || bathrooms) && <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b] ml-0.5" />}
                  </button>
                </div>
              </div>

              {/* Filter panel */}
              {showFilters && (
                <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                     className="p-5 rounded-xl mb-6">
                  <div className="flex flex-wrap gap-4 items-end">
                    <Field label="Min rent">
                      <input type="number" value={rentMin} onChange={e => setRentMin(e.target.value)}
                             placeholder="$0" className={inputCls} style={{ width: 120 }} />
                    </Field>
                    <Field label="Max rent">
                      <input type="number" value={rentMax} onChange={e => setRentMax(e.target.value)}
                             placeholder="Any" className={inputCls} style={{ width: 120 }} />
                    </Field>
                    <Field label="Bedrooms">
                      <input type="number" value={bedrooms} onChange={e => setBedrooms(e.target.value)}
                             placeholder="Any" className={inputCls} style={{ width: 90 }} />
                    </Field>
                    <Field label="Bathrooms">
                      <input type="number" value={bathrooms} onChange={e => setBathrooms(e.target.value)}
                             placeholder="Any" className={inputCls} style={{ width: 90 }} />
                    </Field>
                    <button onClick={() => { setCurrentPage(1); fetchListings(); setShowFilters(false); }}
                            className="px-5 py-2.5 rounded-lg text-sm font-medium text-black transition-opacity hover:opacity-90 mb-px"
                            style={{ background: '#f59e0b' }}>
                      Search
                    </button>
                  </div>
                </div>
              )}

              {/* Grid */}
              {loadingListings ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[...Array(6)].map((_, i) => <ListingCardSkeleton key={i} />)}
                </div>
              ) : listings.length === 0 ? (
                <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                     className="py-20 text-center rounded-xl">
                  <Building2 size={36} className="mx-auto text-[#2a2d33] mb-4" />
                  <p className="text-[#9aa0a6] font-medium">No listings match your search</p>
                  <p className="text-sm text-[#5f6368] mt-1">Try different filter values or clear all filters</p>
                  <button onClick={() => { setRentMin(''); setRentMax(''); setBedrooms(''); setBathrooms(''); fetchListings(); }}
                          className="mt-4 text-sm text-[#f59e0b] hover:underline">
                    Clear all filters
                  </button>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                    {listings.map((l) => (
                      <div key={l.id}
                           style={{ background: '#15181e', border: '1px solid #1e2127' }}
                           className="rounded-xl overflow-hidden hover:border-[#2a2d33] transition-all group flex flex-col">
                        {/* Color accent strip */}
                        <div style={{ height: 3, background: l.is_listing_verified ? 'linear-gradient(90deg, #10b981, #34d399)' : '#1e2127' }} />

                        <div className="p-5 flex-1 flex flex-col">
                          {/* Address + verified */}
                          <div className="flex items-start gap-2 mb-3">
                            <p className="text-[13px] font-medium text-[#e8eaed] leading-snug flex-1">
                              {l.unit_details?.full_address || 'Address not listed'}
                            </p>
                            {l.is_listing_verified && (
                              <BadgeCheck size={15} className="text-emerald-400 shrink-0 mt-0.5" title="Verified listing" />
                            )}
                          </div>

                          {/* Rent */}
                          <div className="mb-4">
                            <span className="text-3xl font-bold text-[#e8eaed]">
                              ${parseInt(l.rent).toLocaleString()}
                            </span>
                            <span className="text-sm text-[#5f6368] ml-1">/mo</span>
                          </div>

                          {/* Details chips */}
                          <div className="flex flex-wrap gap-2 mb-4">
                            {l.unit_details?.no_bedrooms != null && (
                              <span style={{ background: '#1e2127' }} className="flex items-center gap-1 text-[12px] text-[#9aa0a6] px-2.5 py-1 rounded-full">
                                <Bed size={11} /> {l.unit_details.no_bedrooms} bed
                              </span>
                            )}
                            {l.unit_details?.no_bathrooms != null && (
                              <span style={{ background: '#1e2127' }} className="flex items-center gap-1 text-[12px] text-[#9aa0a6] px-2.5 py-1 rounded-full">
                                <Bath size={11} /> {l.unit_details.no_bathrooms} bath
                              </span>
                            )}
                            {l.unit_details?.square_footage && (
                              <span style={{ background: '#1e2127' }} className="flex items-center gap-1 text-[12px] text-[#9aa0a6] px-2.5 py-1 rounded-full">
                                <Ruler size={11} /> {l.unit_details.square_footage} sqft
                              </span>
                            )}
                            {l.lease_term && (
                              <span style={{ background: '#1e2127' }} className="flex items-center gap-1 text-[12px] text-[#9aa0a6] px-2.5 py-1 rounded-full">
                                <Calendar size={11} /> {l.lease_term}mo lease
                              </span>
                            )}
                          </div>

                          {/* Building + agent */}
                          <div className="mt-auto">
                            {l.unit_details?.building_details?.name && (
                              <p className="text-[11px] text-[#4a4d55] flex items-center gap-1 truncate">
                                <Building2 size={10} /> {l.unit_details.building_details.name}
                              </p>
                            )}
                            {l.unit_details?.agent_details && (
                              <p className="text-[11px] text-[#4a4d55] flex items-center gap-1 truncate mt-0.5">
                                <User size={10} />
                                Agent: {l.unit_details.agent_details.first_name} {l.unit_details.agent_details.last_name}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Apply CTA */}
                        <div className="px-5 pb-5">
                          <button
                            onClick={() => handleInitiateApply({
                              id: l.id, unit_ID: l.unit_ID,
                              building_ID: l.unit_details?.building_ID || l.building_ID,
                              address: l.unit_details?.full_address || 'Selected unit',
                              rent: l.rent
                            })}
                            style={{ border: '1px solid #2a2d33' }}
                            className="w-full text-[13px] text-[#9aa0a6] group-hover:text-[#f59e0b] group-hover:border-[#f59e0b]/40 py-2.5 rounded-lg transition-all flex items-center justify-center gap-1.5 font-medium"
                          >
                            Apply for this unit <ArrowRight size={13} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Pagination */}
                  {listingsCount > 20 && (
                    <div className="flex items-center justify-between pt-5" style={{ borderTop: '1px solid #1e2127' }}>
                      <span className="text-sm text-[#5f6368]">
                        Page {currentPage} of {Math.ceil(listingsCount / 20)}
                      </span>
                      <div className="flex gap-2">
                        <button disabled={!prevPageUrl} onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                                style={{ border: '1px solid #2a2d33' }}
                                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-[#9aa0a6] hover:text-[#e8eaed] disabled:opacity-30 transition-all">
                          <ChevronLeft size={14} /> Prev
                        </button>
                        <button disabled={!nextPageUrl} onClick={() => setCurrentPage(p => p + 1)}
                                style={{ border: '1px solid #2a2d33' }}
                                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-[#9aa0a6] hover:text-[#e8eaed] disabled:opacity-30 transition-all">
                          Next <ChevronRight size={14} />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* ══ AUTH ══════════════════════════════════════════════════════ */}
        {currentView === 'auth' && (
          <div className="flex min-h-screen">
            {/* Left panel — branding */}
            <div style={{ background: '#0e1114', borderRight: '1px solid #1e2127', width: '40%' }}
                 className="hidden lg:flex flex-col justify-between p-12">
              <div>
                <div className="flex items-center gap-2.5 mb-12">
                  <div style={{ background: '#f59e0b', borderRadius: 10, width: 30, height: 30 }}
                       className="flex items-center justify-center">
                    <Building2 size={16} color="#000" strokeWidth={2.5} />
                  </div>
                  <span className="text-[15px] font-semibold text-[#e8eaed]">Haven</span>
                </div>
                <h2 className="text-3xl font-bold text-[#e8eaed] leading-snug mb-4">
                  Apply for your next home,<br />faster than ever.
                </h2>
                <p className="text-[#6b7280] leading-relaxed">
                  Create a profile once, apply to multiple listings, and track everything in one dashboard.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  { icon: BadgeCheck, text: 'Verified listings only' },
                  { icon: Clock, text: 'Apply in under 5 minutes' },
                  { icon: TrendingUp, text: 'Real-time application status' },
                ].map(({ icon: Icon, text }) => (
                  <div key={text} className="flex items-center gap-3 text-sm text-[#6b7280]">
                    <Icon size={15} className="text-[#f59e0b]" /> {text}
                  </div>
                ))}
              </div>
            </div>

            {/* Right panel — form */}
            <div className="flex-1 flex items-center justify-center p-8">
              <div style={{ maxWidth: 380, width: '100%' }}>

                <button onClick={() => setCurrentView('listings')}
                        className="flex items-center gap-1.5 text-sm text-[#5f6368] hover:text-[#9aa0a6] mb-8 transition-colors">
                  <ChevronLeft size={14} /> Back to listings
                </button>

                {/* REGISTER */}
                {authMode === 'register' && (
                  <>
                    <h1 className="text-2xl font-bold text-[#e8eaed] mb-1">Create account</h1>
                    <p className="text-sm text-[#6b7280] mb-7">You'll need this to apply for listings.</p>
                    {authError && (
                      <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                           className="flex gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-5">
                        <AlertCircle size={15} className="shrink-0 mt-0.5" /> {authError}
                      </div>
                    )}
                    <form onSubmit={handleRegister} className="space-y-4">
                      <Field label="Username">
                        <input type="text" required value={usernameInput} autoFocus
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
                      <Field label="Password" hint="Use at least 8 characters">
                        <input type="password" required value={passwordInput}
                               onChange={e => setPasswordInput(e.target.value)}
                               placeholder="••••••••" className={inputCls} />
                      </Field>
                      <button type="submit" disabled={authLoading}
                              className="w-full py-2.5 rounded-lg text-sm font-semibold text-black disabled:opacity-60 transition-opacity hover:opacity-90 mt-2"
                              style={{ background: '#f59e0b' }}>
                        {authLoading ? 'Creating account…' : 'Create account'}
                      </button>
                    </form>
                    <p className="text-sm text-center text-[#5f6368] mt-6">
                      Already have an account?{' '}
                      <button onClick={() => { setAuthMode('login'); setAuthError(''); }} className="text-[#f59e0b] hover:underline">
                        Sign in
                      </button>
                    </p>
                  </>
                )}

                {/* OTP */}
                {authMode === 'otp' && (
                  <>
                    <div style={{ background: '#1e2127', border: '1px solid #2a2d33', borderRadius: 99 }}
                         className="w-12 h-12 flex items-center justify-center mb-5">
                      <Mail size={22} className="text-[#f59e0b]" />
                    </div>
                    <h1 className="text-2xl font-bold text-[#e8eaed] mb-1">Check your email</h1>
                    <p className="text-sm text-[#6b7280] mb-7">
                      We sent a 6-digit code to <span className="text-[#e8eaed]">{otpEmail}</span>. It expires in 10 minutes.
                    </p>
                    {otpMessage && (
                      <div style={{ background: '#1e2127', border: '1px solid #2a2d33' }}
                           className="p-3 rounded-lg text-xs text-[#9aa0a6] mb-4 break-all">{otpMessage}</div>
                    )}
                    {authError && (
                      <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                           className="flex gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-4">
                        <AlertCircle size={15} className="shrink-0 mt-0.5" /> {authError}
                      </div>
                    )}
                    <form onSubmit={handleVerifyOtp} className="space-y-4">
                      <Field label="Verification code">
                        <input type="text" required value={otpInput} autoFocus maxLength={6}
                               onChange={e => setOtpInput(e.target.value)}
                               placeholder="000000"
                               className={inputCls + " text-center tracking-[0.6em] text-xl font-bold"} />
                      </Field>
                      <button type="submit" disabled={authLoading}
                              className="w-full py-2.5 rounded-lg text-sm font-semibold text-black disabled:opacity-60"
                              style={{ background: '#f59e0b' }}>
                        {authLoading ? 'Verifying…' : 'Verify email'}
                      </button>
                    </form>
                  </>
                )}

                {/* LOGIN */}
                {authMode === 'login' && (
                  <>
                    <h1 className="text-2xl font-bold text-[#e8eaed] mb-1">Welcome back</h1>
                    <p className="text-sm text-[#6b7280] mb-7">Sign in to track your applications.</p>
                    {otpMessage && (
                      <div style={{ background: '#0d2b1a', border: '1px solid #166534' }}
                           className="flex items-center gap-2 p-3 rounded-lg text-sm text-emerald-400 mb-5">
                        <CheckCircle2 size={15} /> {otpMessage}
                      </div>
                    )}
                    {authError && (
                      <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                           className="flex gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-4">
                        <AlertCircle size={15} className="shrink-0 mt-0.5" /> {authError}
                      </div>
                    )}
                    <form onSubmit={handleLogin} className="space-y-4">
                      <Field label="Username">
                        <input type="text" required value={usernameInput} autoFocus
                               onChange={e => setUsernameInput(e.target.value)}
                               placeholder="yourname" className={inputCls} />
                      </Field>
                      <Field label="Password">
                        <input type="password" required value={passwordInput}
                               onChange={e => setPasswordInput(e.target.value)}
                               placeholder="••••••••" className={inputCls} />
                      </Field>
                      <button type="submit" disabled={authLoading}
                              className="w-full py-2.5 rounded-lg text-sm font-semibold text-black disabled:opacity-60"
                              style={{ background: '#f59e0b' }}>
                        {authLoading ? 'Signing in…' : 'Sign in'}
                      </button>
                    </form>
                    <p className="text-sm text-center text-[#5f6368] mt-6">
                      New here?{' '}
                      <button onClick={() => { setAuthMode('register'); setAuthError(''); setOtpMessage(''); }}
                              className="text-[#f59e0b] hover:underline">
                        Create an account
                      </button>
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ══ APPLY WIZARD ══════════════════════════════════════════════ */}
        {currentView === 'apply' && (
          <div className="max-w-2xl mx-auto px-8 py-10">
            <div className="mb-8">
              <button onClick={() => setCurrentView('listings')}
                      className="flex items-center gap-1.5 text-sm text-[#5f6368] hover:text-[#9aa0a6] mb-5 transition-colors">
                <ChevronLeft size={14} /> Back to listings
              </button>
              <h1 className="text-2xl font-bold text-[#e8eaed]">Rental application</h1>
              <p className="text-sm text-[#6b7280] mt-1">Takes about 5 minutes.</p>
            </div>

            {/* No listing selected */}
            {!selectedListing && !wizardDone ? (
              <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                   className="py-16 text-center rounded-xl">
                <ClipboardList size={32} className="mx-auto text-[#2a2d33] mb-4" />
                <p className="text-[#9aa0a6] font-medium">No listing selected</p>
                <p className="text-sm text-[#5f6368] mt-1">Go to Browse and click "Apply for this unit" on a listing.</p>
                <button onClick={() => setCurrentView('listings')}
                        className="mt-5 px-5 py-2 rounded-lg text-sm font-medium text-black"
                        style={{ background: '#f59e0b' }}>
                  Browse listings
                </button>
              </div>
            ) : wizardDone ? (
              /* ── SUCCESS SCREEN ── */
              <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                   className="py-16 text-center rounded-xl">
                <div style={{ background: '#0d2b1a', border: '1px solid #166534', borderRadius: 99 }}
                     className="w-16 h-16 flex items-center justify-center mx-auto mb-5">
                  <CheckCircle2 size={32} className="text-emerald-400" />
                </div>
                <h2 className="text-xl font-bold text-[#e8eaed] mb-2">Application submitted!</h2>
                <p className="text-sm text-[#6b7280] max-w-xs mx-auto">
                  Your application for <span className="text-[#e8eaed]">{selectedListing?.address}</span> is now under review. We'll notify you of any updates.
                </p>
                <div className="flex items-center justify-center gap-3 mt-8">
                  <button onClick={() => { setCurrentView('dashboard'); }}
                          className="px-5 py-2.5 rounded-lg text-sm font-medium text-black"
                          style={{ background: '#f59e0b' }}>
                    View my applications
                  </button>
                  <button onClick={() => { setWizardDone(false); setSelectedListing(null); setCurrentView('listings'); }}
                          style={{ border: '1px solid #2a2d33' }}
                          className="px-5 py-2.5 rounded-lg text-sm text-[#9aa0a6] hover:text-[#e8eaed] transition-all">
                    Browse more
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Selected listing banner */}
                <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                     className="flex justify-between items-center p-4 rounded-xl mb-6">
                  <div>
                    <p className="text-[10px] font-semibold text-[#5f6368] uppercase tracking-wider mb-1">Applying for</p>
                    <p className="text-sm font-medium text-[#e8eaed]">{selectedListing.address}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-semibold text-[#5f6368] uppercase tracking-wider mb-1">Rent</p>
                    <p className="text-sm font-bold text-[#f59e0b]">${parseInt(selectedListing.rent).toLocaleString()}/mo</p>
                  </div>
                </div>

                {/* Step bar */}
                <div className="flex items-center gap-2 mb-7 text-sm">
                  {['Your info', 'Documents', 'Review'].map((label, i) => {
                    const step = i + 1;
                    const done = wizardStep > step;
                    const active = wizardStep === step;
                    return (
                      <React.Fragment key={step}>
                        <div className={`flex items-center gap-1.5 transition-all ${active ? 'text-[#e8eaed]' : done ? 'text-emerald-400' : 'text-[#4a4d55]'}`}>
                          {done
                            ? <CheckCircle2 size={16} />
                            : <span style={{
                                width: 22, height: 22, borderRadius: 99,
                                border: `1.5px solid ${active ? '#f59e0b' : '#2a2d33'}`,
                                background: active ? '#f59e0b15' : 'transparent',
                                color: active ? '#f59e0b' : 'inherit'
                              }}
                                    className="flex items-center justify-center text-xs font-semibold">{step}</span>
                          }
                          <span className={active ? 'font-semibold' : ''}>{label}</span>
                        </div>
                        {i < 2 && <div className="flex-1 h-px" style={{ background: wizardStep > i + 1 ? '#166534' : '#1e2127' }} />}
                      </React.Fragment>
                    );
                  })}
                </div>

                {/* Error */}
                {wizardError && (
                  <div style={{ background: '#2a1515', border: '1px solid #4a1515' }}
                       className="flex items-start gap-2.5 p-3 rounded-lg text-sm text-red-400 mb-5">
                    <AlertCircle size={15} className="shrink-0 mt-0.5" />
                    <span>{wizardError}</span>
                  </div>
                )}

                {/* STEP 1 — Info */}
                {wizardStep === 1 && (
                  <form onSubmit={handleCreateApplicantProfile}
                        style={{ background: '#15181e', border: '1px solid #1e2127' }}
                        className="p-6 rounded-xl space-y-5">
                    <p className="text-sm font-semibold text-[#e8eaed]">Employment & finances</p>
                    <div className="grid grid-cols-2 gap-4">
                      <Field label="Employer">
                        <input type="text" required value={employer} onChange={e => setEmployer(e.target.value)}
                               placeholder="Company name" className={inputCls} />
                      </Field>
                      <Field label="Job title">
                        <input type="text" required value={jobTitle} onChange={e => setJobTitle(e.target.value)}
                               placeholder="Your role" className={inputCls} />
                      </Field>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
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
                               placeholder="720" min="300" max="900" className={inputCls} />
                      </Field>
                    </div>

                    <div style={{ borderTop: '1px solid #1e2127' }} className="pt-5">
                      <p className="text-sm font-semibold text-[#e8eaed] mb-4">Move-in details</p>
                      <div className="grid grid-cols-2 gap-4">
                        <Field label="Target move-in date">
                          <input type="date" required value={moveInDate} onChange={e => setMoveInDate(e.target.value)}
                                 className={inputCls} />
                        </Field>
                        <div className="flex items-center gap-6 pt-6">
                          <label className="flex items-center gap-2 text-sm text-[#9aa0a6] cursor-pointer select-none">
                            <input type="checkbox" checked={hasRentedBefore} onChange={e => setHasRentedBefore(e.target.checked)}
                                   className="accent-amber-400 w-4 h-4" />
                            Rented before?
                          </label>
                          <label className="flex items-center gap-2 text-sm text-[#9aa0a6] cursor-pointer select-none">
                            <input type="checkbox" checked={maritalStatus} onChange={e => setMaritalStatus(e.target.checked)}
                                   className="accent-amber-400 w-4 h-4" />
                            Married?
                          </label>
                        </div>
                      </div>
                      <div className="mt-4">
                        <Field label="Reason for moving (optional)">
                          <textarea rows="2" value={reason} onChange={e => setReason(e.target.value)}
                                    placeholder="e.g. relocating for work, need more space…"
                                    className={inputCls} />
                        </Field>
                      </div>
                    </div>

                    <button type="submit" disabled={submitting}
                            className="w-full py-2.5 rounded-lg text-sm font-semibold text-black disabled:opacity-50"
                            style={{ background: '#f59e0b' }}>
                      {submitting ? 'Saving…' : 'Continue to documents →'}
                    </button>
                  </form>
                )}

                {/* STEP 2 — Documents */}
                {wizardStep === 2 && (
                  <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                       className="p-6 rounded-xl space-y-5">
                    <div>
                      <p className="text-sm font-semibold text-[#e8eaed]">Verification documents</p>
                      <p className="text-sm text-[#6b7280] mt-1">
                        Upload at least one document — pay stub, bank statement, or ID.
                      </p>
                    </div>

                    {/* Uploaded docs list */}
                    {uploadedDocs.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-[10px] font-semibold text-[#5f6368] uppercase tracking-wider">Uploaded</p>
                        {uploadedDocs.map((doc, idx) => (
                          <div key={idx} style={{ background: '#1a1d22', border: '1px solid #22262e' }}
                               className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg">
                            <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                            <span className="text-sm text-[#e8eaed] font-medium">{doc.label}</span>
                            <span className="text-xs text-[#5f6368] ml-auto truncate max-w-[180px]">
                              {doc.file_field?.split('/').pop()}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Upload form */}
                    <form onSubmit={handleUploadDocument}
                          style={{ background: '#1a1d22', border: '1px solid #22262e' }}
                          className="p-4 rounded-lg space-y-3">
                      <p className="text-xs font-semibold text-[#6b7280] uppercase tracking-wider">Add a document</p>
                      <div className="grid grid-cols-2 gap-3">
                        <Field label="Type">
                          <select value={docLabel} onChange={e => setDocLabel(e.target.value)} className={inputCls}>
                            <option>Pay Stub</option>
                            <option>Bank Statement</option>
                            <option>ID Proof</option>
                            <option>Tax Return</option>
                          </select>
                        </Field>
                        <Field label="File">
                          <input id="file-input" type="file" required
                                 accept=".pdf,.jpg,.jpeg,.png"
                                 onChange={e => setSelectedFile(e.target.files[0])}
                                 className="w-full text-xs text-[#9aa0a6] file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-[#2a2d33] file:text-[#e8eaed] hover:file:bg-[#3a3d44] cursor-pointer" />
                        </Field>
                      </div>
                      <button type="submit" disabled={uploadingDoc}
                              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-black disabled:opacity-50"
                              style={{ background: '#f59e0b' }}>
                        <FileUp size={14} />
                        {uploadingDoc ? 'Uploading…' : 'Upload'}
                      </button>
                    </form>

                    <div className="flex gap-3 pt-2">
                      <button onClick={() => setWizardStep(1)}
                              style={{ border: '1px solid #2a2d33' }}
                              className="flex-1 py-2.5 rounded-lg text-sm text-[#9aa0a6] hover:text-[#e8eaed] transition-all">
                        ← Back
                      </button>
                      <button onClick={() => setWizardStep(3)} disabled={uploadedDocs.length === 0}
                              className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-black disabled:opacity-40"
                              style={{ background: '#f59e0b' }}>
                        Continue →
                      </button>
                    </div>
                  </div>
                )}

                {/* STEP 3 — Review & submit */}
                {wizardStep === 3 && (
                  <div style={{ background: '#15181e', border: '1px solid #1e2127' }}
                       className="p-6 rounded-xl space-y-5">
                    <div>
                      <p className="text-sm font-semibold text-[#e8eaed]">Review your application</p>
                      <p className="text-sm text-[#6b7280] mt-1">Looks good? Submit it and we'll take it from here.</p>
                    </div>

                    {/* Summary */}
                    <div style={{ background: '#1a1d22', border: '1px solid #22262e' }}
                         className="p-4 rounded-lg space-y-2.5 text-sm">
                      {[
                        ['Employer', employer],
                        ['Job title', jobTitle],
                        ['Annual income', income ? `$${parseInt(income).toLocaleString()}` : '—'],
                        ['Credit score', creditScore],
                        ['Documents', `${uploadedDocs.length} attached`],
                        ['Move-in date', moveInDate],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="text-[#5f6368]">{k}</span>
                          <span className="text-[#e8eaed] font-medium">{v || '—'}</span>
                        </div>
                      ))}
                    </div>

                    {/* Lease options */}
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
                        ← Back
                      </button>
                      <button onClick={handleFinalSubmitApplication} disabled={submitting}
                              className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-black disabled:opacity-50 flex items-center justify-center gap-2"
                              style={{ background: '#f59e0b' }}>
                        <Send size={14} />
                        {submitting ? 'Submitting…' : 'Submit application'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ══ DASHBOARD ════════════════════════════════════════════════ */}
        {currentView === 'dashboard' && (
          <div>
            {/* Dashboard header */}
            <div style={{ borderBottom: '1px solid #1e2127' }} className="px-10 pt-10 pb-8">
              <div className="flex items-end justify-between max-w-4xl">
                <div>
                  <h1 className="text-2xl font-bold text-[#e8eaed]">
                    {user ? `Hi, ${user.username} 👋` : 'Dashboard'}
                  </h1>
                  <p className="text-sm text-[#6b7280] mt-1">
                    {myApplications.length > 0
                      ? `You have ${myApplications.length} application${myApplications.length > 1 ? 's' : ''} on file.`
                      : 'Track your rental applications here.'}
                  </p>
                </div>
                <button onClick={fetchDashboardData}
                        className="flex items-center gap-1.5 text-sm text-[#5f6368] hover:text-[#9aa0a6] transition-colors">
                  <RefreshCw size={13} /> Refresh
                </button>
              </div>
            </div>

            <div className="px-10 py-8 max-w-5xl space-y-6">
              {loadingDashboard ? (
                <div className="grid grid-cols-2 gap-4">
                  {[...Array(2)].map((_, i) => (
                    <div key={i} style={{ background: '#15181e', border: '1px solid #1e2127' }} className="p-6 rounded-xl space-y-3">
                      <Skeleton className="h-3 w-1/3" />
                      <Skeleton className="h-9 w-1/2" />
                      <Skeleton className="h-3 w-2/3" />
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  {/* Stats row */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div style={{ background: '#15181e', border: '1px solid #1e2127' }} className="p-6 rounded-xl">
                      <div className="flex items-center gap-2 text-[#5f6368] text-xs font-semibold uppercase tracking-wider mb-4">
                        <TrendingUp size={13} /> Market overview
                      </div>
                      {marketStats ? (
                        <div className="flex gap-8">
                          <div>
                            <p className="text-3xl font-bold text-[#e8eaed]">{marketStats.total_listings?.toLocaleString() ?? '—'}</p>
                            <p className="text-xs text-[#5f6368] mt-1">total listings</p>
                          </div>
                          <div style={{ borderLeft: '1px solid #1e2127' }} className="pl-8">
                            <p className="text-3xl font-bold text-[#e8eaed]">
                              ${Math.round(marketStats.average_rent || 0).toLocaleString()}
                            </p>
                            <p className="text-xs text-[#5f6368] mt-1">avg rent / mo</p>
                          </div>
                          <div style={{ borderLeft: '1px solid #1e2127' }} className="pl-8">
                            <p className="text-3xl font-bold text-emerald-400">{marketStats.verified_listings ?? '—'}</p>
                            <p className="text-xs text-[#5f6368] mt-1">verified</p>
                          </div>
                        </div>
                      ) : <p className="text-sm text-[#5f6368]">Stats unavailable right now.</p>}
                    </div>

                    <div style={{ background: '#15181e', border: '1px solid #1e2127' }} className="p-6 rounded-xl">
                      <div className="flex items-center gap-2 text-[#5f6368] text-xs font-semibold uppercase tracking-wider mb-4">
                        <Star size={13} /> Tenant satisfaction
                      </div>
                      {reviewStats ? (
                        <div className="flex gap-8">
                          <div>
                            <p className="text-3xl font-bold text-[#e8eaed]">{Number(reviewStats.avg_cleanliness || 0).toFixed(1)}<span className="text-lg font-normal text-[#5f6368]">/5</span></p>
                            <p className="text-xs text-[#5f6368] mt-1">avg cleanliness</p>
                          </div>
                          <div style={{ borderLeft: '1px solid #1e2127' }} className="pl-8">
                            <p className="text-3xl font-bold text-[#e8eaed]">{Number(reviewStats.avg_maintenance || 0).toFixed(1)}<span className="text-lg font-normal text-[#5f6368]">/5</span></p>
                            <p className="text-xs text-[#5f6368] mt-1">maintenance</p>
                          </div>
                          <div style={{ borderLeft: '1px solid #1e2127' }} className="pl-8">
                            <p className="text-3xl font-bold text-[#e8eaed]">{Math.round(reviewStats.deposit_return_rate || 0)}%</p>
                            <p className="text-xs text-[#5f6368] mt-1">deposit returned</p>
                          </div>
                        </div>
                      ) : <p className="text-sm text-[#5f6368]">Review stats unavailable.</p>}
                    </div>
                  </div>

                  {/* My applications */}
                  <div style={{ background: '#15181e', border: '1px solid #1e2127' }} className="rounded-xl overflow-hidden">
                    <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid #1e2127' }}>
                      <p className="text-sm font-semibold text-[#e8eaed]">My applications</p>
                      {myApplications.length > 0 && (
                        <span style={{ background: '#1a1d22', border: '1px solid #2a2d33' }}
                              className="text-xs text-[#9aa0a6] px-2.5 py-0.5 rounded-full">
                          {myApplications.length}
                        </span>
                      )}
                    </div>

                    {myApplications.length === 0 ? (
                      <div className="py-14 text-center">
                        <ClipboardList size={30} className="mx-auto text-[#2a2d33] mb-3" />
                        <p className="text-sm text-[#9aa0a6] font-medium">No applications yet</p>
                        <p className="text-xs text-[#5f6368] mt-1">Apply for a listing to see it here.</p>
                        <button onClick={() => setCurrentView('listings')}
                                className="mt-5 px-4 py-2 rounded-lg text-sm font-medium text-black"
                                style={{ background: '#f59e0b' }}>
                          Browse listings
                        </button>
                      </div>
                    ) : (
                      <table className="w-full text-sm">
                        <thead>
                          <tr style={{ borderBottom: '1px solid #1e2127' }}>
                            {['Application', 'Submitted', 'Lease', 'Status'].map(h => (
                              <th key={h} className="px-6 py-3 text-left text-[10px] font-semibold text-[#5f6368] uppercase tracking-wider">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {myApplications.map((app) => (
                            <tr key={app.id} style={{ borderBottom: '1px solid #1e2127' }}
                                className="hover:bg-[#1a1d22] transition-colors">
                              <td className="px-6 py-4 text-xs text-[#5f6368] font-mono">
                                #{app.id?.slice(0, 8).toUpperCase()}
                              </td>
                              <td className="px-6 py-4 text-[#9aa0a6]">{app.submitted_at_date || '—'}</td>
                              <td className="px-6 py-4 text-[#9aa0a6]">{app.lease_term || 12} months</td>
                              <td className="px-6 py-4"><StatusBadge status={app.application_status} /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

      </main>

      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
