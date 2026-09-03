import React, { useState } from 'react';
import { Search, Shield, CheckCircle, Clock, AlertCircle, Award, MapPin, Download, FileWarning, Send, Check, GitPullRequest } from 'lucide-react';
import ParcelMap from '../components/ParcelMap';
export default function CitizenView({ lang, t, apiBase, currentAuth, onAuthChange }) {
  const [searchUlpin, setSearchUlpin] = useState('UP231000000001');
  const [parcelData, setParcelData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Dispute Filing state
  const [showDisputeForm, setShowDisputeForm] = useState(false);
  const [disputeType, setDisputeType] = useState('boundary_overlap');
  const [disputeDesc, setDisputeDesc] = useState('');
  const [complainantName, setComplainantName] = useState('');
  const [disputeSubmitting, setDisputeSubmitting] = useState(false);
  const [disputeResult, setDisputeResult] = useState(null);
  const [disputeError, setDisputeError] = useState(null);

  // Tier 3a Mutation Request state
  const [showMutationForm, setShowMutationForm] = useState(false);
  const [mutationType, setMutationType] = useState('sale');
  const [newOwnerName, setNewOwnerName] = useState('');
  const [declaredValue, setDeclaredValue] = useState('1500000');
  const [deedRef, setDeedRef] = useState('');
  const [proposedArea, setProposedArea] = useState('');
  const [mutationSubmitting, setMutationSubmitting] = useState(false);
  const [mutationResult, setMutationResult] = useState(null);
  const [mutationError, setMutationError] = useState(null);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!searchUlpin) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/parcels/${searchUlpin.trim()}`);
      if (!res.ok) throw new Error('Parcel not found. Check the 14-digit ULPIN.');
      const data = await res.json();
      setParcelData(data);
    } catch (err) {
      setError(err.message);
      setParcelData(null);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl text-center space-y-4">
        <h2 className="text-xl font-bold text-slate-100 flex items-center justify-center gap-2">
          <Shield className="w-6 h-6 text-emerald-400" />
          {t.citizenView} — Verify Title Certainty
        </h2>
        <p className="text-xs text-slate-400 max-w-xl mx-auto">
          Enter your 14-digit Unique Land Parcel Identification Number (ULPIN) to view verified ownership status, cadastral boundary alignment on the GIS map, and title assurance coverage.
        </p>
        <form onSubmit={handleSearch} className="flex gap-2 max-w-lg mx-auto">
          <input
            type="text"
            value={searchUlpin}
            onChange={(e) => setSearchUlpin(e.target.value)}
            placeholder="e.g. UP231000000001 or TN042000000001"
            className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm font-mono text-slate-100 focus:outline-none focus:border-emerald-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-5 py-2.5 rounded-xl transition flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            {loading ? 'Searching...' : 'Check Status'}
          </button>
        </form>
        <div className="flex justify-center gap-2 text-[11px] text-slate-400">
          <span>Try quick sample:</span>
          <button onClick={() => { setSearchUlpin('UP231000000001'); }} className="text-emerald-400 hover:underline font-mono">UP231000000001</button>
          <span>•</span>
          <button onClick={() => { setSearchUlpin('TN042000000001'); }} className="text-emerald-400 hover:underline font-mono">TN042000000001</button>
          <span>•</span>
          <button onClick={() => { setSearchUlpin('JH117000000001'); }} className="text-purple-400 hover:underline font-mono">JH117000000001 (FRA Community)</button>
        </div>
      </div>
      {error && (
        <div className="bg-rose-950/40 border border-rose-800 text-rose-300 p-4 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          <span>{error}</span>
        </div>
      )}
      {}
      {parcelData && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
          {}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div className="text-xs text-slate-400">Parcel Identification</div>
              <div className="text-2xl font-bold font-mono text-slate-100">{parcelData.parcel.ulpin}</div>
              <div className="text-xs text-slate-400 mt-0.5">{parcelData.parcel.village}, {parcelData.parcel.district}, {parcelData.parcel.state}</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs text-slate-400">Torrens Confidence</div>
                <div className={`text-xl font-bold font-mono ${
                  parcelData.mirror_result?.mirror_score >= 85 ? 'text-emerald-400' :
                  parcelData.mirror_result?.mirror_score >= 70 ? 'text-amber-400' : 'text-rose-400'
                }`}>
                  {parcelData.mirror_result?.mirror_score} / 100
                </div>
              </div>
              <div className={`p-3 rounded-xl border flex items-center gap-2 ${
                parcelData.on_chain_state?.found
                  ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300'
                  : 'bg-amber-950/50 border-amber-500/40 text-amber-300'
              }`}>
                <Award className="w-5 h-5" />
                <span className="text-xs font-semibold">
                  {parcelData.on_chain_state?.found ? 'Sealed Title Certificate' : 'Presumptive Record'}
                </span>
              </div>

              {/* Tier 2a Download PDF Certificate Button */}
              {parcelData.on_chain_state?.found ? (
                <a
                  href={`${apiBase}/parcels/${parcelData.parcel.ulpin}/certificate`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow-md"
                  title="Download official Torrens Title Attestation Certificate (PDF)"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Title Certificate (PDF)</span>
                </a>
              ) : (
                <span
                  className="text-[11px] text-slate-500 italic bg-slate-900/80 px-3 py-2 rounded-xl border border-slate-800 hidden sm:inline-block"
                  title="Certificates are only issued for cryptographically sealed parcels"
                >
                  Certificate Unavailable (Unsealed)
                </span>
              )}
            </div>
          </div>
          {}
          {parcelData.parcel.geometry && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-emerald-400" />
                <span>Cadastral Boundary Survey (GeoJSON Polygon Layer)</span>
              </div>
              <ParcelMap
                parcels={[parcelData.parcel]}
                selectedParcel={parcelData.parcel}
                height="280px"
                villageName={parcelData.parcel.village}
              />
            </div>
          )}
          {}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">Primary Title Holder</div>
              <div className="text-sm font-semibold text-slate-100 mt-1">
                {parcelData.parcel.schema_type === 'community'
                  ? parcelData.parcel.community_entity
                  : parcelData.parcel.owners?.[0]?.name || 'Unknown'}
              </div>
              <div className="text-[10px] text-slate-400 font-mono mt-1 truncate">
                ID Hash: {parcelData.parcel.owners?.[0]?.id_hash?.substring(0, 16) || 'FRA-COMMUNITY'}...
              </div>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">Registered Land Extent</div>
              <div className="text-sm font-semibold text-slate-100 mt-1">
                {parcelData.parcel.area_textual} {parcelData.parcel.area_unit}
              </div>
              <div className="text-[10px] text-emerald-400 mt-1">
                Cadastral Match: {parcelData.mirror_result?.computed_area_ha} Ha (Polygon)
              </div>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400">Encumbrance & Liabilities</div>
              <div className="text-sm font-semibold text-slate-100 mt-1">
                {parcelData.parcel.encumbrance?.mortgaged ? (
                  <span className="text-rose-400">Mortgaged: ₹{parcelData.parcel.encumbrance.amount_inr?.toLocaleString()}</span>
                ) : (
                  <span className="text-emerald-400">Encumbrance-Free (निर्भार)</span>
                )}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                {parcelData.parcel.encumbrance?.creditor || 'No financial charge registered'}
              </div>
            </div>
          </div>
          {}
          {parcelData.parcel.mutation_history?.length > 0 && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-400" />
                Verified Title Chain (Mutation History)
              </div>
              <div className="space-y-2">
                {parcelData.parcel.mutation_history.map((m, idx) => (
                  <div key={idx} className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-slate-200 uppercase">{m.event_type.replace('_', ' ')}</span>
                      <span className="text-slate-400 ml-2">from {m.from_owner} → {m.to_owner}</span>
                      <p className="text-[11px] text-slate-400 mt-0.5">{m.remarks}</p>
                    </div>
                    <div className="text-[11px] font-mono text-slate-400">{m.date}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {}
          <div className="bg-emerald-950/30 border border-emerald-800/40 rounded-xl p-4 flex items-center justify-between text-xs text-emerald-300">
            <div>
              <div className="font-semibold flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Bhoomi Setu Assurance Coverage Active
              </div>
              <p className="text-[11px] text-emerald-400/80 mt-0.5">
                In the event of administrative error or cadastral mismatch, the self-funding Assurance Pool provides restorative backing.
              </p>
            </div>
            <span className="text-[10px] bg-emerald-900/60 border border-emerald-700 px-2 py-1 rounded text-emerald-200">
              Torrens Principle #3
            </span>
          </div>

          {/* Tier 2b Citizen Dispute / Grievance Redressal Section */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileWarning className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold text-slate-200">Land Title Grievance & Dispute Redressal</span>
                <span className="text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.5 rounded font-mono">
                  Off-Chain Queue
                </span>
              </div>
              <button
                onClick={() => {
                  setShowDisputeForm(!showDisputeForm);
                  setDisputeResult(null);
                }}
                className="text-xs text-amber-400 hover:text-amber-300 font-semibold underline underline-offset-2"
              >
                {showDisputeForm ? 'Cancel Filing' : 'File a Title Dispute'}
              </button>
            </div>

            {disputeResult && (
              <div className="p-3 bg-emerald-950/40 border border-emerald-600/50 rounded-lg text-xs space-y-1">
                <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                  <Check className="w-4 h-4" />
                  Grievance Filed Successfully — Tracking ID: {disputeResult.dispute_id}
                </div>
                <p className="text-[11px] text-slate-300">
                  Case assigned to <strong>{disputeResult.dispute?.assigned_to}</strong> for field inquiry and cadastral verification.
                </p>
              </div>
            )}

            {showDisputeForm && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (!disputeDesc) return;
                  setDisputeSubmitting(true);
                  try {
                    const res = await fetch(`${apiBase}/disputes/file`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        ulpin: parcelData.parcel.ulpin,
                        complainant_name: complainantName || currentAuth?.displayName || 'Citizen Landowner',
                        dispute_type: disputeType,
                        description: disputeDesc,
                      }),
                    });
                    const data = await res.json();
                    if (res.ok) {
                      setDisputeResult(data);
                      setDisputeDesc('');
                      setShowDisputeForm(false);
                    }
                  } catch (err) {
                    console.error('Failed to file dispute:', err);
                  } finally {
                    setDisputeSubmitting(false);
                  }
                }}
                className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-3 pt-3"
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Complainant Name</label>
                    <input
                      type="text"
                      placeholder={currentAuth?.displayName || "e.g. Ramesh Kumar"}
                      value={complainantName}
                      onChange={(e) => setComplainantName(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Dispute Category</label>
                    <select
                      value={disputeType}
                      onChange={(e) => setDisputeType(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                    >
                      <option value="boundary_overlap">Boundary Overlap / Encroachment</option>
                      <option value="inheritance_claim">Undivided Ancestral / Inheritance Claim</option>
                      <option value="fraudulent_mutation">Fraudulent or Unregistered Mutation</option>
                      <option value="area_discrepancy">Ground Area vs RoR Record Mismatch</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Detailed Grievance Description *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Describe the discrepancy, affected boundaries, or legal heir rights regarding this parcel..."
                    value={disputeDesc}
                    onChange={(e) => setDisputeDesc(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                  />
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[10px] text-slate-500">
                    🏷️ <strong>Honesty Label:</strong> Prototype grievance filing stored off-chain for administrative review.
                  </span>
                  <button
                    type="submit"
                    disabled={disputeSubmitting}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1.5 shadow"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {disputeSubmitting ? 'Filing Grievance...' : 'Submit Grievance'}
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Tier 3a Citizen Mutation Request Section */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GitPullRequest className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-slate-200">Citizen Land Mutation Application</span>
                <span className="text-[9px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.5 rounded font-mono">
                  Pending Review Queue
                </span>
              </div>
              <button
                onClick={() => {
                  setShowMutationForm(!showMutationForm);
                  setMutationResult(null);
                }}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold underline underline-offset-2"
              >
                {showMutationForm ? 'Cancel Application' : 'Apply for Title Mutation'}
              </button>
            </div>

            {mutationResult && (
              <div className="p-3 bg-emerald-950/40 border border-emerald-600/50 rounded-lg text-xs space-y-1">
                <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                  <Check className="w-4 h-4" />
                  Mutation Request Lodged — Tracking ID: {mutationResult.request_id}
                </div>
                <p className="text-[11px] text-slate-300">
                  Application forwarded to Sub-Registrar queue. Mirror Engine re-verification will execute prior to on-chain sealing.
                </p>
              </div>
            )}

            {mutationError && (
              <div className="p-3 bg-rose-950/40 border border-rose-600/50 rounded-lg text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{mutationError}</span>
              </div>
            )}

            {showMutationForm && (
              !currentAuth || (currentAuth.role !== 'citizen' && currentAuth.role !== 'registrar') ? (
                <div className="bg-slate-950/80 p-4 rounded-xl border border-cyan-800/60 space-y-3">
                  <div className="flex items-start gap-2 text-xs text-cyan-300">
                    <AlertCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <strong>Citizen Authentication Required:</strong> Only verified landowners can initiate title mutations.
                    </div>
                  </div>
                  <button
                    onClick={async () => {
                      const res = await fetch(`${apiBase}/auth/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ role: 'citizen' }),
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
                    className="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg transition shadow"
                  >
                    Authenticate as Citizen (Ramesh Kumar)
                  </button>
                </div>
              ) : (
                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    if (!newOwnerName || !deedRef) return;
                    setMutationSubmitting(true);
                    setMutationError(null);
                    try {
                      const headers = { 'Content-Type': 'application/json' };
                      if (currentAuth?.token) {
                        headers['Authorization'] = `Bearer ${currentAuth.token}`;
                      }
                      const dummyHash = Array.from(newOwnerName).reduce((acc, char) => (acc * 31 + char.charCodeAt(0)) >>> 0, 12345).toString(16).padStart(64, 'a');
                      const res = await fetch(`${apiBase}/mutation-requests/`, {
                        method: 'POST',
                        headers,
                        body: JSON.stringify({
                          ulpin: parcelData.parcel.ulpin,
                          applicant_name: currentAuth?.displayName || 'Ramesh Kumar',
                          mutation_type: mutationType,
                          new_owner_name: newOwnerName,
                          new_owner_id_hash: dummyHash,
                          declared_value_inr: parseFloat(declaredValue) || 1500000.0,
                          deed_reference: deedRef,
                          proposed_area_ha: proposedArea ? parseFloat(proposedArea) : null,
                        }),
                      });
                      const data = await res.json();
                      if (res.ok) {
                        setMutationResult(data);
                        setNewOwnerName('');
                        setDeedRef('');
                        setShowMutationForm(false);
                      } else {
                        setMutationError(data.detail || 'Failed to submit mutation application');
                      }
                    } catch (err) {
                      console.error('Failed to file mutation:', err);
                      setMutationError(err.message);
                    } finally {
                      setMutationSubmitting(false);
                    }
                  }}
                  className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-3 pt-3"
                >
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">Mutation Type</label>
                      <select
                        value={mutationType}
                        onChange={(e) => setMutationType(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                      >
                        <option value="sale">Sale Deed (बिक्री पत्र)</option>
                        <option value="gift">Gift Deed (दान पत्र)</option>
                        <option value="inheritance">Inheritance / Succession (वारिसाना)</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">New Transferee / Buyer Name *</label>
                      <input
                        required
                        type="text"
                        placeholder="e.g. Sunita Verma"
                        value={newOwnerName}
                        onChange={(e) => setNewOwnerName(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">Deed Registration Reference *</label>
                      <input
                        required
                        type="text"
                        placeholder="e.g. REG-SALE-2026/4102"
                        value={deedRef}
                        onChange={(e) => setDeedRef(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">Declared Value (INR) *</label>
                      <input
                        required
                        type="number"
                        placeholder="1500000"
                        value={declaredValue}
                        onChange={(e) => setDeclaredValue(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-500">
                      🏷️ <strong>Honesty Label:</strong> Queued off-chain. Mirror Engine scoring will re-verify before Curtain seal update.
                    </span>
                    <button
                      type="submit"
                      disabled={mutationSubmitting}
                      className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1.5 shadow"
                    >
                      <Send className="w-3.5 h-3.5" />
                      {mutationSubmitting ? 'Submitting...' : 'Submit Mutation Application'}
                    </button>
                  </div>
                </form>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
