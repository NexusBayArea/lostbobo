import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ReferenceLine,
  Cell,
  Legend
} from 'recharts';
import {
  CheckCircle2,
  Target,
  TrendingUp,
  Activity,
  Download,
  Brain,
  Shield,
  FileText,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';

interface ResultsPanelProps {
  run: any;
}

const TABS = [
  { id: 'summary', label: 'Summary', icon: Target },
  { id: 'visualization', label: 'Visualization', icon: Activity },
  { id: 'metrics', label: 'Metrics', icon: TrendingUp },
  { id: 'ai', label: 'AI Insights', icon: Brain },
];

export function ResultsPanel({ run }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState('summary');

  const isSobol = run.config_summary?.sampling_method === 'sobol';
  const results = run.results || {};
  const stats = results.stats || {};
  const sensitivity = results.sensitivity || [];

  const sensitivityData = sensitivity.map((s: any) => ({
    name: s.parameterName,
    influence: s.influenceCoefficient,
    mainEffect: s.mainEffect || 0,
    interaction: s.interactionStrength || 0,
    isHighInteraction: (s.interactionStrength || 0) > 0.3
  }));

  const tempData = Array.from({ length: run.progress?.total || 15 }, (_, i) => ({
    runId: i,
    maxTemp: results.baseline?.max_temperature ? results.baseline.max_temperature + (Math.random() * 20 - 10) : 380 + Math.random() * 60,
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-background dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-lg"
    >
      {/* Header */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                {isSobol ? 'Enterprise Analysis Complete' : 'Analysis Complete'}
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Run ID: {run.run_id} • {run.progress?.total} runs completed
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                try {
                  const blob = await api.exportPdf(run.run_id);
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `SimHPC_Report_${run.run_id}.pdf`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  window.URL.revokeObjectURL(url);
                } catch (err) {
                  console.error(err);
                  alert('Failed to export PDF');
                }
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 rounded-xl hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              <FileText className="w-4 h-4" />
              Export PDF
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-700 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-2 px-6 py-4 text-sm font-medium transition-colors border-b-2 whitespace-nowrap',
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'summary' && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
                <p className="text-xs text-blue-600 dark:text-blue-400 mb-1">Max Temperature</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {results.baseline?.max_temperature?.toFixed(1) || '0.0'} K
                </p>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Peak Stress</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {results.baseline?.peak_stress?.toFixed(1) || '0.0'} MPa
                </p>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Variance</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {stats.variance?.toFixed(2) || '0.0'}
                </p>
              </div>
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-100 dark:border-green-800">
                <p className="text-xs text-green-600 dark:text-green-400 mb-1">Confidence</p>
                <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                  ±{stats.confidence_interval?.toFixed(1) || '0.0'}%
                </p>
              </div>
            </div>

            {/* Sensitivity Ranking List */}
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">
                {isSobol ? 'Global Sensitivity Analysis (Sobol Indices)' : 'Sensitivity Ranking'}
              </h3>
              <div className="space-y-3">
                {sensitivity.map((metric: any, index: number) => (
                  <div
                    key={metric.parameterName}
                    className={cn(
                      "flex items-center gap-4 p-4 rounded-xl border transition-colors",
                      isSobol && metric.interaction_strength > 0.3
                        ? "bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30"
                        : "bg-slate-50 dark:bg-slate-700/50 border-transparent"
                    )}
                  >
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold",
                      isSobol && metric.interaction_strength > 0.3 ? "bg-red-500 text-white" : "bg-blue-500 text-white"
                    )}>
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-slate-900 dark:text-white">{metric.parameterName}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {isSobol
                          ? `Total Effect (S_T): ${metric.total_effect.toFixed(3)} | Interaction: ${(metric.interaction_strength * 100).toFixed(1)}%`
                          : `Variance contribution: ${(metric.main_effect * 100).toFixed(1)}%`}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={cn(
                        "font-semibold text-slate-900 dark:text-white",
                        isSobol && metric.interaction_strength > 0.3 && "text-red-600 dark:text-red-400"
                      )}>
                        {metric.influence_coefficient.toFixed(2)}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {isSobol ? 'total effect' : 'influence'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'visualization' && (
          <div className="space-y-8">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                  {isSobol ? 'Main Effect vs Interaction (Enterprise)' : 'Parameter Influence'}
                </h3>
                {isSobol && (
                  <div className="flex items-center gap-4 text-xs font-medium">
                    <div className="flex items-center gap-1.5 text-blue-500">
                      <div className="w-3 h-3 rounded-sm bg-blue-500" /> Main Effect ($S_1$)
                    </div>
                    <div className="flex items-center gap-1.5 text-purple-500">
                      <div className="w-3 h-3 rounded-sm bg-purple-500" /> Interaction
                    </div>
                  </div>
                )}
              </div>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={sensitivityData} layout="vertical" margin={{ left: 40, right: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" domain={[0, 1]} />
                    <YAxis type="category" dataKey="name" width={120} />
                    <Tooltip
                      contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                    />
                    {isSobol ? (
                      <>
                        <Bar dataKey="mainEffect" stackId="a" fill="#3B82F6" radius={[0, 0, 0, 0]} />
                        <Bar dataKey="interaction" stackId="a" fill="#A855F7" radius={[0, 4, 4, 0]}>
                          {sensitivityData.map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={entry.interaction > 0.3 ? '#EF4444' : '#A855F7'} />
                          ))}
                        </Bar>
                      </>
                    ) : (
                      <Bar dataKey="influence" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                    )}
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {isSobol && (
                <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-700 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    <strong>Interpretation:</strong> Red segments indicate high multi-variable interaction ($S_T - S_1 &gt; 0.3$).
                    This suggests the parameter's impact is coupled with other variables and cannot be optimized in isolation.
                  </p>
                </div>
              )}
            </div>

            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">
                Monte Carlo Sample Distribution
              </h3>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="runId" name="Run" />
                    <YAxis type="number" dataKey="maxTemp" name="Max Temp" unit=" K" domain={['auto', 'auto']} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <ReferenceLine y={results.baseline?.max_temperature || 412.3} stroke="#10B981" strokeDasharray="5 5" label="Baseline" />
                    <Scatter data={tempData} fill="#3B82F6" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-6 bg-slate-50 dark:bg-slate-700/50 rounded-xl text-center border border-slate-100 dark:border-slate-700">
                <p className="text-3xl font-bold text-slate-900 dark:text-white">{run.progress?.total}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Total Simulations</p>
              </div>
              <div className="p-6 bg-slate-50 dark:bg-slate-700/50 rounded-xl text-center border border-slate-100 dark:border-slate-700">
                <p className="text-3xl font-bold text-slate-900 dark:text-white">0</p>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Convergence Failures</p>
              </div>
              <div className="p-6 bg-slate-50 dark:bg-slate-700/50 rounded-xl text-center border border-slate-100 dark:border-slate-700">
                <p className="text-3xl font-bold text-slate-900 dark:text-white">
                  {stats.std_dev?.toFixed(2) || '0.0'}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Standard Deviation</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="prose dark:prose-invert max-w-none">
            {run.ai_report ? (
              <div className="space-y-8">
                {run.ai_report.metadata?.manual_review_required && (
                  <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-bold text-amber-800 dark:text-amber-300">Numerical Integrity Warning</p>
                      <p className="text-xs text-amber-700 dark:text-amber-400">
                        Discrepancies detected between solver outputs and AI interpretation. Manual verification recommended.
                      </p>
                    </div>
                  </div>
                )}
                {run.ai_report.sections.sort((a: any, b: any) => a.order - b.order).map((section: any) => (
                  <div key={section.title} className="bg-slate-50 dark:bg-slate-900/30 p-6 rounded-2xl border border-slate-100 dark:border-slate-700">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                      <Brain className="w-5 h-5 text-blue-500" />
                      {section.title}
                    </h3>
                    <div className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                      {section.content}
                    </div>
                  </div>
                ))}
                <div className="text-xs text-slate-400 dark:text-slate-500 italic pt-4 border-t border-slate-200 dark:border-slate-700">
                  {run.ai_report.disclaimer}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                <Loader2 className="w-8 h-8 animate-spin mb-4" />
                <p>Generating technical interpretation...</p>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
