import { useState, useEffect } from "react";

// ─── Inline ThemeToggle ───────────────────────────────────────────────────────
function ThemeToggle({ variant = "default" }: { variant?: string }) {
  const [dark, setDark] = useState(() =>
    typeof document !== "undefined" && document.documentElement.classList.contains("dark")
  );
  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [dark]);
  return (
    <button
      onClick={() => setDark(d => !d)}
      className="w-9 h-9 flex items-center justify-center rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
      title={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      )}
    </button>
  );
}

// ─── Mock Data ────────────────────────────────────────────────────────────────
const MOCK_EXPERIMENTS = [
  {
    id: 482,
    title: "Fast Charge Limit Study (NMC811)",
    status: "completed",
    engine: "PyBaMM",
    question: "What is the fastest charge rate without lithium plating?",
    tags: ["battery", "fast-charge", "nmc811"],
    createdAt: "2026-03-05T09:12:00Z",
    completedAt: "2026-03-05T11:47:00Z",
    parameters: [
      { name: "Temperature", value: "298 K", changed: false },
      { name: "C-rate sweep", value: "1–5C", changed: false },
      { name: "Electrode thickness", value: "75 µm", changed: false },
      { name: "Electrolyte conductivity", value: "1.1 S/m", changed: false },
    ],
    runs: [
      { id: 1, label: "Run #1", param: "C-rate", value: "1C", result: "Stable", convergent: true, plotY: [0.92, 0.88, 0.85, 0.84, 0.83] },
      { id: 2, label: "Run #2", param: "C-rate", value: "2C", result: "Stable", convergent: true, plotY: [0.91, 0.86, 0.81, 0.79, 0.77] },
      { id: 3, label: "Run #3", param: "C-rate", value: "2.5C", result: "Marginal", convergent: true, plotY: [0.89, 0.83, 0.76, 0.71, 0.68] },
      { id: 4, label: "Run #4", param: "C-rate", value: "3C", result: "Plating", convergent: false, plotY: [0.87, 0.78, 0.69, 0.59, 0.44] },
    ],
    observations: [
      "Lithium plating begins between 2.6C and 2.8C.",
      "Voltage drop increases rapidly after 2.5C.",
      "Temperature sensitivity is higher at elevated C-rates.",
    ],
    conclusion: "Optimal charge rate: 2.6C. Above 2.8C, plating current exceeds safe threshold. Recommend conservative limit of 2.5C with 5% margin.",
    linkedIds: [475, 468, 451],
    metrics: { optimalRate: "2.6C", tempSensitivity: "+4%", energyDensity: "—", platingThreshold: "2.8C" },
  },
  {
    id: 475,
    title: "LFP Cost Study",
    status: "completed",
    engine: "PyBaMM",
    question: "What cell chemistry minimises cost per kWh below 100 Wh/kg?",
    tags: ["battery", "lfp", "cost"],
    createdAt: "2026-03-03T14:00:00Z",
    completedAt: "2026-03-03T16:22:00Z",
    parameters: [
      { name: "Chemistry", value: "LFP", changed: false },
      { name: "Capacity", value: "3.2 Ah", changed: false },
      { name: "Cycle target", value: "2000", changed: false },
    ],
    runs: [
      { id: 1, label: "Run #1", param: "Discharge rate", value: "0.5C", result: "Stable", convergent: true, plotY: [3.31, 3.30, 3.29, 3.28, 3.27] },
      { id: 2, label: "Run #2", param: "Discharge rate", value: "1C", result: "Stable", convergent: true, plotY: [3.29, 3.27, 3.25, 3.22, 3.19] },
    ],
    observations: ["LFP shows excellent cycle stability.", "Voltage plateau very flat — good for SoC estimation."],
    conclusion: "LFP viable for stationary storage at 88 Wh/kg. Cost target achieved.",
    linkedIds: [482, 468],
    metrics: { optimalRate: "1C", tempSensitivity: "+1.2%", energyDensity: "88 Wh/kg", platingThreshold: "N/A" },
  },
  {
    id: 468,
    title: "Battery Thermal Analysis",
    status: "completed",
    engine: "MFEM + SUNDIALS",
    question: "Does passive cooling sustain safe cell temperatures at 3C?",
    tags: ["thermal", "cooling", "mfem"],
    createdAt: "2026-02-28T10:00:00Z",
    completedAt: "2026-02-28T13:05:00Z",
    parameters: [
      { name: "C-rate", value: "3C", changed: false },
      { name: "Ambient temp", value: "298 K", changed: false },
      { name: "Cooling", value: "Passive", changed: false },
    ],
    runs: [
      { id: 1, label: "Run #1", param: "Cooling", value: "Passive", result: "Overheat", convergent: false, plotY: [299, 304, 312, 324, 341] },
      { id: 2, label: "Run #2", param: "Cooling", value: "Active (5 W)", result: "Marginal", convergent: true, plotY: [299, 302, 306, 309, 312] },
    ],
    observations: ["Passive cooling insufficient above 2.5C.", "Active cooling with 5 W maintains Tmax < 315 K."],
    conclusion: "Passive cooling inadequate at 3C. Recommend forced convection or liquid cooling for fast-charge applications.",
    linkedIds: [482, 451],
    metrics: { optimalRate: "2.5C", tempSensitivity: "+8%", energyDensity: "—", platingThreshold: "N/A" },
  },
  {
    id: 451,
    title: "Fast Charging Literature Review",
    status: "draft",
    engine: "—",
    question: "What does existing literature say about plating limits in NMC cells?",
    tags: ["literature", "nmc", "review"],
    createdAt: "2026-02-20T08:00:00Z",
    completedAt: null,
    parameters: [],
    runs: [],
    observations: ["Refs: Plett (2015), Doyle (1993), Safari (2011)."],
    conclusion: "",
    linkedIds: [482, 468],
    metrics: {},
  },
];

const TIMELINE = [
  { day: "Day 1", label: "Initial C-rate sweep", expId: 482 },
  { day: "Day 2", label: "Temperature variation", expId: 468 },
  { day: "Day 3", label: "Electrode thickness optimization", expId: 475 },
];

// ─── Micro sparkline SVG ──────────────────────────────────────────────────────
function Sparkline({ data, color = "#22d3ee", width = 80, height = 28 }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={pts.split(" ").pop().split(",")[0]} cy={pts.split(" ").pop().split(",")[1]} r="2.5" fill={color} />
    </svg>
  );
}

// ─── Status Badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    completed: { label: "Completed", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25" },
    running:   { label: "Running",   cls: "bg-cyan-500/15 text-cyan-400 border-cyan-500/25 animate-pulse" },
    draft:     { label: "Draft",     cls: "bg-slate-500/15 text-slate-400 border-slate-600/25" },
    failed:    { label: "Failed",    cls: "bg-red-500/15 text-red-400 border-red-500/25" },
  };
  const { label, cls } = map[status] || map.draft;
  return <span className={`text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded border ${cls}`}>{label}</span>;
}

// ─── Inline mini-bar chart for parameter runs ──────────────────────────────
function RunBar({ runs }: { runs: any[] }) {
  const maxLen = runs.length;
  return (
    <div className="flex flex-col gap-1 mt-2">
      {runs.map((r, i) => (
        <div key={r.id} className="flex items-center gap-2 text-[11px]">
          <span className="w-14 text-slate-500 shrink-0">{r.value}</span>
          <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${r.convergent ? "bg-cyan-500" : "bg-red-500"}`}
              style={{ width: `${((i + 1) / maxLen) * 100}%`, transitionDelay: `${i * 80}ms` }}
            />
          </div>
          <span className={`w-14 text-right shrink-0 ${r.convergent ? "text-slate-400" : "text-red-400"}`}>{r.result}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Comparison Panel ─────────────────────────────────────────────────────────
function ComparePanel({ expA, expB, onClose }: { expA: any, expB: any, onClose: () => void }) {
  if (!expA || !expB) return null;
  const keys = ["optimalRate", "tempSensitivity", "energyDensity", "platingThreshold"];
  const labels: Record<string, string> = { optimalRate: "Optimal Rate", tempSensitivity: "Temp Sensitivity", energyDensity: "Energy Density", platingThreshold: "Plating Threshold" };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-background border border-slate-700/60 rounded-2xl p-6 w-full max-w-xl shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-slate-900 dark:text-white font-semibold text-sm tracking-wide">Experiment Comparison</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900 dark:hover:text-white text-lg leading-none">×</button>
        </div>
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="text-slate-500 text-right font-medium">Metric</div>
          <div className="text-cyan-400 font-semibold text-center">#{expA.id}</div>
          <div className="text-indigo-400 font-semibold text-center">#{expB.id}</div>
          {keys.map(k => (
            <div key={k} className="contents">
              <div className="text-slate-400 text-right py-2 border-t border-slate-800">{labels[k]}</div>
              <div className="text-slate-900 dark:text-white text-center py-2 border-t border-slate-800">{expA.metrics[k] || "—"}</div>
              <div className="text-slate-900 dark:text-white text-center py-2 border-t border-slate-800">{expB.metrics[k] || "—"}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-500">
          <span className="text-slate-300 font-medium">Summary: </span>
          {expA.title} vs {expB.title}
        </div>
      </div>
    </div>
  );
}

// ─── Experiment Detail Panel ──────────────────────────────────────────────────
function DetailPanel({ exp, allExps, onClose, onCompare, onReplay }: { exp: any, allExps: any[], onClose: () => void, onCompare: (a: any, b: any) => void, onReplay: (e: any) => void }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [newObs, setNewObs] = useState("");
  const [observations, setObservations] = useState(exp.observations as string[]);
  const linked = allExps.filter(e => exp.linkedIds.includes(e.id));

  const tabs = ["overview", "runs", "observations", "timeline", "linked"];

  return (
    <div className="fixed inset-0 z-40 flex" onClick={onClose}>
      <div className="ml-auto w-full max-w-2xl h-full bg-background dark:bg-slate-900 border-l border-slate-800 flex flex-col shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-start justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-mono text-slate-500">EXP #{exp.id}</span>
              <StatusBadge status={exp.status} />
              <span className="text-[10px] text-slate-600 font-mono bg-slate-800/60 px-1.5 py-0.5 rounded">{exp.engine}</span>
            </div>
            <h2 className="text-slate-900 dark:text-white font-semibold text-base leading-snug">{exp.title}</h2>
            <p className="text-slate-600 dark:text-slate-400 text-xs mt-1 italic">"{exp.question}"</p>
          </div>
          <button onClick={onClose} className="text-slate-600 dark:text-slate-500 hover:text-slate-900 dark:hover:text-slate-300 ml-4 text-xl mt-0.5 leading-none shrink-0">×</button>
        </div>

        {/* Tabs */}
        <div className="flex gap-0 border-b border-slate-800 shrink-0 px-6">
          {tabs.map(t => (
            <button key={t} onClick={() => setActiveTab(t)}
              className={`py-3 px-3 text-[11px] font-medium uppercase tracking-wider border-b-2 transition-colors ${
                activeTab === t ? "border-cyan-500 text-cyan-600 dark:text-cyan-400" : "border-transparent text-slate-600 dark:text-slate-500 hover:text-slate-900 dark:hover:text-slate-300"
              }`}>
              {t}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 custom-scroll">

          {activeTab === "overview" && (
            <>
              {/* Parameters */}
              <section>
                <h4 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-3">Parameters</h4>
                <div className="grid grid-cols-2 gap-2">
                  {exp.parameters.map((p: any) => (
                    <div key={p.name} className="bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2">
                      <div className="text-[10px] text-slate-600 dark:text-slate-500">{p.name}</div>
                      <div className="text-slate-900 dark:text-white text-sm font-mono mt-0.5">{p.value}</div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Metrics */}
              {Object.keys(exp.metrics).length > 0 && (
                <section>
                  <h4 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-3">Key Outputs</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(exp.metrics).filter(([,v]) => v && v !== "—").map(([k, v]) => (
                      <div key={k} className="bg-cyan-500/5 border border-cyan-500/20 rounded-lg px-3 py-2">
                        <div className="text-[10px] text-cyan-600 capitalize">{k.replace(/([A-Z])/g, ' $1').trim()}</div>
                        <div className="text-cyan-300 text-sm font-mono font-semibold mt-0.5">{v as string}</div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Conclusion */}
              {exp.conclusion && (
                <section>
                  <h4 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">Conclusion</h4>
                  <p className="text-slate-300 text-xs leading-relaxed bg-slate-900/40 border border-slate-800 rounded-lg px-4 py-3">
                    {exp.conclusion}
                  </p>
                </section>
              )}
            </>
          )}

          {activeTab === "runs" && (
            <section>
              <h4 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-3">Parameter Variation Tracking</h4>
              {exp.runs.length === 0 ? (
                <p className="text-slate-600 text-xs italic">No runs recorded.</p>
              ) : (
                <div className="space-y-3">
                  {exp.runs.map((r: any) => (
                    <div key={r.id} className={`border rounded-xl px-4 py-3 flex items-center gap-4 ${r.convergent ? "border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-900/40" : "border-red-200 dark:border-red-900/40 bg-red-50 dark:bg-red-950/10"}`}>
                      <div className="shrink-0">
                        <div className="text-[10px] text-slate-600 dark:text-slate-500 font-mono">{r.label}</div>
                        <div className="text-slate-900 dark:text-white text-sm font-mono font-semibold">{r.value}</div>
                        <div className={`text-[10px] mt-0.5 ${r.convergent ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}>{r.result}</div>
                      </div>
                      <div className="flex-1">
                        <div className="text-[10px] text-slate-600 mb-1">Voltage curve</div>
                        <Sparkline data={r.plotY} color={r.convergent ? "#22d3ee" : "#f87171"} width={120} height={30} />
                      </div>
                    </div>
                  ))}
                  <div className="mt-3">
                    <div className="text-[10px] text-slate-500 mb-2 uppercase tracking-widest">Parameter sweep</div>
                    <RunBar runs={exp.runs} />
                  </div>
                </div>
              )}
            </section>
          )}

          {activeTab === "observations" && (
            <section>
              <h4 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-3">Observations</h4>
              <div className="space-y-2 mb-4">
                {observations.map((obs, i) => (
                  <div key={i} className="flex gap-2 items-start">
                    <span className="text-cyan-600 dark:text-cyan-400 mt-0.5 shrink-0">◆</span>
                    <p className="text-slate-700 dark:text-slate-300 text-xs leading-relaxed">{obs}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-2 mt-3">
                <input
                  className="flex-1 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:border-cyan-600"
                  placeholder="Add an observation…"
                  value={newObs}
                  onChange={e => setNewObs(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === "Enter" && newObs.trim()) {
                      setObservations(o => [...o, newObs.trim()]);
                      setNewObs("");
                    }
                  }}
                />
                <button
                  onClick={() => { if (newObs.trim()) { setObservations(o => [...o, newObs.trim()]); setNewObs(""); }}}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white dark:text-slate-900 text-xs px-3 py-2 rounded-lg font-medium transition-colors">
                  Add
                </button>
              </div>
            </section>
          )}

          {activeTab === "timeline" && (
            <section>
              <h4 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-3">Experiment Timeline</h4>
              <div className="relative pl-4">
                <div className="absolute left-0 top-0 bottom-0 w-px bg-slate-300 dark:bg-slate-800" />
                {TIMELINE.map((t, i) => (
                  <div key={i} className="relative mb-5 pl-5">
                    <div className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-cyan-500 bg-background dark:bg-slate-900" />
                    <div className="text-[10px] text-slate-600 dark:text-slate-500 font-mono">{t.day}</div>
                    <div className={`text-xs mt-0.5 font-medium ${t.expId === exp.id ? "text-cyan-600 dark:text-cyan-400" : "text-slate-700 dark:text-slate-300"}`}>{t.label}</div>
                    {t.expId === exp.id && <div className="text-[10px] text-cyan-600 dark:text-cyan-400 mt-0.5">← current</div>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {activeTab === "linked" && (
            <section>
              <h4 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-3">Related Experiments</h4>
              <div className="space-y-2">
                {linked.map(e => (
                  <div key={e.id} className="border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 bg-slate-100/50 dark:bg-slate-900/40 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-mono text-slate-600 dark:text-slate-500">#{e.id}</span>
                      <div className="text-slate-900 dark:text-white text-xs font-medium mt-0.5">{e.title}</div>
                      <div className="flex gap-1 mt-1">
                        {e.tags.slice(0, 2).map(t => (
                          <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400">{t}</span>
                        ))}
                      </div>
                    </div>
                    <button onClick={() => onCompare(exp, e)}
                      className="text-[10px] text-cyan-400 border border-cyan-800/50 px-2 py-1 rounded-lg hover:bg-cyan-500/10 transition-colors">
                      Compare
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-800 flex gap-2 shrink-0">
          <button onClick={() => onReplay(exp)}
            className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-4 py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M1 4v6h6M23 20v-6h-6"/>
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
            </svg>
            Replay
          </button>
          <button onClick={() => onCompare(exp, null)}
            className="flex-1 bg-indigo-900/40 hover:bg-indigo-900/60 text-indigo-300 text-xs font-medium px-4 py-2.5 rounded-xl border border-indigo-800/40 transition-colors flex items-center justify-center gap-2">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/>
              <polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/>
            </svg>
            Compare
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Search bar ───────────────────────────────────────────────────────────────
function SearchBar({ value, onChange }: { value: string, onChange: (v: string) => void }) {
  return (
    <div className="relative">
      <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        className="w-full bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-900 dark:text-white placeholder-slate-600 focus:outline-none focus:border-cyan-700 transition-colors"
        placeholder='Search experiments… e.g. "lithium plating above 2C"'
        value={value}
        onChange={e => onChange(e.target.value)}
      />
    </div>
  );
}

// ─── Experiment Card ──────────────────────────────────────────────────────────
function ExperimentCard({ exp, onClick }: { exp: any, onClick: () => void }) {
  return (
    <button onClick={onClick} className="w-full text-left group">
      <div className="border border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-600 rounded-2xl p-4 bg-slate-100/50 dark:bg-slate-900/30 hover:bg-slate-200/50 dark:hover:bg-slate-900/60 transition-all duration-200">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-slate-500">#{exp.id}</span>
            <StatusBadge status={exp.status} />
          </div>
          <span className="text-[10px] text-slate-600 font-mono">{exp.engine}</span>
        </div>
        <h3 className="text-slate-900 dark:text-white text-sm font-medium leading-snug mb-1 group-hover:text-cyan-600 dark:group-hover:text-cyan-200 transition-colors">{exp.title}</h3>
        <p className="text-slate-600 dark:text-slate-500 text-[11px] italic line-clamp-1 mb-3">"{exp.question}"</p>

        <div className="flex items-end justify-between">
          <div className="flex gap-1 flex-wrap">
            {exp.tags.map((t: string) => (
              <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800/80 text-slate-600 dark:text-slate-500">{t}</span>
            ))}
          </div>
          {exp.runs.length > 0 && (
            <Sparkline
              data={exp.runs[Math.floor(exp.runs.length / 2)]?.plotY}
              color={exp.status === "completed" ? "#22d3ee" : "#64748b"}
              width={60}
              height={20}
            />
          )}
        </div>

        {exp.runs.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center gap-3 text-[10px] text-slate-600">
            <span>{exp.runs.length} runs</span>
            <span>·</span>
            <span>{exp.runs.filter((r: any) => r.convergent).length} converged</span>
            <span>·</span>
            <span>{exp.linkedIds.length} linked</span>
          </div>
        )}
      </div>
    </button>
  );
}

// ─── Replay Toast ─────────────────────────────────────────────────────────────
function ReplayToast({ exp, onDismiss }: { exp: any, onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500);
    return () => clearTimeout(t);
  }, [onDismiss]);
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-slate-100 dark:bg-slate-900 border border-cyan-800/60 text-slate-900 dark:text-white text-xs px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-fade-in">
      <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
      <span>Replaying <strong>Experiment #{exp.id}</strong> — parameters & solver loaded</span>
      <button onClick={onDismiss} className="text-slate-600 dark:text-slate-500 hover:text-slate-900 dark:hover:text-white ml-2">×</button>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ExperimentNotebook() {
  console.log("ExperimentNotebook: Rendering...");
  const [experiments, setExperiments] = useState(MOCK_EXPERIMENTS);
  const [selected, setSelected] = useState<any>(null);
  const [compareA, setCompareA] = useState<any>(null);
  const [compareB, setCompareB] = useState<any>(null);
  const [showCompare, setShowCompare] = useState(false);
  const [search, setSearch] = useState("");
  const [replayExp, setReplayExp] = useState<any>(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    console.log("ExperimentNotebook: Mounted");
  }, []);

  const filtered = experiments.filter(e => {
    const q = search.toLowerCase();
    const matchSearch = !q || e.title.toLowerCase().includes(q) ||
      e.question.toLowerCase().includes(q) ||
      e.tags.some(t => t.includes(q)) ||
      e.observations.some(o => o.toLowerCase().includes(q));
    const matchFilter = filter === "all" || e.status === filter;
    return matchSearch && matchFilter;
  });

  const handleNewEntry = () => {
    console.log("ExperimentNotebook: Creating new entry");
    const newId = Math.floor(Math.random() * 1000) + 500;
    const newExp = {
      id: newId,
      title: "New Research Entry",
      status: "draft",
      engine: "—",
      question: "Click to define research objective...",
      tags: ["draft"],
      createdAt: new Date().toISOString(),
      completedAt: null,
      parameters: [],
      runs: [],
      observations: [],
      conclusion: "",
      linkedIds: [],
      metrics: {},
    };
    setExperiments([newExp, ...experiments]);
    setSelected(newExp);
  };

  const handleCompare = (a: any, b: any) => {
    setCompareA(a);
    if (b) { setCompareB(b); setShowCompare(true); }
    else {
      // pick next experiment for comparison
      const other = experiments.find(e => e.id !== a.id && e.status === "completed");
      if (other) { setCompareB(other); setShowCompare(true); }
    }
  };

  const handleReplay = (exp: any) => {
    setSelected(null);
    setReplayExp(exp);
  };

  const stats = {
    total: experiments.length,
    completed: experiments.filter(e => e.status === "completed").length,
    totalRuns: experiments.reduce((s, e) => s + e.runs.length, 0),
    converged: experiments.reduce((s, e) => s + e.runs.filter(r => r.convergent).length, 0),
  };

  return (
    <div className="min-h-screen bg-background text-slate-900 dark:text-white font-sans selection:bg-cyan-900/40">
      <style>{`
        * { font-family: 'DM Sans', sans-serif; }
        .font-mono, code { font-family: 'DM Mono', monospace; }
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-track { background: transparent; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
        .line-clamp-1 { display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
        @keyframes fade-in { from { opacity: 0; transform: translateX(-50%) translateY(8px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
        .animate-fade-in { animation: fade-in 0.3s ease; }
      `}</style>

      <div className="max-w-5xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-7 h-7 rounded-lg bg-cyan-500/15 border border-cyan-500/25 flex items-center justify-center">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" strokeWidth="1.8">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <h1 className="text-slate-900 dark:text-white font-semibold text-lg tracking-tight">Experiment Notebook</h1>
            </div>
            <p className="text-slate-600 dark:text-slate-500 text-xs">Auto-generated from every simulation run · persistent research workspace</p>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle variant="default" />
            <button
              onClick={handleNewEntry}
              className="bg-cyan-600 hover:bg-cyan-500 text-white dark:text-slate-900 text-xs font-medium px-4 py-2.5 rounded-xl transition-colors flex items-center gap-1.5 shadow-lg shadow-cyan-900/30"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              New Entry
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[
            { label: "Experiments", value: stats.total },
            { label: "Completed", value: stats.completed },
            { label: "Total Runs", value: stats.totalRuns },
            { label: "Converged", value: `${stats.converged}/${stats.totalRuns}` },
          ].map(s => (
            <div key={s.label} className="bg-slate-100/50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3">
              <div className="text-[10px] text-slate-600 dark:text-slate-500 uppercase tracking-widest">{s.label}</div>
              <div className="text-slate-900 dark:text-white font-semibold text-xl font-mono mt-0.5">{s.value}</div>
            </div>
          ))}
        </div>

        {/* Search & Filter */}
        <div className="flex gap-3 mb-5">
          <div className="flex-1">
            <SearchBar value={search} onChange={setSearch} />
          </div>
          <div className="flex gap-1.5">
            {["all", "completed", "draft"].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`text-[10px] uppercase tracking-widest px-3 py-2 rounded-xl font-medium transition-colors border ${
                  filter === f ? "bg-slate-200 dark:bg-slate-800 border-slate-400 dark:border-slate-600 text-slate-900 dark:text-white" : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-500 hover:text-slate-900 dark:hover:text-slate-300"
                }`}>
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Knowledge engine hint when searching */}
        {search && (
          <div className="mb-4 px-4 py-2.5 bg-indigo-900/20 border border-indigo-800/40 rounded-xl flex items-center gap-2">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <span className="text-indigo-300 text-xs">Searching across {experiments.length} experiments, {stats.totalRuns} runs, and all observations</span>
            <span className="ml-auto text-indigo-500 text-[10px] font-mono">{filtered.length} results</span>
          </div>
        )}

        {/* Experiment Grid */}
        <div className="grid grid-cols-2 gap-3 mb-8">
          {filtered.map(exp => (
            <ExperimentCard key={exp.id} exp={exp} onClick={() => setSelected(exp)} />
          ))}
          {filtered.length === 0 && (
            <div className="col-span-2 py-12 text-center text-slate-600 text-sm">
              No experiments match "{search}"
            </div>
          )}
        </div>

        {/* Timeline section */}
        <section className="border border-slate-200 dark:border-slate-800 rounded-2xl p-5 bg-slate-100/30 dark:bg-slate-900/20 mb-6">
          <h3 className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-4">Experiment Timeline</h3>
          <div className="flex items-center gap-0">
            {TIMELINE.map((t, i) => (
              <div key={i} className="flex items-center gap-0 flex-1">
                <div className="flex flex-col items-center">
                  <div className="w-3 h-3 rounded-full border-2 border-cyan-500 bg-background dark:bg-slate-900" />
                  <div className="text-[10px] text-slate-600 dark:text-slate-500 font-mono mt-1 whitespace-nowrap">{t.day}</div>
                  <div className="text-[11px] text-slate-700 dark:text-slate-300 mt-0.5 text-center max-w-24">{t.label}</div>
                </div>
                {i < TIMELINE.length - 1 && <div className="flex-1 h-px bg-slate-300 dark:bg-slate-800 mb-6" />}
              </div>
            ))}
          </div>
        </section>

        {/* Knowledge graph hint */}
        <div className="border border-slate-800/60 rounded-2xl p-5 bg-gradient-to-br from-indigo-950/20 to-transparent">
          <div className="flex items-center gap-2 mb-2">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="1.8">
              <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
            </svg>
            <span className="text-indigo-300 text-xs font-medium">Knowledge Graph</span>
          </div>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            {experiments.reduce((s, e) => s + e.linkedIds.length, 0)} experiment links across {experiments.length} entries.
            As experiments accumulate, this becomes a searchable knowledge engine for your team.
          </p>
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <DetailPanel
          exp={selected}
          allExps={experiments}
          onClose={() => setSelected(null)}
          onCompare={handleCompare}
          onReplay={handleReplay}
        />
      )}

      {/* Compare modal */}
      {showCompare && (
        <ComparePanel
          expA={compareA}
          expB={compareB}
          onClose={() => setShowCompare(false)}
        />
      )}

      {/* Replay toast */}
      {replayExp && (
        <ReplayToast exp={replayExp} onDismiss={() => setReplayExp(null)} />
      )}
    </div>
  );
}
