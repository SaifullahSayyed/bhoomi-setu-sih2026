import React, { useState } from 'react';
import { Search, Shield, CheckCircle, Clock, AlertCircle, Award, MapPin } from 'lucide-react';
import ParcelMap from '../components/ParcelMap';

export default function CitizenView({ lang, t, apiBase }) {
  const [searchUlpin, setSearchUlpin] = useState('UP231000000001');
  const [parcelData, setParcelData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
      {/* Search Bar */}
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

      {/* Parcel Information Card */}
      {parcelData && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
          {/* Status Header */}
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
            </div>
          </div>

          {/* Interactive GIS Boundary Map */}
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

          {/* Details Grid */}
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

          {/* Chain of Title Timeline */}
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

          {/* Title Assurance Protection Banner */}
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
        </div>
      )}
    </div>
  );
}
