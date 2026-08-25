import React, { useState, useEffect } from 'react';
import { Users, Vote, CheckSquare, Activity, AlertTriangle, ShieldCheck, WifiOff, RefreshCw } from 'lucide-react';
export default function CommunityGovernance({ lang, t, apiBase }) {
  const [commInfo, setCommInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [actionDesc, setActionDesc] = useState('Authorize Forest Resource Leasing (Tendu/Mahua)');
  const [voteSubmitting, setVoteSubmitting] = useState(false);
  const [voteResponse, setVoteResponse] = useState(null);
  const [offlineMode, setOfflineMode] = useState(false);
  const fetchCommunityInfo = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/community/info`);
      const data = await res.json();
      setCommInfo(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetchCommunityInfo();
  }, []);
  const toggleMemberSelection = (idx) => {
    if (selectedMembers.includes(idx)) {
      setSelectedMembers(selectedMembers.filter(i => i !== idx));
    } else {
      setSelectedMembers([...selectedMembers, idx]);
    }
  };
  const handleCastVote = async (isOffline) => {
    if (selectedMembers.length === 0) return;
    setVoteSubmitting(true);
    setVoteResponse(null);
    try {
      const res = await fetch(`${apiBase}/community/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_id: 0,
          member_indices: selectedMembers,
          offline_batch: isOffline,
        }),
      });
      const data = await res.json();
      setVoteResponse(data);
      fetchCommunityInfo();
    } catch (e) {
      setVoteResponse({ success: false, error: e.message });
    } finally {
      setVoteSubmitting(false);
    }
  };
  const gini = commInfo?.governance_health?.gini_coefficient ?? 0;
  const healthStatus = commInfo?.governance_health?.health_status ?? 'healthy';
  return (
    <div className="space-y-6">
      {}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Community Entity</div>
          <div className="text-lg font-bold text-amber-400 mt-1">Dongri Pahad Gram Sabha</div>
          <div className="text-xs text-slate-400 mt-1">Forest Rights Act (FRA) CFR</div>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Registered Members</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{commInfo?.member_count || 20}</div>
          <div className="text-xs text-slate-400 mt-1">Multi-sig Quorum: 60% (12 votes)</div>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Elite-Capture Risk (Gini)</div>
          <div className={`text-2xl font-bold font-mono mt-1 ${
            healthStatus === 'healthy' ? 'text-emerald-400' :
            healthStatus === 'warning' ? 'text-amber-400' : 'text-rose-400'
          }`}>
            G = {gini}
          </div>
          <div className="text-xs text-slate-400 mt-1">{commInfo?.governance_health?.health_label}</div>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Historical Resolutions</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">{commInfo?.voting_history_count || 15}</div>
          <div className="text-xs text-slate-400 mt-1">Recorded on CommunityTenure.sol</div>
        </div>
      </div>
      {}
      <div className="bg-amber-950/30 border border-amber-800/40 rounded-xl p-4 flex items-start gap-3 text-xs text-amber-200">
        <Activity className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-300 block mb-0.5">Priority 2b: Elite-Capture Detection & FRA Community Tenure</span>
          Unlike individual titling, Forest Rights Act lands belong collectively to the Gram Sabha. Bhoomi Setu enforces 60% multi-sig quorum and actively monitors voting equality via the Gini coefficient:
          <span className="font-mono bg-amber-950/80 px-2 py-0.5 rounded text-[11px] ml-1 text-amber-300">
            G = (2 × Σ(i · x_i)) / (n · Σx_i) - (n + 1) / n
          </span>
        </div>
      </div>
      {}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {}
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Vote className="w-4 h-4 text-amber-400" />
              Active Resolution & Signature Collection
            </h3>
            <span className="text-xs font-mono text-amber-400 bg-amber-950/60 border border-amber-800 px-2 py-0.5 rounded">
              Quorum: 60% Required
            </span>
          </div>
          <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-lg text-xs space-y-1">
            <div className="text-slate-400">Proposed Resolution:</div>
            <div className="font-semibold text-slate-200">{actionDesc}</div>
          </div>
          <div>
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span>Select Gram Sabha Members Present ({selectedMembers.length} selected):</span>
              <button
                onClick={() => setSelectedMembers(selectedMembers.length === 20 ? [] : Array.from({ length: 20 }, (_, i) => i))}
                className="text-amber-400 hover:underline text-[11px]"
              >
                {selectedMembers.length === 20 ? 'Deselect All' : 'Select All 20 Members'}
              </button>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-[220px] overflow-y-auto p-1">
              {commInfo?.registered_members?.map((m, idx) => {
                const isSelected = selectedMembers.includes(idx);
                const pastVotes = commInfo.governance_health?.participation_counts?.[m.name_pseudonym] || 0;
                return (
                  <div
                    key={m.member_id}
                    onClick={() => toggleMemberSelection(idx)}
                    className={`p-2.5 rounded-lg border text-left cursor-pointer transition text-xs ${
                      isSelected
                        ? 'bg-amber-950/60 border-amber-500/70 text-amber-200'
                        : 'bg-slate-950/50 border-slate-800/80 text-slate-300 hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="font-medium truncate">{m.name_pseudonym}</div>
                    <div className="text-[10px] text-slate-400 font-mono flex justify-between mt-1">
                      <span>Mem #{m.member_id}</span>
                      <span className="text-amber-400/80">{pastVotes} past votes</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          {}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Signatures: {selectedMembers.length} / 20</span>
              <span className={selectedMembers.length >= 12 ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                {selectedMembers.length >= 12 ? 'Quorum Met (≥60%)' : `${12 - selectedMembers.length} more needed for quorum`}
              </span>
            </div>
            <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-800">
              <div
                className={`h-full transition-all duration-300 ${
                  selectedMembers.length >= 12 ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
                style={{ width: `${Math.min(100, (selectedMembers.length / 20) * 100)}%` }}
              />
            </div>
          </div>
          {}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <button
              disabled={selectedMembers.length === 0 || voteSubmitting}
              onClick={() => handleCastVote(false)}
              className="py-2.5 px-3 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold text-xs rounded-xl transition flex items-center justify-center gap-1.5"
            >
              <Vote className="w-4 h-4" />
              {voteSubmitting ? 'Casting...' : 'Cast Multi-Sig Vote'}
            </button>
            <button
              disabled={selectedMembers.length === 0 || voteSubmitting}
              onClick={() => handleCastVote(true)}
              className="py-2.5 px-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-50 text-amber-300 font-semibold text-xs rounded-xl transition flex items-center justify-center gap-1.5"
            >
              <WifiOff className="w-4 h-4 text-amber-400" />
              {t.offlineBatch}
            </button>
          </div>
          {voteResponse && (
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-1">
              <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                <CheckSquare className="w-4 h-4" />
                Vote Recorded on CommunityTenure.sol
              </div>
              <div className="text-[10px] text-slate-400">
                {voteResponse.offline_batch_note || 'Signatures processed via multi-sig contract.'}
              </div>
            </div>
          )}
        </div>
        {}
        <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Participation Equality Meter (Gini)
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Tracks if voting influence is monopolized by village elites.
            </p>
          </div>
          {}
          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 text-center space-y-2">
            <div className="text-xs text-slate-400 uppercase font-semibold">Current Governance Inequality</div>
            <div className={`text-3xl font-black font-mono ${
              healthStatus === 'healthy' ? 'text-emerald-400' :
              healthStatus === 'warning' ? 'text-amber-400' : 'text-rose-400'
            }`}>
              G = {gini}
            </div>
            <div className="text-xs font-semibold text-slate-200">
              {commInfo?.governance_health?.health_label}
            </div>
            <div className="text-[11px] text-slate-400 max-w-xs mx-auto">
              {gini < 0.3 ? 'Participation evenly distributed across hamlet members.' :
               gini < 0.5 ? 'Moderate concentration detected among vocal elders.' :
               'Alert: High concentration — majority of votes cast by top 3 members.'}
            </div>
          </div>
          {}
          <div className="space-y-2">
            <div className="text-xs font-semibold text-slate-300">Top Member Activity:</div>
            <div className="space-y-1.5 max-h-[220px] overflow-y-auto pr-1">
              {commInfo?.registered_members?.slice(0, 8).map((m) => {
                const count = commInfo.governance_health?.participation_counts?.[m.name_pseudonym] || 0;
                const total = commInfo.total_votes || 15;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={m.member_id} className="text-xs bg-slate-950/40 p-2 rounded border border-slate-800/60 space-y-1">
                    <div className="flex justify-between text-slate-300">
                      <span className="font-medium">{m.name_pseudonym}</span>
                      <span className="font-mono text-amber-400">{count} votes ({pct}%)</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                      <div className="bg-amber-500 h-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
