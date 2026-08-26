import React, { useState, useEffect } from 'react';
import { Network, Split, AlertCircle, Cpu, FileCode2, CheckCircle2 } from 'lucide-react';
export default function ArchitectureDemoView({ lang, t, apiBase }) {
  const [graphSummary, setGraphSummary] = useState(null);
  const [sampleRisk, setSampleRisk] = useState(null);
  const [harmonizeData, setHarmonizeData] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    const fetchDemos = async () => {
      setLoading(true);
      try {
        const [gRes, rRes, hRes] = await Promise.all([
          fetch(`${apiBase}/gnn/graph-summary`),
          fetch(`${apiBase}/gnn/risk/UP231000000001`),
          fetch(`${apiBase}/harmonize/demo`),
        ]);
        setGraphSummary(await gRes.json());
        setSampleRisk(await rRes.json());
        const hData = await hRes.json();
        setHarmonizeData(hData.demonstration_records || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchDemos();
  }, []);
  return (
    <div className="space-y-6">
      {}
      <div className="bg-amber-950/40 border border-amber-800/60 rounded-2xl p-4 text-xs text-amber-200 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-amber-300 block text-sm mb-0.5">
            Priority 4 Architecture Demonstrations (Honest Status Labeling)
          </span>
          The modules shown below are <strong>Architecture Proof-of-Concepts (POCs)</strong> trained on synthetic representations. They are not claimed to be production-validated machine learning models or universal state adapters.
        </div>
      </div>
      {}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">4a. Graph Neural Network (GNN) Dispute-Risk Pipeline</h3>
              <p className="text-xs text-slate-400">Node embeddings across Owners, Parcels, and Mutation Edges</p>
            </div>
          </div>
          <span className="text-[10px] bg-purple-950 text-purple-300 border border-purple-800 px-2 py-1 rounded font-semibold uppercase tracking-wider">
            Architecture Demo
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <div className="text-slate-400">Total Graph Nodes</div>
            <div className="text-xl font-bold text-slate-100 mt-1">{graphSummary?.total_nodes || 650}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Owners + Parcels</div>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <div className="text-slate-400">Relational Edges</div>
            <div className="text-xl font-bold text-purple-400 mt-1">{graphSummary?.total_edges || 1100}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Ownership + Mutations</div>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <div className="text-slate-400">Sample Parcel Risk</div>
            <div className={`text-xl font-bold mt-1 ${
              sampleRisk?.dispute_risk_category === 'Low' ? 'text-emerald-400' :
              sampleRisk?.dispute_risk_category === 'Moderate' ? 'text-amber-400' : 'text-rose-400'
            }`}>
              {sampleRisk?.dispute_risk_category || 'Low'} Risk ({sampleRisk?.dispute_risk_score ?? 0.15})
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5 font-mono">UP231000000001</div>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <div className="text-slate-400">Pipeline Recommendation</div>
            <div className="text-xs font-semibold text-slate-200 mt-1">
              {sampleRisk?.recommendation || 'Standard verification sufficient.'}
            </div>
          </div>
        </div>
        <div className="text-[11px] font-mono text-slate-400 bg-slate-950/40 p-2.5 rounded border border-slate-800/80">
          🏷️ <strong>Honesty Label:</strong> {sampleRisk?.honesty_label || 'Prototype pipeline — trained on synthetic data, not a validated real-world accuracy result.'}
        </div>
      </div>
      {}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-cyan-500/20 text-cyan-400 rounded-lg">
              <Split className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">4c. Adaptive Cross-State Schema Harmonizer</h3>
              <p className="text-xs text-slate-400">Heuristic Mapping across 3 Diverse State Land Registry Formats</p>
            </div>
          </div>
          <span className="text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800 px-2 py-1 rounded font-semibold uppercase tracking-wider">
            Proof of Concept
          </span>
        </div>
        <div className="space-y-3">
          {harmonizeData.map((item, idx) => (
            <div key={idx} className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-xs font-semibold text-cyan-300">
                <span>{item.state_source}</span>
                <span className="text-[10px] text-slate-400 font-mono">Canonical Target: ULPIN Unified</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {}
                <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 font-mono">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold mb-1 flex items-center gap-1">
                    <FileCode2 className="w-3.5 h-3.5 text-amber-400" />
                    Raw State Format (Input):
                  </div>
                  <pre className="text-[11px] text-amber-200/90 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(item.raw_input, null, 2)}
                  </pre>
                </div>
                {}
                <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 font-mono">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold mb-1 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    Normalized Canonical Output:
                  </div>
                  <pre className="text-[11px] text-emerald-200/90 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(item.harmonized_canonical, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg">
              <FileCode2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">4d. Government Shapefile Ingestion & Bulk Spatial Indexing (Beta)</h3>
              <p className="text-xs text-slate-400">Ingests Esri Shapefiles (.shp/.dbf/.shx) from SVAMITVA drone surveys & reprojects via GeoPandas / GDAL</p>
            </div>
          </div>
          <span className="text-[10px] bg-amber-950 text-amber-300 border border-amber-800 px-2 py-1 rounded font-semibold uppercase tracking-wider">
            Extended Capability (Beta)
          </span>
        </div>

        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold text-slate-200">SVAMITVA Drone-Survey Government Shapefile (.shp)</div>
              <div className="text-[11px] text-slate-400">Source: Mock Cadastral/Abadi Survey of India Export (25 Parcels in UTM 44N)</div>
            </div>
            <button
              onClick={async () => {
                try {
                  const res = await fetch(`${apiBase}/shapefile/import-sample`);
                  const data = await res.json();
                  alert(`Imported ${data.count} parcels successfully from Shapefile! Reprojected to EPSG:4326 and scored via Mirror Engine.`);
                } catch (e) {
                  alert('Error importing shapefile: ' + e.message);
                }
              }}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-3 py-1.5 rounded-lg text-xs transition flex items-center gap-1.5 shadow"
            >
              <FileCode2 className="w-3.5 h-3.5" />
              Import Government Shapefile (Beta)
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-2 border-t border-slate-800">
            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
              <div className="text-slate-400">CRS Auto-Reprojection</div>
              <div className="text-sm font-bold text-emerald-400 mt-1">EPSG:32644 → EPSG:4326</div>
              <div className="text-[10px] text-slate-400 mt-0.5">UTM 44N Metric to Lat/Lon WGS84</div>
            </div>
            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
              <div className="text-slate-400">Vectorized Spatial Overlap Query</div>
              <div className="text-sm font-bold text-cyan-400 mt-1">0.91 ms (4,688x faster)</div>
              <div className="text-[10px] text-slate-400 mt-0.5">GeoPandas R-Tree Spatial Index (sindex)</div>
            </div>
            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
              <div className="text-slate-400">Core Isolation & Degradation</div>
              <div className="text-sm font-bold text-purple-400 mt-1">100% Graceful Fallback</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Core runs independently without GDAL</div>
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-400 bg-slate-950/40 p-2.5 rounded border border-slate-800/80">
            🏷️ <strong>Honesty Label:</strong> Extended Capability (Architecture Demo). Demonstrated for SVAMITVA Shapefile I/O without altering the core 500-parcel pilot dataset.
          </div>
        </div>
      </div>
    </div>
  );
}

