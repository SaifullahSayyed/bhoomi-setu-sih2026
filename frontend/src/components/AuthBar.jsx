import React, { useState, useEffect } from 'react';
import { Shield, User, Landmark, Users, ChevronDown, Check, Key, LogOut } from 'lucide-react';

const ROLE_CONFIG = {
  registrar: {
    label: 'Sub-Registrar',
    color: 'border-emerald-500/40 bg-emerald-950/60 text-emerald-300',
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    icon: Shield,
    defaultName: 'R. K. Sharma (Pratapgarh, UP)',
  },
  community_member: {
    label: 'Gram Sabha Member',
    color: 'border-amber-500/40 bg-amber-950/60 text-amber-300',
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    icon: Users,
    defaultName: 'Devi Besra (Dongri Pahad, JH)',
  },
  bank: {
    label: 'Bank Credit Officer',
    color: 'border-blue-500/40 bg-blue-950/60 text-blue-300',
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    icon: Landmark,
    defaultName: 'Ananya Sen (SBI National)',
  },
  citizen: {
    label: 'Citizen Landowner',
    color: 'border-cyan-500/40 bg-cyan-950/60 text-cyan-300',
    badge: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    icon: User,
    defaultName: 'Ramesh Kumar (Landowner)',
  },
};

export default function AuthBar({ apiBase, currentAuth, onAuthChange }) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [demoProfiles, setDemoProfiles] = useState([]);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    fetch(`${apiBase}/auth/roles`)
      .then((res) => res.json())
      .then((data) => {
        if (data.profiles) setDemoProfiles(data.profiles);
      })
      .catch((err) => console.error('Failed to load demo roles:', err));
  }, [apiBase]);

  const handleRoleSelect = async (role) => {
    setSwitching(true);
    try {
      const res = await fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
      });
      const data = await res.json();
      if (data.access_token) {
        onAuthChange({
          token: data.access_token,
          role: data.role,
          username: data.username,
          displayName: data.display_name,
          designation: data.designation,
          jurisdiction: data.jurisdiction,
        });
      }
    } catch (e) {
      console.error('Login failed:', e);
    } finally {
      setSwitching(false);
      setDropdownOpen(false);
    }
  };

  const activeRole = currentAuth?.role || 'registrar';
  const roleMeta = ROLE_CONFIG[activeRole] || ROLE_CONFIG.registrar;
  const RoleIcon = roleMeta.icon;

  return (
    <div className="relative">
      <button
        onClick={() => setDropdownOpen(!dropdownOpen)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs transition shadow-sm ${roleMeta.color}`}
        title="Prototype Role-Based Access Control — Click to switch demo user"
      >
        <div className={`p-1 rounded-lg border ${roleMeta.badge}`}>
          <RoleIcon className="w-3.5 h-3.5" />
        </div>
        <div className="text-left hidden md:block">
          <div className="text-[10px] uppercase font-bold tracking-wider opacity-80 flex items-center gap-1">
            <span>{roleMeta.label}</span>
            <span className="text-[9px] bg-slate-900/80 px-1 py-0.2 rounded border border-slate-700/60 font-mono">RBAC</span>
          </div>
          <div className="text-xs font-semibold text-slate-100 truncate max-w-[150px]">
            {currentAuth?.displayName || roleMeta.defaultName}
          </div>
        </div>
        <ChevronDown className="w-3.5 h-3.5 opacity-70 ml-1" />
      </button>

      {dropdownOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setDropdownOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl z-50 p-3 space-y-2">
            <div className="border-b border-slate-800 pb-2 px-1">
              <div className="text-xs font-bold text-slate-100 flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-amber-400" />
                  Select Demo Identity (RBAC)
                </span>
                <span className="text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.5 rounded font-mono">
                  Prototype
                </span>
              </div>
              <p className="text-[10px] text-slate-400 mt-1 leading-snug">
                Pre-seeded credentials for evaluation. Enforces real JWT verification and role permissions on write endpoints.
              </p>
            </div>

            <div className="space-y-1.5 max-h-[300px] overflow-y-auto pt-1">
              {['registrar', 'community_member', 'bank', 'citizen'].map((roleKey) => {
                const isSelected = activeRole === roleKey;
                const meta = ROLE_CONFIG[roleKey];
                const Icon = meta.icon;
                const profile = demoProfiles.find((p) => p.role === roleKey);

                return (
                  <button
                    key={roleKey}
                    onClick={() => handleRoleSelect(roleKey)}
                    disabled={switching}
                    className={`w-full text-left p-2.5 rounded-xl border transition flex items-start gap-2.5 ${
                      isSelected
                        ? 'bg-slate-800/90 border-emerald-500/60 shadow'
                        : 'bg-slate-950/60 border-slate-800 hover:bg-slate-800/60 hover:border-slate-700'
                    }`}
                  >
                    <div className={`p-1.5 rounded-lg border mt-0.5 ${meta.badge}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-100">{meta.label}</span>
                        {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400" />}
                      </div>
                      <div className="text-[11px] text-slate-300 truncate">
                        {profile?.display_name || meta.defaultName}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                        User: {profile?.username || roleKey} · {profile?.jurisdiction || 'Demo'}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="pt-2 border-t border-slate-800 px-1">
              <div className="text-[10px] font-mono text-slate-400 bg-slate-950/70 p-2 rounded border border-slate-800/80">
                🏷️ <strong>Honesty Label:</strong> Demo credentials for judging purposes, not a production identity system (no Aadhaar linkage).
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
