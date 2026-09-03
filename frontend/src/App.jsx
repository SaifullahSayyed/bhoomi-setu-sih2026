import React, { useState, useEffect } from 'react';
import { translations } from './i18n/translations';
import RegistrarDashboard from './views/RegistrarDashboard';
import CitizenView from './views/CitizenView';
import BankView from './views/BankView';
import CommunityGovernance from './views/CommunityGovernance';
import ArchitectureDemoView from './views/ArchitectureDemoView';
import AuthBar from './components/AuthBar';
import { ShieldCheck, UserCheck, Landmark, Users, Layers, Globe } from 'lucide-react';
const API_BASE = 'http://127.0.0.1:8000';
export default function App() {
  const [activeTab, setActiveTab] = useState('registrar');
  const [lang, setLang] = useState('en');
  const [currentAuth, setCurrentAuth] = useState(() => {
    try {
      const saved = localStorage.getItem('bhoomi_auth');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const t = translations[lang] || translations.en;

  // Auto-authenticate as default demo role (registrar) on first load if no token
  useEffect(() => {
    if (!currentAuth?.token) {
      fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'registrar' }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.access_token) {
            const authObj = {
              token: data.access_token,
              role: data.role,
              username: data.username,
              displayName: data.display_name,
              designation: data.designation,
              jurisdiction: data.jurisdiction,
            };
            setCurrentAuth(authObj);
            try {
              localStorage.setItem('bhoomi_auth', JSON.stringify(authObj));
            } catch {}
          }
        })
        .catch((err) => console.error('Initial demo auth failed:', err));
    }
  }, []);

  const handleAuthChange = (newAuth) => {
    setCurrentAuth(newAuth);
    try {
      localStorage.setItem('bhoomi_auth', JSON.stringify(newAuth));
    } catch {}
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {}
      <header className="border-b border-slate-800/80 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-tight text-slate-100">
                  {t.appTitle} <span className="text-emerald-400 font-normal text-sm">(SIH26014)</span>
                </h1>
                <span className="text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded font-semibold uppercase tracking-wider">
                  Land Stack
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">{t.subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* RBAC Role Selector */}
            <AuthBar
              apiBase={API_BASE}
              currentAuth={currentAuth}
              onAuthChange={handleAuthChange}
            />

            {/* Language Selector */}
            <div className="flex items-center bg-slate-800/80 border border-slate-700/80 rounded-lg p-0.5 text-xs font-semibold">
              <button
                onClick={() => setLang('en')}
                className={`px-2.5 py-1 rounded-md transition ${lang === 'en' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
              >
                EN
              </button>
              <button
                onClick={() => setLang('hi')}
                className={`px-2.5 py-1 rounded-md transition ${lang === 'hi' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
              >
                हिन्दी
              </button>
            </div>
          </div>
        </div>
      </header>
      {}
      <nav className="border-b border-slate-800/60 bg-slate-900/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 overflow-x-auto py-2">
          <button
            onClick={() => setActiveTab('registrar')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              activeTab === 'registrar'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>{t.registrarView}</span>
            <span className="text-[9px] bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-800">P1–2</span>
          </button>
          <button
            onClick={() => setActiveTab('citizen')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              activeTab === 'citizen'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
            }`}
          >
            <UserCheck className="w-4 h-4 text-emerald-400" />
            <span>{t.citizenView}</span>
            <span className="text-[9px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">P3</span>
          </button>
          <button
            onClick={() => setActiveTab('bank')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              activeTab === 'bank'
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
            }`}
          >
            <Landmark className="w-4 h-4 text-blue-400" />
            <span>{t.bankView} (Curtain)</span>
            <span className="text-[9px] bg-blue-950 text-blue-400 px-1.5 py-0.5 rounded border border-blue-800">P3</span>
          </button>
          <button
            onClick={() => setActiveTab('community')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              activeTab === 'community'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
            }`}
          >
            <Users className="w-4 h-4 text-amber-400" />
            <span>{t.communityView} (FRA)</span>
            <span className="text-[9px] bg-amber-950 text-amber-400 px-1.5 py-0.5 rounded border border-amber-800">P2b</span>
          </button>
          <button
            onClick={() => setActiveTab('arch')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              activeTab === 'arch'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4 text-purple-400" />
            <span>{t.archDemoView}</span>
            <span className="text-[9px] bg-purple-950 text-purple-400 px-1.5 py-0.5 rounded border border-purple-800">P4 POC</span>
          </button>
        </div>
      </nav>
      {}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'registrar' && (
          <RegistrarDashboard
            lang={lang}
            t={t}
            apiBase={API_BASE}
            currentAuth={currentAuth}
            onAuthChange={handleAuthChange}
          />
        )}
        {activeTab === 'citizen' && (
          <CitizenView
            lang={lang}
            t={t}
            apiBase={API_BASE}
            currentAuth={currentAuth}
            onAuthChange={handleAuthChange}
          />
        )}
        {activeTab === 'bank' && (
          <BankView
            lang={lang}
            t={t}
            apiBase={API_BASE}
            currentAuth={currentAuth}
            onAuthChange={handleAuthChange}
          />
        )}
        {activeTab === 'community' && (
          <CommunityGovernance
            lang={lang}
            t={t}
            apiBase={API_BASE}
            currentAuth={currentAuth}
            onAuthChange={handleAuthChange}
          />
        )}
        {activeTab === 'arch' && (
          <ArchitectureDemoView
            lang={lang}
            t={t}
            apiBase={API_BASE}
            currentAuth={currentAuth}
          />
        )}
      </main>
      {}
      <footer className="border-t border-slate-800/80 py-4 bg-slate-950 text-slate-400 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong>Bhoomi Setu (भूमि सेतु)</strong> — Built for SIH26014 (Ministry of Rural Development)
          </div>
          <div className="text-[11px] text-slate-400 italic text-center sm:text-right">
            {t.prototypeDisclaimer}
          </div>
        </div>
      </footer>
    </div>
  );
}
