import { motion } from 'framer-motion';
import { Loader2, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface JobProgressProps {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'queued' | 'processing';
  progress: number;
  className?: string;
}

export function JobProgress({ status, progress, className }: JobProgressProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'queued':
      case 'pending':
        return {
          icon: Clock,
          color: 'text-amber-500',
          bgColor: 'bg-amber-500',
          label: 'Waiting in Queue...',
        };
      case 'processing':
      case 'running':
        return {
          icon: Loader2,
          color: 'text-blue-500',
          bgColor: 'bg-blue-500',
          label: `Processing Physics: ${progress}%`,
          animate: true,
        };
      case 'completed':
        return {
          icon: CheckCircle2,
          color: 'text-emerald-500',
          bgColor: 'bg-emerald-500',
          label: 'Analysis Complete',
        };
      case 'failed':
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-500',
          label: 'Simulation Failed',
        };
      default:
        return {
          icon: Clock,
          color: 'text-slate-400',
          bgColor: 'bg-slate-400',
          label: 'Unknown State',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={cn("w-5 h-5", config.color, config.animate && "animate-spin")} />
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {config.label}
          </span>
        </div>
        {status === 'processing' || status === 'running' ? (
          <span className="text-xs font-mono text-slate-500">{progress}%</span>
        ) : null}
      </div>
      
      <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <motion.div
          className={cn("h-full", config.bgColor)}
          initial={{ width: 0 }}
          animate={{ 
            width: `${status === 'completed' ? 100 : (status === 'failed' ? 100 : progress)}%` 
          }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
