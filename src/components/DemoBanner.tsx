import { motion } from 'framer-motion';
import { Zap, AlertTriangle } from 'lucide-react';

interface DemoBannerProps {
  remaining: number;
  limit: number;
}

/**
 * Banner displayed at the top of the dashboard for demo users,
 * showing remaining simulation runs and upgrade CTA.
 */
export function DemoBanner({ remaining, limit }: DemoBannerProps) {
  const used = limit - remaining;
  const percentage = Math.round((used / limit) * 100);
  const isLow = remaining <= 2;
  const isExhausted = remaining <= 0;

  if (isExhausted) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-red-500/10 via-orange-500/10 to-red-500/10 border border-red-200 dark:border-red-800 rounded-2xl p-5 mb-6"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/40 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <p className="font-semibold text-red-700 dark:text-red-300 text-sm">
                Demo Complete
              </p>
              <p className="text-xs text-red-600/70 dark:text-red-400/70">
                You've used all {limit} demo simulations.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <a
              href="mailto:deploy@simhpc.com?subject=Request%20Extended%20Demo%20Access"
              className="px-4 py-2 text-xs font-semibold bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Request More Access
            </a>
            <a
              href="/pricing"
              className="px-4 py-2 text-xs font-semibold bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Upgrade
            </a>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl p-5 mb-6 border ${
        isLow
          ? 'bg-gradient-to-r from-amber-500/5 via-orange-500/5 to-amber-500/5 border-amber-200 dark:border-amber-800'
          : 'bg-gradient-to-r from-blue-500/5 via-indigo-500/5 to-blue-500/5 border-blue-200 dark:border-blue-800'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            isLow
              ? 'bg-amber-100 dark:bg-amber-900/40'
              : 'bg-blue-100 dark:bg-blue-900/40'
          }`}>
            <Zap className={`w-5 h-5 ${isLow ? 'text-amber-500' : 'text-blue-500'}`} />
          </div>
          <div>
            <p className={`font-semibold text-sm ${
              isLow
                ? 'text-amber-700 dark:text-amber-300'
                : 'text-blue-700 dark:text-blue-300'
            }`}>
              Demo Mode — {remaining} run{remaining !== 1 ? 's' : ''} remaining
            </p>
            <p className={`text-xs ${
              isLow
                ? 'text-amber-600/70 dark:text-amber-400/70'
                : 'text-blue-600/70 dark:text-blue-400/70'
            }`}>
              {used} of {limit} simulations used
            </p>
          </div>
        </div>
        <a
          href="/pricing"
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            isLow
              ? 'bg-amber-600 text-white hover:bg-amber-700'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          Upgrade Plan
        </a>
      </div>

      {/* Progress Bar */}
      <div className="mt-3 w-full h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full rounded-full ${
            isLow
              ? 'bg-gradient-to-r from-amber-400 to-orange-500'
              : 'bg-gradient-to-r from-blue-400 to-indigo-500'
          }`}
        />
      </div>
    </motion.div>
  );
}
