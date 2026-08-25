import React, { useState } from 'react';
import { Landmark, CheckCircle, XCircle, Shield, Lock, EyeOff, AlertTriangle } from 'lucide-react';
export default function BankView({ lang, t, apiBase }) {
  const [queryUlpin, setQueryUlpin] = useState('UP231000000001');
  const [collateralState, setCollateralState] = useState(null);
  const [loading, setLoading] = useState(false);
  const handleVerify = async (e) => {
    e?.preventDefault();
    if (!queryUlpin) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/sealed/${queryUlpin.trim()}`);
      const data = await res.json();
      setCollateralState(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/20 text-blue-400 rounded-xl border border-blue-500/30">
            <Landmark className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">{t.bankView} — Lending Collateral Check</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Demonstrates the <strong>Torrens Curtain Principle</strong>: Instant cryptographic collateral verification without exposing private chain-of-title.
            </p>
          </div>
        </div>
        <form onSubmit={handleVerify} className="flex gap-2 max-w-lg pt-2">
          <input
            type="text"
            value={queryUlpin}
            onChange={(e) => setQueryUlpin(e.target.value)}
            placeholder="Enter ULPIN (e.g. UP231000000001)"
            className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm font-mono text-slate-100 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs px-5 py-2.5 rounded-xl transition"
          >
            {loading ? 'Querying Ledger...' : 'Verify Collateral'}
          </button>
        </form>
      </div>
      {}
      <div className="bg-blue-950/30 border border-blue-800/40 rounded-xl p-4 flex items-start gap-3 text-xs text-blue-200">
        <EyeOff className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-blue-300 block mb-0.5">Torrens Principle #2: The Curtain</span>
          {t.curtainPrincipleNote} Lenders do not need 30-year physical title searches. The blockchain Curtain Ledger confirms that the current state was verified by the Mirror Engine and sealed.
        </div>
      </div>
      {}
      {collateralState && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <div className="text-xs text-slate-400">Queried ULPIN</div>
              <div className="text-xl font-bold font-mono text-slate-100">{collateralState.ulpin}</div>
            </div>
            <div>
              {collateralState.found ? (
                <div className="bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 px-4 py-2 rounded-xl flex items-center gap-2 text-xs font-bold">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  Title Verified & Sealed on-chain
                </div>
              ) : (
                <div className="bg-amber-950/60 border border-amber-500/50 text-amber-300 px-4 py-2 rounded-xl flex items-center gap-2 text-xs font-bold">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Unsealed / Presumptive Only
                </div>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Visible to Financial Institution (Clean Attestation)
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800/80">
                  <span className="text-slate-400">Current Seal Status:</span>
                  <span className="font-semibold text-emerald-400">{collateralState.found ? 'Canonical Current Owner Sealed' : 'Not Sealed'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/80">
                  <span className="text-slate-400">Mirror Confidence at Sealing:</span>
                  <span className="font-mono font-bold text-slate-200">{collateralState.mirror_score || 0} / 100</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/80">
                  <span className="text-slate-400">Owner Identity Pseudonym:</span>
                  <span className="font-mono text-[11px] text-slate-400 truncate max-w-[180px]">{collateralState.owner_identity_hash || 'None'}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Assurance Backing:</span>
                  <span className="text-cyan-400 font-semibold">Active Pool Protection</span>
                </div>
              </div>
            </div>
            {}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <Lock className="w-4 h-4 text-amber-400" />
                Hidden Behind the Curtain (Privacy Preserved)
              </div>
              <div className="space-y-2 text-xs text-slate-400">
                <div className="flex items-center gap-2 p-2 bg-slate-900/60 rounded border border-slate-800">
                  <EyeOff className="w-3.5 h-3.5 text-amber-400" />
                  <span>Personal Aadhaar / Raw PII (Hashed only)</span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-slate-900/60 rounded border border-slate-800">
                  <EyeOff className="w-3.5 h-3.5 text-amber-400" />
                  <span>30-Year Historical Mutation & Partition Records</span>
                </div>
                <div className="flex items-center gap-2 p-2 bg-slate-900/60 rounded border border-slate-800">
                  <EyeOff className="w-3.5 h-3.5 text-amber-400" />
                  <span>Original Handwritten Devanagari/Hindi Revenue Registers</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
