import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { CheckCircle2, XCircle } from 'lucide-react';

const comparison = [
  {
    feature: 'Speed',
    simhpc: '< 5 minutes per run',
    traditional: '2-8 hours',
  },
  {
    feature: 'Confidence Intervals',
    simhpc: 'Built-in (Sobol GSA)',
    traditional: 'Manual post-processing',
  },
  {
    feature: 'GPU Support',
    simhpc: 'A40, H100, native CUDA',
    traditional: 'CPU-bound or expensive',
  },
  {
    feature: 'Determinism',
    simhpc: 'Verified and audited',
    traditional: 'Manual verification',
  },
  {
    feature: 'API Access',
    simhpc: 'REST + WebSocket streaming',
    traditional: 'Manual downloads',
  },
  {
    feature: 'Compliance',
    simhpc: 'ITAR/EAR ready, audit logs',
    traditional: 'Manual controls',
  },
];

export function ValueDifferentiator() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section
      ref={ref}
      className="py-24 lg:py-32 bg-white dark:bg-slate-900"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white tracking-tight mb-6">
            Why Choose SimHPC?
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Faster, more reliable, and enterprise-ready compared to traditional workflows.
          </p>
        </motion.div>

        <div className="overflow-x-auto">
          <table className="w-full max-w-4xl mx-auto">
            <thead>
              <tr className="border-b-2 border-slate-200 dark:border-slate-700">
                <th className="text-left py-4 px-6 font-semibold text-slate-900 dark:text-white">Feature</th>
                <th className="text-left py-4 px-6 font-semibold text-blue-600 dark:text-blue-400">SimHPC</th>
                <th className="text-left py-4 px-6 font-semibold text-slate-500 dark:text-slate-400">Traditional</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((row, index) => (
                <motion.tr
                  key={row.feature}
                  initial={{ opacity: 0, x: -20 }}
                  animate={isInView ? { opacity: 1, x: 0 } : {}}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                  className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <td className="py-4 px-6 font-medium text-slate-900 dark:text-white">{row.feature}</td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                      <span className="text-slate-700 dark:text-slate-300">{row.simhpc}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      <XCircle className="w-5 h-5 text-slate-400 dark:text-slate-600 flex-shrink-0" />
                      <span className="text-slate-500 dark:text-slate-400">{row.traditional}</span>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}