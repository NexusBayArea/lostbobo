import { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings2, AlertTriangle, Plus, ChevronDown, ChevronUp } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

export interface Parameter {
  name: string;
  baseValue: number;
  unit: string;
  perturbable: boolean;
  min: number;
  max: number;
}

interface ConfigurationPanelProps {
  enabled: boolean;
  onEnabledChange: (enabled: boolean) => void;
  numRuns: number;
  onNumRunsChange: (n: number) => void;
  samplingMethod: string;
  onSamplingMethodChange: (m: string) => void;
  parameters: Parameter[];
  onParametersChange: (p: Parameter[]) => void;
  timeout: number;
  onTimeoutChange: (t: number) => void;
  seed?: number;
  onSeedChange: (s?: number) => void;
}

const samplingMethods = [
  '±10% Range (Random)',
  '±5% Range (Random)',
  '±20% Range (Random)',
  'Latin Hypercube',
];

export function ConfigurationPanel({
  enabled,
  onEnabledChange,
  numRuns,
  onNumRunsChange,
  samplingMethod,
  onSamplingMethodChange,
  parameters,
  onParametersChange,
  timeout,
  onTimeoutChange,
  seed,
  onSeedChange,
}: ConfigurationPanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const perturbableCount = parameters.filter((p) => p.perturbable).length;
  const estimatedTime = Math.ceil((numRuns * 45) / 60);

  const handleParameterToggle = (index: number) => {
    const updated = [...parameters];
    updated[index].perturbable = !updated[index].perturbable;
    onParametersChange(updated);
  };

  const handleParameterMinMaxChange = (index: number, field: 'min' | 'max', value: number) => {
    const updated = [...parameters];
    updated[index][field] = value;
    onParametersChange(updated);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'bg-slate-900 border-2 transition-colors rounded-2xl',
        enabled ? 'border-cyan-500/50' : 'border-slate-800'
      )}
    >
      {/* Header */}
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className={cn(
                'w-12 h-12 rounded-xl flex items-center justify-center transition-colors',
                enabled
                  ? 'bg-cyan-500 text-white'
                  : 'bg-slate-800 text-slate-500'
              )}
            >
              <Settings2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                Robustness Analysis
              </h2>
              <p className="text-sm text-slate-400">
                Enable parameter variation and sensitivity analysis
              </p>
            </div>
          </div>
          <Switch checked={enabled} onCheckedChange={onEnabledChange} />
        </div>
      </div>

      {enabled && (
        <div className="p-6 space-y-6">
          {/* Warning Banner */}
          <div className="flex items-start gap-3 p-4 bg-yellow-500/10 rounded-xl border border-yellow-500/20">
            <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-500">
                Computational Cost Awareness
              </p>
              <p className="text-sm text-slate-400">
                Robustness analysis spawns multiple simulation runs. Estimated time: ~{estimatedTime} minutes for {numRuns} runs.
              </p>
            </div>
          </div>

          {/* Basic Configuration */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Number of Runs */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-slate-300">
                  Number of Runs
                </label>
                <span className="px-3 py-1 bg-slate-800 rounded-full text-sm font-medium text-cyan-400 font-mono">
                  {numRuns}
                </span>
              </div>
              <Slider
                min={1}
                max={100}
                step={1}
                value={[numRuns]}
                onValueChange={(v) => onNumRunsChange(v[0])}
              />
              <p className="text-xs text-slate-500">
                Recommended: 10-20 runs for statistical significance
              </p>
            </div>

            {/* Sampling Method */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-slate-300">
                Sampling Method
              </label>
              <select
                value={samplingMethod}
                onChange={(e) => onSamplingMethodChange(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                {samplingMethods.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Parameters */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-300">
                Parameter Selection
              </label>
              <span className="px-3 py-1 bg-slate-800 rounded-full text-sm text-slate-400">
                {perturbableCount} of {parameters.length} selected
              </span>
            </div>

            <div className="bg-slate-800/50 rounded-xl overflow-hidden border border-slate-800">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Perturb</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Parameter</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 text-center">Base Value</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Min</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400">Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parameters.map((param, index) => (
                      <tr key={param.name} className="border-t border-slate-800">
                        <td className="px-4 py-3">
                          <Switch
                            checked={param.perturbable}
                            onCheckedChange={() => handleParameterToggle(index)}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <div>
                            <p className="text-sm font-medium text-white">{param.name}</p>
                            <p className="text-xs text-slate-500">{param.unit}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-cyan-400 font-mono text-center">
                          {param.baseValue}
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            value={param.min ?? ''}
                            onChange={(e) => handleParameterMinMaxChange(index, 'min', parseFloat(e.target.value))}
                            disabled={!param.perturbable}
                            className="w-20 px-2 py-1 text-sm bg-slate-800 border border-slate-700 rounded-lg text-white disabled:opacity-30"
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            value={param.max ?? ''}
                            onChange={(e) => handleParameterMinMaxChange(index, 'max', parseFloat(e.target.value))}
                            disabled={!param.perturbable}
                            className="w-20 px-2 py-1 text-sm bg-slate-800 border border-slate-700 rounded-lg text-white disabled:opacity-30"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-400 border border-slate-700 rounded-xl hover:bg-slate-800 transition-colors">
              <Plus className="w-4 h-4" />
              Add Parameter
            </button>
          </div>

          {/* Advanced Settings */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              Advanced Settings
            </button>

            {showAdvanced && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-4 grid md:grid-cols-2 gap-4 p-4 bg-slate-800/50 rounded-xl"
              >
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Convergence Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={timeout}
                    onChange={(e) => onTimeoutChange(parseInt(e.target.value) || 300)}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Random Seed (optional)
                  </label>
                  <input
                    type="number"
                    value={seed ?? ''}
                    onChange={(e) => onSeedChange(e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="Auto"
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white font-mono"
                  />
                </div>
              </motion.div>
            )}
          </div>
        </div>
      )}

      {!enabled && (
        <div className="p-6">
          <p className="text-sm text-slate-500">
            Enable robustness analysis to configure parameter perturbations and statistical sensitivity analysis.
            This feature is OFF by default to signal intentional design and computational cost awareness.
          </p>
        </div>
      )}
    </motion.div>
  );
}
