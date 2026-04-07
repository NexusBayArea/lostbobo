import { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings2, AlertTriangle, Plus, ChevronDown, ChevronUp } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

const SAMPLING_METHODS = [
  { value: '±5%', label: '±5% Perturbation' },
  { value: '±10%', label: '±10% Perturbation' },
  { value: 'latin_hypercube', label: 'Latin Hypercube' },
  { value: 'sobol', label: 'Sobol GSA (Enterprise)' },
];






export interface Parameter {
  name: string;
  baseValue: number;
  unit: string;
  perturbable: boolean;
  min?: number;
  max?: number;
}

interface ConfigurationPanelProps {
  enabled: boolean;
  onEnabledChange: (val: boolean) => void;
  numRuns: number;
  onNumRunsChange: (val: number) => void;
  samplingMethod: string;
  onSamplingMethodChange: (val: string) => void;
  parameters: Parameter[];
  onParametersChange: (val: Parameter[]) => void;
  timeout: number;
  onTimeoutChange: (val: number) => void;
  seed?: number;
  onSeedChange: (val: number | undefined) => void;
}

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
  onSeedChange
}: ConfigurationPanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const perturbableCount = parameters.filter((p) => p.perturbable).length;
  const estimatedTime = Math.ceil((numRuns * 45) / 60);

  const handleParameterToggle = (index: number) => {
    const updated = [...parameters];
    updated[index].perturbable = !updated[index].perturbable;
    onParametersChange(updated);
  };

  const handleParameterMinChange = (index: number, val: string) => {
    const updated = [...parameters];
    updated[index].min = val === '' ? undefined : parseFloat(val);
    onParametersChange(updated);
  };

  const handleParameterMaxChange = (index: number, val: string) => {
    const updated = [...parameters];
    updated[index].max = val === '' ? undefined : parseFloat(val);
    onParametersChange(updated);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'bg-white dark:bg-slate-800 rounded-2xl border-2 transition-colors',
        enabled ? 'border-blue-500' : 'border-slate-200 dark:border-slate-700'
      )}
    >
      {/* Header */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className={cn(
                'w-12 h-12 rounded-xl flex items-center justify-center transition-colors',
                enabled
                  ? 'bg-blue-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-500'
              )}
            >
              <Settings2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Robustness Analysis
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
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
          <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                Computational Cost Awareness
              </p>
              <p className="text-sm text-amber-700 dark:text-amber-400">
                Robustness analysis spawns multiple simulation runs. Estimated time: ~{estimatedTime} minutes for {numRuns} runs.
              </p>
            </div>
          </div>

          {/* Basic Configuration */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Number of Runs */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Number of Runs
                </label>
                <span className="px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-sm font-medium text-slate-700 dark:text-slate-300">
                  {numRuns}
                </span>
              </div>
              <Slider
                min={5}
                max={50}
                step={1}
                value={[numRuns]}
                onValueChange={(v) => onNumRunsChange(v[0])}
              />
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Recommended: 10-20 runs for statistical significance
              </p>
            </div>

            {/* Sampling Method */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Sampling Method
              </label>
              <select
                value={samplingMethod}
                onChange={(e) => onSamplingMethodChange(e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {SAMPLING_METHODS.map((method) => (
                  <option key={method.value} value={method.value}>
                    {method.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Parameters */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Parameter Selection
              </label>
              <span className="px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-sm text-slate-600 dark:text-slate-400">
                {perturbableCount} of {parameters.length} selected
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-slate-100 dark:bg-slate-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Perturb</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Parameter</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Base Value</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Min</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Max</th>
                  </tr>
                </thead>
                <tbody>
                  {parameters.map((param, index) => (
                    <tr key={param.name} className="border-t border-slate-200 dark:border-slate-700">
                      <td className="px-4 py-3">
                        <Switch
                          checked={param.perturbable}
                          onCheckedChange={() => handleParameterToggle(index)}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-sm font-medium text-slate-900 dark:text-white">{param.name}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">{param.unit}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">{param.baseValue}</td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={param.min || ''}
                          onChange={(e) => handleParameterMinChange(index, e.target.value)}
                          disabled={!param.perturbable}
                          className="w-20 px-2 py-1 text-sm bg-white dark:bg-slate-600 border border-slate-200 dark:border-slate-600 rounded-lg disabled:opacity-50"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={param.max || ''}
                          onChange={(e) => handleParameterMaxChange(index, e.target.value)}
                          disabled={!param.perturbable}
                          className="w-20 px-2 py-1 text-sm bg-white dark:bg-slate-600 border border-slate-200 dark:border-slate-600 rounded-lg disabled:opacity-50"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
              <Plus className="w-4 h-4" />
              Add Parameter
            </button>
          </div>

          {/* Advanced Settings */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              Advanced Settings
            </button>

            {showAdvanced && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-4 grid md:grid-cols-2 gap-4 p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl"
              >
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Convergence Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={timeout}
                    onChange={(e) => onTimeoutChange(parseInt(e.target.value))}
                    className="w-full px-4 py-3 bg-white dark:bg-slate-600 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Random Seed (optional)
                  </label>
                  <input
                    type="number"
                    placeholder="Auto"
                    value={seed || ''}
                    onChange={(e) => onSeedChange(e.target.value === '' ? undefined : parseInt(e.target.value))}
                    className="w-full px-4 py-3 bg-white dark:bg-slate-600 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white"
                  />
                </div>
              </motion.div>
            )}
          </div>
        </div>
      )}

      {!enabled && (
        <div className="p-6">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Enable robustness analysis to configure parameter perturbations and statistical sensitivity analysis.
            This feature is OFF by default to signal intentional design and computational cost awareness.
          </p>
        </div>
      )}
    </motion.div>
  );
}
