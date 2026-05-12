import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Cpu, 
  Clock, 
  Play, 
  Search, 
  Plus,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { useExperiments } from '@/hooks/useExperiments';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export default function ExperimentNotebook() {
  const { experiments, loading, error, refresh } = useExperiments();
  const [searchTerm, setSearchTerm] = useState('');

  const filteredExperiments = experiments.filter(ex => 
    ex.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Experiment Notebook</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-2">
            Explore your memory fabric and review past simulation results.
          </p>
        </div>
        <Button onClick={refresh} variant="outline" size="sm">
          <RefreshCcw className="h-4 w-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Search & Actions */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search experiments..."
            className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" /> New Experiment
        </Button>
      </div>

      {/* Loading/Error states */}
      {loading && (
        <div className="flex items-center justify-center py-20 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin mr-3" /> Fetching experiments from memory fabric...
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 p-6 rounded-xl text-red-700 dark:text-red-300 flex items-center gap-3">
          <AlertCircle className="h-6 w-6" /> {error}
        </div>
      )}

      {/* Experiments Grid */}
      {!loading && !error && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredExperiments.map((ex) => (
            <motion.div
              key={ex.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg">
                  <FileText className="h-6 w-6" />
                </div>
                <Badge variant={ex.status === 'completed' ? 'default' : 'secondary'}>
                  {ex.status}
                </Badge>
              </div>
              <h3 className="font-semibold text-lg text-slate-900 dark:text-white mb-2">{ex.name}</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 line-clamp-2">{ex.description}</p>
              
              <div className="flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" /> {new Date(ex.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-1">
                  <Cpu className="h-3 w-3" /> {ex.solver}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

const RefreshCcw = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/>
  </svg>
);

const Badge = ({ children, variant = 'default' }: { children: React.ReactNode, variant?: 'default' | 'secondary' }) => (
  <span className={cn(
    "px-2 py-1 rounded text-xs font-medium",
    variant === 'default' ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-600"
  )}>
    {children}
  </span>
);
