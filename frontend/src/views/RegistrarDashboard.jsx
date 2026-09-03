import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle, RefreshCw, FileText, Lock, Key, DollarSign, Database, Map as MapIcon, List, FileWarning, Check, MessageSquare, GitPullRequest } from 'lucide-react';
import ParcelMap from '../components/ParcelMap';
export default function RegistrarDashboard({ lang, t, apiBase, currentAuth, onAuthChange }) {
  const [parcels, setParcels] = useState([]);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [selectedVillage, setSelectedVillage] = useState('All');
  const [loading, setLoading] = useState(false);
  const [sealingLoading, setSealingLoading] = useState(false);
  const [sealResult, setSealResult] = useState(null);
  const [filterFlag, setFilterFlag] = useState('all');
  const [poolBalance, setPoolBalance] = useState(0);
  const [totalDatasetCount, setTotalDatasetCount] = useState(500);
  const [viewMode, setViewMode] = useState('split'); 
  const [apiError, setApiError] = useState(null);
  const [disputes, setDisputes] = useState([]);
  const [resolvingId, setResolvingId] = useState(null);

  // Tier 3a Mutation requests state
  const [mutations, setMutations] = useState([]);
  const [approvingMutationId, setApprovingMutationId] = useState(null);
  const [mutationActionError, setMutationActionError] = useState(null);

  const fetchMutations = async () => {
    try {
      const res = await fetch(`${apiBase}/mutation-requests/`);
      const data = await res.json();
      setMutations(data.requests || []);
    } catch (e) {
      console.error('Failed to fetch mutations:', e);
    }
  };

  const handleApproveMutation = async (requestId) => {
    setApprovingMutationId(requestId);
    setMutationActionError(null);
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (currentAuth?.token) {
        headers['Authorization'] = `Bearer ${currentAuth.token}`;
      }
      const res = await fetch(`${apiBase}/mutation-requests/${requestId}/approve`, {
        method: 'POST',
        headers,
      });
      const data = await res.json();
      if (!res.ok) {
        setMutationActionError(data.detail || 'Approval rejected by Mirror Engine');
      }
      fetchMutations();
      fetchParcels();
    } catch (e) {
      console.error('Failed to approve mutation:', e);
      setMutationActionError(e.message);
    } finally {
      setApprovingMutationId(null);
    }
  };

  const fetchDisputes = async () => {
    try {
      const headers = {};
      if (currentAuth?.token) {
        headers['Authorization'] = `Bearer ${currentAuth.token}`;
      }
      const res = await fetch(`${apiBase}/disputes/`, { headers });
      const data = await res.json();
      setDisputes(data.disputes || []);
    } catch (e) {
      console.error('Failed to fetch disputes:', e);
    }
  };

  const handleResolveDispute = async (disputeId, status, notes) => {
    setResolvingId(disputeId);
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (currentAuth?.token) {
        headers['Authorization'] = `Bearer ${currentAuth.token}`;
      }
      const res = await fetch(`${apiBase}/disputes/${disputeId}/resolve`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          status: status || 'RESOLVED',
          resolution_notes: notes || 'Administrative inquiry concluded. Land record verified.',
        }),
      });
      if (res.ok) {
        fetchDisputes();
      }
    } catch (e) {
      console.error('Failed to resolve dispute:', e);
    } finally {
      setResolvingId(null);
    }
  };

  const fetchParcels = async () => {
    setLoading(true);
    setApiError(null);
    try {
      let url = `${apiBase}/parcels/?limit=500`;
      if (selectedVillage !== 'All') {
        url += `&village=${encodeURIComponent(selectedVillage)}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setParcels(data.parcels || []);
      if (data.total_dataset_count) {
        setTotalDatasetCount(data.total_dataset_count);
      }
      if (data.parcels?.length > 0 && !selectedParcel) {
        setSelectedParcel(data.parcels[0]);
      }
    } catch (e) {
      console.error(e);
      setApiError(`Backend API connection failed (${e.message}). Ensure FastAPI server is running on ${apiBase}`);
    } finally {
      setLoading(false);
    }
  };
  const fetchPoolBalance = async () => {
    try {
      const res = await fetch(`${apiBase}/pool/balance`);
      const data = await res.json();
      setPoolBalance(data.balance || 0);
    } catch (e) {
      console.error(e);
    }
  };
  useEffect(() => {
    fetchParcels();
    fetchPoolBalance();
    fetchDisputes();
    fetchMutations();
  }, [selectedVillage]);

  const handleSeal = async (ulpin, declaredValue) => {
    setSealingLoading(true);
    setSealResult(null);
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (currentAuth?.token) {
        headers['Authorization'] = `Bearer ${currentAuth.token}`;
      }
      const res = await fetch(`${apiBase}/seal/${ulpin}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ declared_value_inr: declaredValue }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSealResult({ sealed: false, reason: data.detail || `HTTP ${res.status}: Action restricted to Sub-Registrar` });
        return;
      }
      setSealResult(data);
      fetchParcels();
      fetchPoolBalance();
    } catch (e) {
      setSealResult({ sealed: false, reason: e.message });
    } finally {
      setSealingLoading(false);
    }
  };
  const filteredParcels = parcels.filter(p => {
    if (filterFlag === 'all') return true;
    if (filterFlag === 'mismatch') return p.mirror_result?.flags?.some(f => f.includes('area_mismatch'));
    if (filterFlag === 'duplicate') return p.mirror_result?.flags?.some(f => f.includes('duplicate') || f.includes('overlap'));
    if (filterFlag === 'benami') return p.mirror_result?.flags?.some(f => f.includes('owner_pattern'));
    if (filterFlag === 'eligible') return p.mirror_result?.sealing_eligible;
    return true;
  });
  return (
    <div className="space-y-6">
      {apiError && (
        <div className="bg-rose-950/70 border border-rose-600/60 text-rose-200 px-4 py-3 rounded-xl flex items-center justify-between text-xs font-semibold">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>⚠️ {apiError}</span>
          </div>
          <button
            onClick={fetchParcels}
            className="bg-rose-900/60 hover:bg-rose-800 border border-rose-700 px-2.5 py-1 rounded text-white transition"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Role Alert Banner if viewing as non-registrar */}
      {currentAuth && currentAuth.role !== 'registrar' && (
        <div className="bg-amber-950/40 border border-amber-500/40 text-amber-200 px-4 py-3 rounded-xl flex items-center justify-between text-xs font-medium shadow-md">
          <div className="flex items-center gap-2.5">
            <Lock className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold text-amber-300">
                Viewing as {currentAuth.displayName || currentAuth.role} (Read-Only Mode):
              </span>
              <span className="text-amber-200/80 ml-1.5">
                Dashboard is readable, but cryptographic sealing on CurtainLedger.sol requires Sub-Registrar authorization.
              </span>
            </div>
          </div>
          <button
            onClick={async () => {
              const res = await fetch(`${apiBase}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: 'registrar' }),
              });
              const data = await res.json();
              if (data.access_token) {
                onAuthChange?.({
                  token: data.access_token,
                  role: data.role,
                  username: data.username,
                  displayName: data.display_name,
                  designation: data.designation,
                  jurisdiction: data.jurisdiction,
                });
              }
            }}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-3 py-1.5 rounded-lg text-xs transition shrink-0 ml-3 shadow"
          >
            Switch to Sub-Registrar
          </button>
        </div>
      )}

      {}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Parcels Indexed</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {selectedVillage === 'All' ? totalDatasetCount : parcels.length}
          </div>
          <div className="text-xs text-emerald-400 mt-1">
            {selectedVillage === 'All' ? '500 Across 3 Villages' : `${selectedVillage} records`}
          </div>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Clean &amp; Sealable (≥85)</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {parcels.filter(p => p.mirror_result?.sealing_eligible && !(p.mirror_result?.flags?.length > 0)).length || 0}
          </div>
          <div className="text-xs text-slate-400 mt-1">Score ≥ 85, zero flags detected</div>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Flagged Parcels</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {parcels.filter(p => p.mirror_result?.flags?.length > 0 && p.schema_type !== 'community').length || 0}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {(() => {
              const flaggedSealable = parcels.filter(p => p.mirror_result?.flags?.length > 0 && p.mirror_result?.sealing_eligible).length;
              const flaggedBlocked = parcels.filter(p => p.mirror_result?.flags?.length > 0 && !p.mirror_result?.sealing_eligible && p.schema_type !== 'community').length;
              return `${flaggedSealable} minor (still sealable) · ${flaggedBlocked} blocked`;
            })()}
          </div>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Assurance Pool Solvency</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">₹{(poolBalance * 1000).toLocaleString()}</div>
          <div className="text-xs text-slate-400 mt-1">Risk-indexed self-funding</div>
        </div>
        <div
          className="bg-purple-950/40 border border-purple-800/60 rounded-xl p-4 cursor-help"
          title={t.communityGovernedTooltip || "Collectively owned under the Forest Rights Act — governed via CommunityTenure.sol multi-sig, not subject to individual Mirror Engine reconciliation."}
        >
          <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider">{t.communityGoverned || "Community-Governed (FRA)"}</div>
          <div className="text-2xl font-bold text-purple-300 mt-1">
            {parcels.filter(p => p.schema_type === 'community').length || 100}
          </div>
          <div className="text-xs text-purple-400/70 mt-1">FRA multi-sig, not Mirror-scored</div>
        </div>

      </div>
      {}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs text-slate-400 font-medium">Village:</label>
          <select
            value={selectedVillage}
            onChange={(e) => setSelectedVillage(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-sm rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="All">All Jurisdictions (3 Villages)</option>
            <option value="Rampur Khurd">Rampur Khurd (UP - Bigha)</option>
            <option value="Vellore Nagar">Vellore Nagar (TN - Cents)</option>
            <option value="Dongri Pahad">Dongri Pahad (JH - Community)</option>
          </select>
          <label className="text-xs text-slate-400 font-medium ml-2">Anomaly Filter:</label>
          <select
            value={filterFlag}
            onChange={(e) => setFilterFlag(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-sm rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All Records</option>
            <option value="eligible">Eligible to Seal (Score ≥ 85)</option>
            <option value="mismatch">Area Discrepancies (&gt;10%)</option>
            <option value="duplicate">Duplicate Claims / Overlaps</option>
            <option value="benami">Benami Pattern Detected</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          {}
          <div className="flex items-center bg-slate-800 border border-slate-700 rounded-lg p-0.5 text-xs font-semibold">
            <button
              onClick={() => setViewMode('split')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition ${
                viewMode === 'split' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <MapIcon className="w-3.5 h-3.5" />
              <span>GIS Map + List</span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition ${
                viewMode === 'table' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <List className="w-3.5 h-3.5" />
              <span>List Only</span>
            </button>
            <button
              onClick={() => setViewMode('disputes')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md transition ${
                viewMode === 'disputes' ? 'bg-amber-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileWarning className="w-3.5 h-3.5 text-amber-400" />
              <span>Grievances ({disputes.filter(d => d.status === 'OPEN').length} Open)</span>
            </button>
            <button
              onClick={() => setViewMode('mutations')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md transition ${
                viewMode === 'mutations' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GitPullRequest className="w-3.5 h-3.5 text-cyan-400" />
              <span>Mutations ({mutations.filter(m => m.status === 'PENDING').length} Pending)</span>
            </button>
          </div>
          <button
            onClick={fetchParcels}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs px-3 py-1.5 rounded-lg transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>
      {}
      {viewMode === 'split' && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <span className="flex items-center gap-1.5">
              <MapIcon className="w-4 h-4 text-emerald-400" />
              Interactive GIS Cadastral Map (Click any polygon to inspect)
            </span>
            <span className="text-[11px] text-slate-400">
              Showing {filteredParcels.length} Polygons across {selectedVillage === 'All' ? '3 States' : selectedVillage}
            </span>
          </div>
          <ParcelMap
            parcels={filteredParcels}
            selectedParcel={selectedParcel}
            onSelectParcel={(p) => { setSelectedParcel(p); setSealResult(null); }}
            height="340px"
            villageName={selectedVillage}
          />
        </div>
      )}

      {viewMode === 'disputes' ? (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <FileWarning className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">Citizen Land Grievances &amp; Dispute Queue</h3>
                <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded font-mono">
                  Off-Chain Grievance Store
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Field inquiries, boundary overlap claims, and inheritance petitions filed by citizens. Sub-Registrar can review evidence and update inquiry status.
              </p>
            </div>
            <button
              onClick={fetchDisputes}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh Queue
            </button>
          </div>

          <div className="space-y-3">
            {disputes.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800">
                No disputes registered in current jurisdiction.
              </div>
            ) : (
              disputes.map((d) => (
                <div key={d.dispute_id} className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-amber-400">{d.dispute_id}</span>
                      <span className="text-slate-600">•</span>
                      <span className="font-mono text-xs text-slate-300">ULPIN: {d.ulpin}</span>
                      <span className="text-slate-600">•</span>
                      <span className="text-xs uppercase font-semibold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        {d.dispute_type?.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                        d.status === 'RESOLVED' ? 'bg-emerald-950 text-emerald-300 border-emerald-700' :
                        d.status === 'UNDER_INQUIRY' ? 'bg-blue-950 text-blue-300 border-blue-700' :
                        'bg-amber-950 text-amber-300 border-amber-700'
                      }`}>
                        {d.status}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {d.filed_at ? new Date(d.filed_at).toLocaleDateString() : 'Recent'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div>
                      <div className="text-slate-500 text-[11px]">Complainant</div>
                      <div className="font-semibold text-slate-200 mt-0.5">{d.complainant_name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{d.contact_info}</div>
                    </div>
                    <div className="md:col-span-2">
                      <div className="text-slate-500 text-[11px]">Grievance Summary</div>
                      <p className="text-slate-300 mt-0.5 leading-relaxed">{d.description}</p>
                      {d.evidence_summary && (
                        <div className="text-[11px] text-slate-400 mt-1 italic">
                          Evidence: {d.evidence_summary}
                        </div>
                      )}
                      {d.resolution_notes && (
                        <div className="text-[11px] text-emerald-400 mt-1.5 bg-emerald-950/30 p-2 rounded border border-emerald-800/40">
                          <strong>Resolution Note:</strong> {d.resolution_notes}
                        </div>
                      )}
                    </div>
                  </div>

                  {d.status !== 'RESOLVED' && (
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800/60">
                      {d.status === 'OPEN' && (
                        <button
                          disabled={resolvingId === d.dispute_id}
                          onClick={() => handleResolveDispute(d.dispute_id, 'UNDER_INQUIRY', 'Tehsil revenue team deputed for joint boundary inspection.')}
                          className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 text-blue-300 text-xs font-semibold rounded-lg transition"
                        >
                          Mark Under Field Inquiry
                        </button>
                      )}
                      <button
                        disabled={resolvingId === d.dispute_id}
                        onClick={() => handleResolveDispute(d.dispute_id, 'RESOLVED', 'Field survey completed; boundary marks reconciled per spatial coordinates.')}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1 shadow"
                      >
                        <Check className="w-3.5 h-3.5" />
                        Resolve Grievance
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      ) : viewMode === 'mutations' ? (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <GitPullRequest className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-slate-100">Citizen Mutation &amp; Title Transfer Review Queue</h3>
                <span className="text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded font-mono">
                  Off-Chain Queue ➔ Curtain Ledger Sealing
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Citizen-initiated deed applications. <strong>Approve &amp; Seal</strong> re-invokes Mirror Engine scoring on new ownership/area parameters before executing the on-chain mutation transaction.
              </p>
            </div>
            <button
              onClick={fetchMutations}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh Queue
            </button>
          </div>

          {mutationActionError && (
            <div className="p-3 bg-rose-950/40 border border-rose-600/50 rounded-lg text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{mutationActionError}</span>
            </div>
          )}

          <div className="space-y-3">
            {mutations.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-xs">
                No mutation requests pending review.
              </div>
            ) : (
              mutations.map((m) => (
                <div key={m.request_id} className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-cyan-400">{m.request_id}</span>
                      <span className="text-slate-500">•</span>
                      <span className="text-xs text-slate-300 font-semibold">{m.ulpin}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                        m.status === 'APPROVED_AND_SEALED'
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          : m.status === 'REJECTED'
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                          : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      }`}>
                        {m.status}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500">
                      Filed: {new Date(m.filed_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-300">
                    <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 block uppercase font-mono">Applicant &amp; Transfer</span>
                      <div className="font-semibold text-slate-200 mt-0.5">{m.applicant_name}</div>
                      <div className="text-slate-400 text-[11px]">Type: <span className="text-slate-300 font-mono capitalize">{m.mutation_type} Deed</span></div>
                    </div>
                    <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 block uppercase font-mono">Transferee / Buyer</span>
                      <div className="font-semibold text-cyan-300 mt-0.5">{m.new_owner_name}</div>
                      <div className="text-slate-500 text-[10px] font-mono truncate" title={m.new_owner_id_hash}>ID: {m.new_owner_id_hash}</div>
                    </div>
                    <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 block uppercase font-mono">Deed &amp; Consideration</span>
                      <div className="font-semibold text-emerald-400 mt-0.5">₹{Number(m.declared_value_inr).toLocaleString()}</div>
                      <div className="text-slate-400 text-[11px]">Ref: <span className="font-mono text-slate-300">{m.deed_reference}</span></div>
                    </div>
                  </div>

                  {m.status === 'APPROVED_AND_SEALED' && (
                    <div className="bg-emerald-950/30 border border-emerald-600/40 rounded-lg p-3 text-xs text-emerald-300 space-y-1">
                      <div className="font-semibold flex items-center gap-1.5 text-emerald-400">
                        <ShieldCheck className="w-4 h-4" />
                        Mirror Engine Re-Verification Passed (Score: {m.mirror_verification?.mirror_score}/100) — On-Chain Mutation Sealed
                      </div>
                      <div className="font-mono text-[11px] text-slate-400">
                        CurtainLedger TX Hash: <span className="text-emerald-300">{m.tx_hash}</span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Approved by {m.approved_by} at {new Date(m.approved_at).toLocaleString()}
                      </div>
                    </div>
                  )}

                  {m.status === 'REJECTED' && (
                    <div className="bg-rose-950/30 border border-rose-600/40 rounded-lg p-3 text-xs text-rose-300 space-y-1">
                      <div className="font-semibold flex items-center gap-1.5 text-rose-400">
                        <AlertTriangle className="w-4 h-4" />
                        Mutation Rejected by Mirror Engine
                      </div>
                      <div className="text-[11px] text-rose-200">
                        {m.rejection_reason}
                      </div>
                    </div>
                  )}

                  {m.status === 'PENDING' && (
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[11px] text-slate-400">
                        Action required: Re-scores candidate cadastral geometry &amp; RoR text. Rejects if score &lt; 85.
                      </span>
                      <button
                        disabled={approvingMutationId === m.request_id}
                        onClick={() => handleApproveMutation(m.request_id)}
                        className="px-3.5 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1.5 shadow"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        {approvingMutationId === m.request_id ? 'Re-Verifying...' : 'Re-Verify with Mirror Engine & Approve Seal'}
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {}
        <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-[600px]">
          <div className="p-3 border-b border-slate-800 bg-slate-900 flex justify-between items-center text-xs text-slate-400 font-semibold uppercase">
            <span>Parcels ({filteredParcels.length})</span>
            <span>Mirror Score</span>
          </div>
          <div className="overflow-y-auto flex-1 divide-y divide-slate-800/60">
            {filteredParcels.map((p) => {
              const score = p.mirror_result?.mirror_score ?? 0;
              const isSelected = selectedParcel?.ulpin === p.ulpin;
              const isCommunity = p.schema_type === 'community';
              return (
                <div
                  key={p.ulpin}
                  onClick={() => { setSelectedParcel(p); setSealResult(null); }}
                  className={`p-3.5 cursor-pointer transition flex items-center justify-between text-left ${
                    isSelected ? 'bg-emerald-950/40 border-l-4 border-emerald-500' : 'hover:bg-slate-800/40'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-200">{p.ulpin}</span>
                      {isCommunity ? (
                        <span className="text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 px-1.5 py-0.5 rounded font-semibold">FRA Community</span>
                      ) : (
                        <span className="text-[10px] text-slate-400">{p.village}</span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 truncate max-w-[220px]">
                      {isCommunity ? p.community_entity : p.owners?.map(o => o.name).join(', ')}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`px-2.5 py-1 rounded-md font-mono text-xs font-bold ${
                      score >= 85 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                      score >= 70 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                      'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    }`}>
                      {score}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        {}
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-5 h-[600px] overflow-y-auto">
          {selectedParcel ? (
            <>
              {}
              <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold font-mono text-slate-100">{selectedParcel.ulpin}</h3>
                    <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                      {selectedParcel.village} ({selectedParcel.state})
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    {selectedParcel.schema_type === 'community' ? (
                      <span className="text-purple-400 font-medium">Forest Rights Act (FRA) Gram Sabha Collective Title</span>
                    ) : (
                      `Owner(s): ${selectedParcel.owners?.map(o => `${o.name} (${o.share_fraction * 100}%)`).join(', ')}`
                    )}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Mirror Score</div>
                  <div className={`text-2xl font-black font-mono ${
                    selectedParcel.mirror_result?.mirror_score >= 85 ? 'text-emerald-400' :
                    selectedParcel.mirror_result?.mirror_score >= 70 ? 'text-amber-400' : 'text-rose-400'
                  }`}>
                    {selectedParcel.mirror_result?.mirror_score} / 100
                  </div>
                </div>
              </div>
              {}
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                  <span className="flex items-center gap-1.5">
                    <Database className="w-4 h-4 text-emerald-400" />
                    Mirror Engine Reconciliation (Ground vs. Register)
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">Tolerance: 10%</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                    <div className="text-slate-400">Textual RoR Stated Extent</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      {selectedParcel.area_textual} {selectedParcel.area_unit}
                      <span className="text-[10px] text-slate-400 block">≈ {selectedParcel.area_ha_textual} Hectares</span>
                    </div>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded border border-slate-800">
                    <div className="text-slate-400">Computed GeoJSON Extent</div>
                    <div className="font-semibold text-slate-200 mt-0.5">
                      {selectedParcel.mirror_result?.computed_area_ha} Ha
                      <span className="text-[10px] text-slate-400 block">Shoelace polygon area</span>
                    </div>
                  </div>
                </div>
                {selectedParcel.mirror_result?.area_discrepancy_pct && (
                  <div className="text-xs text-amber-300 bg-amber-950/40 border border-amber-800/50 p-2 rounded flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                    <span>Discrepancy: <strong>{selectedParcel.mirror_result.area_discrepancy_pct}%</strong> variance between survey deed and spatial polygon.</span>
                  </div>
                )}
              </div>
              {}
              <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-3">
                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                  <span>Record-of-Rights (RoR) Entry</span>
                  <span className="text-slate-400 italic text-[10px]">[OCR-simulated input for prototype scope]</span>
                </div>
                <div className="font-mono text-xs text-slate-300 bg-slate-900/90 p-2 rounded border border-slate-800">
                  {selectedParcel.ror_text}
                </div>
              </div>
              {}
              {selectedParcel.mirror_result?.flags?.length > 0 ? (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    Detected Risk Flags:
                  </div>
                  <div className="space-y-1">
                    {selectedParcel.mirror_result.flags.map((flag, i) => (
                      <div key={i} className="text-xs bg-rose-950/30 border border-rose-800/40 text-rose-300 px-2.5 py-1.5 rounded flex items-center justify-between">
                        <span>{flag}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-xs bg-emerald-950/30 border border-emerald-800/40 text-emerald-300 px-3 py-2 rounded flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>No discrepancies detected. Ready for cryptographic sealing on Curtain Ledger.</span>
                </div>
              )}
              {}
              {selectedParcel.schema_type !== 'community' && (
                <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-cyan-300">
                    <span className="flex items-center gap-1.5">
                      <DollarSign className="w-4 h-4" />
                      Risk-Indexed Assurance Pool Premium
                    </span>
                    <span className="text-[10px] text-slate-400">Torrens Insurance Principle</span>
                  </div>
                  <div className="bg-slate-900 p-2.5 rounded border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1">
                    <div className="text-cyan-400 font-bold">premium = base_rate × declared_value × (1 + k × (threshold − mirror_score))</div>
                    <div className="text-slate-400 text-[10px]">
                      base_rate = 0.1% | k = 0.05 | threshold = 85 | score = {selectedParcel.mirror_result?.mirror_score}
                    </div>
                    <div className="text-slate-200 pt-1 border-t border-slate-800">
                      Calculated Premium: <strong className="text-emerald-400">
                        ₹{(
                          (selectedParcel.declared_value_inr || 1000000) *
                          0.001 *
                          Math.max(0, 1 + 0.05 * (85 - (selectedParcel.mirror_result?.mirror_score || 85)))
                        ).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                      </strong> (on declared ₹{(selectedParcel.declared_value_inr || 1000000).toLocaleString()})
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-400 italic">
                    {t.prototypeDisclaimer}
                  </div>
                </div>
              )}
              {}
              <div className="pt-2">
                {selectedParcel.schema_type === 'community' ? (
                  <div className="bg-purple-950/40 border border-purple-800 text-purple-300 p-3 rounded-lg text-xs space-y-1">
                    <div className="font-semibold text-purple-200">Community-Governed (FRA) — CommunityTenure.sol</div>
                    <div className="text-purple-400/80">Collectively owned under the Forest Rights Act — governed via Gram Sabha multi-sig quorum in the <strong>Community Tenure</strong> tab. Not subject to individual Mirror Engine reconciliation (no individual purchase deeds or 7/12 mutation records apply to FRA collective title).</div>
                  </div>
                ) : currentAuth && currentAuth.role !== 'registrar' ? (
                  <div className="space-y-2">
                    <div className="text-[11px] text-amber-300 bg-amber-950/50 p-2.5 rounded-lg border border-amber-800/60 flex items-start gap-2">
                      <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <strong>Sub-Registrar authorization required:</strong> Currently authenticated as {currentAuth.displayName || currentAuth.role}. Only Sub-Registrars can seal parcels on CurtainLedger.sol.
                      </div>
                    </div>
                    <button
                      onClick={async () => {
                        const res = await fetch(`${apiBase}/auth/login`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ role: 'registrar' }),
                        });
                        const data = await res.json();
                        if (data.access_token) {
                          onAuthChange?.({
                            token: data.access_token,
                            role: data.role,
                            username: data.username,
                            displayName: data.display_name,
                            designation: data.designation,
                            jurisdiction: data.jurisdiction,
                          });
                        }
                      }}
                      className="w-full py-2 px-3 rounded-lg font-semibold text-xs transition bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-2 shadow"
                    >
                      <Key className="w-3.5 h-3.5" />
                      Authenticate as Sub-Registrar to Seal
                    </button>
                  </div>
                ) : (
                  <button
                    disabled={!selectedParcel.mirror_result?.sealing_eligible || sealingLoading}
                    onClick={() => handleSeal(selectedParcel.ulpin, selectedParcel.declared_value_inr)}
                    className={`w-full py-2.5 px-4 rounded-lg font-semibold text-xs transition flex items-center justify-center gap-2 ${
                      selectedParcel.mirror_result?.sealing_eligible
                        ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                    }`}
                  >
                    <Lock className="w-4 h-4" />
                    {sealingLoading ? 'Sealing on Ledger...' : selectedParcel.mirror_result?.sealing_eligible ? 'Seal on Curtain Ledger & Pay Assurance Premium' : 'Sealing Ineligible (Score < 85 Threshold)'}
                  </button>
                )}

              </div>
              {}
              {sealResult && (
                <div className={`p-3 rounded-lg text-xs border ${
                  sealResult.sealed
                    ? 'bg-emerald-950/40 border-emerald-600/50 text-emerald-300'
                    : 'bg-rose-950/40 border-rose-600/50 text-rose-300'
                }`}>
                  <div className="font-bold flex items-center gap-1.5">
                    {sealResult.sealed ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                    {sealResult.sealed ? 'Cryptographically Sealed on CurtainLedger.sol' : 'Sealing Rejected'}
                  </div>
                  <div className="mt-1 font-mono text-[11px]">{sealResult.reason || `Tx: ${sealResult.on_chain?.tx_hash || '0xSimulatedReceipt'}`}</div>
                  {sealResult.off_chain_cid && (
                    <div className="text-[10px] text-slate-400 mt-1">Off-Chain CID: {sealResult.off_chain_cid} [IPFS-equivalent store]</div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">Select a parcel from the list or map above to inspect</div>
          )}
        </div>
      </div>
      </>
      )}
    </div>
  );
}
