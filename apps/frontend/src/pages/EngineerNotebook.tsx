import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Navigation } from '@/components/Navigation';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/lib/supabase';
import {
  BookOpen, Save, Clock, AlertCircle, CheckCircle2, Search,
  Play, GitCompare, GitBranch, Calendar, Link, ChevronDown,
  ChevronRight, Plus, Trash2, ExternalLink, RotateCcw, BarChart3
} from 'lucide-react';

interface NotebookEntry {
  id: string;
  simulation_id: string | null;
  title: string;
  research_question: string;
  parameters: string;
  observations: string;
  conclusions: string;
  notes: string;
  linked_experiment_ids: string[];
  created_at: string;
  updated_at: string;
}

interface SimulationRecord {
  id: string;
  name: string;
  status: string;
  created_at: string;
  result_summary: any;
}

const defaultEntry = (): Omit<NotebookEntry, 'id' | 'created_at' | 'updated_at'> => ({
  simulation_id: null,
  title: '',
  research_question: '',
  parameters: '',
  observations: '',
  conclusions: '',
  notes: '',
  linked_experiment_ids: [],
});

export function EngineerNotebook() {
  const { user } = useAuth();
  const [entries, setEntries] = useState<NotebookEntry[]>([]);
  const [simulations, setSimulations] = useState<SimulationRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [compareMode, setCompareMode] = useState(false);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [status, setStatus] = useState<'saved' | 'saving' | 'error'>('saved');
  const [loaded, setLoaded] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!user?.id || !supabase) return;

    supabase
      .from('notebook_entries')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .then(({ data, error }) => {
        if (data) setEntries(data);
        setLoaded(true);
      });

    supabase
      .from('simulations')
      .select('id, name, status, created_at, result_summary')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(50)
      .then(({ data }) => {
        if (data) setSimulations(data);
      });
  }, [user?.id]);

  const selectedEntry = useMemo(
    () => entries.find(e => e.id === selectedId) || null,
    [entries, selectedId]
  );

  const filteredEntries = useMemo(() => {
    if (!searchQuery) return entries;
    const q = searchQuery.toLowerCase();
    return entries.filter(e =>
      e.title.toLowerCase().includes(q) ||
      e.research_question.toLowerCase().includes(q) ||
      e.observations.toLowerCase().includes(q) ||
      e.conclusions.toLowerCase().includes(q)
    );
  }, [entries, searchQuery]);

  const createEntry = () => {
    const newEntry = {
      ...defaultEntry(),
      title: `Experiment #${entries.length + 1}`,
    };
    setEntries(prev => [newEntry as NotebookEntry, ...prev]);
    setSelectedId(newEntry.title + Date.now());
  };

  const updateEntry = (field: keyof NotebookEntry, value: any) => {
    if (!selectedId) return;
    setEntries(prev =>
      prev.map(e => (e.id === selectedId ? { ...e, [field]: value } : e))
    );
  };

  const deleteEntry = (id: string) => {
    setEntries(prev => prev.filter(e => e.id !== id));
    if (selectedId === id) setSelectedId(null);
  };

  const linkSimulation = (simId: string) => {
    if (!selectedId) return;
    const entry = entries.find(e => e.id === selectedId);
    if (!entry) return;
    const linked = entry.linked_experiment_ids.includes(simId)
      ? entry.linked_experiment_ids.filter(id => id !== simId)
      : [...entry.linked_experiment_ids, simId];
    updateEntry('linked_experiment_ids', linked);
  };

  const replayExperiment = () => {
    if (!selectedEntry?.simulation_id) return;
    window.open(`/dashboard?replay=${selectedEntry.simulation_id}`, '_blank');
  };

  const toggleCompare = (id: string) => {
    setCompareIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id].slice(0, 2)
    );
  };

  const compareEntries = compareIds
    .map(id => entries.find(e => e.id === id))
    .filter(Boolean) as NotebookEntry[];

  useEffect(() => {
    if (!user?.id || !supabase || !loaded || entries.length === 0) return;

    setStatus('saving');
    const timeout = setTimeout(() => {
      const client = supabase;
      if (!client) return;

      Promise.all(
        entries.map(entry =>
          client.from('notebook_entries').upsert({
            id: entry.id,
            user_id: user.id,
            simulation_id: entry.simulation_id,
            title: entry.title,
            research_question: entry.research_question,
            parameters: entry.parameters,
            observations: entry.observations,
            conclusions: entry.conclusions,
            notes: entry.notes,
            linked_experiment_ids: entry.linked_experiment_ids,
            updated_at: new Date().toISOString(),
          }, { onConflict: 'id' })
        )
      ).then(results => {
        const hasError = results.some(r => r.error);
        setStatus(hasError ? 'error' : 'saved');
      });
    }, 1500);

    return () => clearTimeout(timeout);
  }, [entries, user?.id, loaded]);

  const statusIcon = status === 'saved' ? (
    <CheckCircle2 className="w-4 h-4 text-green-400" />
  ) : status === 'saving' ? (
    <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />
  ) : (
    <AlertCircle className="w-4 h-4 text-red-400" />
  );

  const Section = ({
    title,
    field,
    value,
    height = 'h-28',
    icon,
    placeholder,
  }: {
    title: string;
    field: keyof NotebookEntry;
    value: string;
    height?: string;
    icon?: React.ReactNode;
    placeholder?: string;
  }) => {
    const isExpanded = expandedSections[field] ?? true;
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden mb-4"
      >
        <button
          onClick={() => setExpandedSections(prev => ({ ...prev, [field]: !isExpanded }))}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            {icon}
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{title}</h3>
          </div>
          {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
        </button>
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <textarea
                value={value}
                onChange={(e) => updateEntry(field, e.target.value)}
                placeholder={placeholder}
                className={`w-full ${height} p-4 bg-slate-50 dark:bg-slate-800 border-0 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-cyan-500 resize-y font-mono text-sm leading-relaxed`}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-background dark:bg-slate-950">
      <Navigation />
      <div className="flex-1 pt-[72px] flex overflow-hidden">
        {/* Left Sidebar - Entry List */}
        <aside className="w-72 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-cyan-500" />
                <h2 className="font-semibold text-slate-900 dark:text-white">Experiments</h2>
              </div>
              <div className="flex items-center gap-1">
                {statusIcon}
              </div>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search experiments..."
                className="w-full pl-9 pr-3 py-2 bg-slate-100 dark:bg-slate-800 border-0 rounded-lg text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>
            <div className="flex gap-2 mt-3">
              <button
                onClick={createEntry}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-cyan-500 hover:bg-cyan-600 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" /> New
              </button>
              <button
                onClick={() => setCompareMode(!compareMode)}
                className={`flex items-center justify-center gap-1 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  compareMode
                    ? 'bg-cyan-500/10 text-cyan-500 border border-cyan-500/20'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                <GitCompare className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {filteredEntries.map((entry) => (
              <button
                key={entry.id}
                onClick={() => {
                  if (compareMode) {
                    toggleCompare(entry.id);
                  } else {
                    setSelectedId(entry.id);
                  }
                }}
                className={`w-full text-left px-4 py-3 border-b border-slate-100 dark:border-slate-800 transition-colors ${
                  selectedId === entry.id
                    ? 'bg-cyan-50 dark:bg-cyan-500/5 border-l-2 border-l-cyan-500'
                    : compareIds.includes(entry.id)
                    ? 'bg-purple-50 dark:bg-purple-500/5 border-l-2 border-l-purple-500'
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {entry.title}
                  </span>
                  {compareMode && (
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      compareIds.includes(entry.id)
                        ? 'border-purple-500 bg-purple-500'
                        : 'border-slate-300 dark:border-slate-600'
                    }`} />
                  )}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-slate-400">
                    {new Date(entry.created_at).toLocaleDateString()}
                  </span>
                  {entry.simulation_id && (
                    <span className="text-[10px] text-cyan-500 bg-cyan-50 dark:bg-cyan-500/10 px-1.5 py-0.5 rounded">
                      Linked
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto">
          {compareMode && compareEntries.length === 2 ? (
            <div className="p-6 max-w-6xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <GitCompare className="w-6 h-6 text-purple-500" />
                  Compare Experiments
                </h2>
                <button
                  onClick={() => { setCompareMode(false); setCompareIds([]); }}
                  className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                >
                  Exit Compare
                </button>
              </div>
              <div className="grid grid-cols-2 gap-6">
                {compareEntries.map((entry) => (
                  <div key={entry.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">{entry.title}</h3>
                    {[
                      { label: 'Research Question', value: entry.research_question },
                      { label: 'Parameters', value: entry.parameters },
                      { label: 'Observations', value: entry.observations },
                      { label: 'Conclusions', value: entry.conclusions },
                    ].map(({ label, value }) => (
                      <div key={label} className="mb-4">
                        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
                        <p className="text-sm text-slate-700 dark:text-slate-300 mt-1 font-mono whitespace-pre-wrap">{value || '—'}</p>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          ) : selectedEntry ? (
            <div className="p-6 max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={selectedEntry.title}
                    onChange={(e) => updateEntry('title', e.target.value)}
                    className="text-2xl font-bold bg-transparent border-0 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 rounded-lg px-2 py-1"
                  />
                </div>
                <div className="flex items-center gap-2">
                  {selectedEntry.simulation_id && (
                    <button
                      onClick={replayExperiment}
                      className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-500/10 rounded-lg hover:bg-cyan-100 dark:hover:bg-cyan-500/20 transition-colors"
                      title="Replay Experiment"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Replay
                    </button>
                  )}
                  <button
                    onClick={() => deleteEntry(selectedEntry.id)}
                    className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Linked Simulations */}
              <div className="mb-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Link className="w-4 h-4 text-slate-500" />
                  <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Link Simulation</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {simulations.map(sim => {
                    const isLinked = selectedEntry.linked_experiment_ids.includes(sim.id);
                    return (
                      <button
                        key={sim.id}
                        onClick={() => linkSimulation(sim.id)}
                        className={`px-3 py-1.5 text-xs font-mono rounded-lg transition-colors ${
                          isLinked
                            ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                        }`}
                      >
                        {sim.name || sim.id.slice(0, 8)}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Sections */}
              <Section
                title="Research Question"
                field="research_question"
                value={selectedEntry.research_question}
                height="h-24"
                icon={<span className="text-cyan-500 text-sm">?</span>}
                placeholder="What are you trying to discover or validate?"
              />
              <Section
                title="Parameters"
                field="parameters"
                value={selectedEntry.parameters}
                height="h-28"
                icon={<BarChart3 className="w-4 h-4 text-blue-500" />}
                placeholder="Temperature, C-rate, mesh resolution, solver settings..."
              />
              <Section
                title="Observations"
                field="observations"
                value={selectedEntry.observations}
                height="h-32"
                icon={<span className="text-amber-500 text-sm">!</span>}
                placeholder="Record convergence behavior, anomalies, thermal drift, pressure spikes..."
              />
              <Section
                title="Conclusions"
                field="conclusions"
                value={selectedEntry.conclusions}
                height="h-24"
                icon={<CheckCircle2 className="w-4 h-4 text-green-500" />}
                placeholder="What did you learn? What's the optimal configuration?"
              />
              <Section
                title="Freeform Notes"
                field="notes"
                value={selectedEntry.notes}
                height="h-40"
                icon={<BookOpen className="w-4 h-4 text-purple-500" />}
                placeholder="Additional thoughts, references, or scratch work..."
              />

              {/* Linked Experiments */}
              {selectedEntry.linked_experiment_ids.length > 0 && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 mb-4">
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch className="w-4 h-4 text-slate-500" />
                    <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Linked Experiments</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedEntry.linked_experiment_ids.map(simId => {
                      const sim = simulations.find(s => s.id === simId);
                      return (
                        <span
                          key={simId}
                          className="px-3 py-1.5 text-xs font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg"
                        >
                          {sim?.name || simId.slice(0, 8)}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Timeline */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-4 h-4 text-slate-500" />
                  <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Experiment Timeline</h3>
                </div>
                <div className="space-y-2">
                  {entries.slice(0, 5).map((entry, i) => (
                    <div key={entry.id} className="flex items-center gap-3 text-sm">
                      <div className="w-2 h-2 rounded-full bg-cyan-500" />
                      <span className="text-slate-500 font-mono text-xs w-20">
                        {new Date(entry.created_at).toLocaleDateString()}
                      </span>
                      <span className="text-slate-700 dark:text-slate-300">{entry.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <BookOpen className="w-16 h-16 text-slate-300 dark:text-slate-700 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-500 dark:text-slate-400 mb-2">No Experiment Selected</h3>
                <p className="text-sm text-slate-400 dark:text-slate-500 mb-4">Create a new entry or select one from the sidebar</p>
                <button
                  onClick={createEntry}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  <Plus className="w-4 h-4" /> New Experiment
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
