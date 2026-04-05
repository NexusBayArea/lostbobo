import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { X, Check } from 'lucide-react';

const traditionalWorkflow = [
  'Run simulation',
  'Inspect output',
  'Manually run parameter sweeps',
];

const simhpcWorkflow = [
  'Run simulation',
  'Automatically quantify sensitivity',
  'Generate structured technical report',
  'Understand result stability',
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
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white tracking-tight mb-6">
            We Don't Just Run Simulations.
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
              We Measure How Stable They Are.
            </span>
          </h2>
        </motion.div>

        {/* Comparison */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Traditional Workflow */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            <div className="absolute -inset-px bg-gradient-to-r from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 rounded-2xl opacity-50" />
            <div className="relative bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-8 border border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-slate-500 dark:text-slate-400 mb-6 flex items-center gap-2">
                <X className="w-5 h-5 text-red-500" />
                Traditional Workflow
              </h3>
              <ul className="space-y-4">
                {traditionalWorkflow.map((step, index) => (
                  <motion.li
                    key={step}
                    initial={{ opacity: 0, x: -20 }}
                    animate={isInView ? { opacity: 1, x: 0 } : {}}
                    transition={{
                      duration: 0.5,
                      delay: 0.3 + index * 0.1,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                    className="flex items-center gap-3"
                  >
                    <span className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-sm font-medium text-slate-500 dark:text-slate-400">
                      {index + 1}
                    </span>
                    <span className="text-slate-500 dark:text-slate-400 line-through">
                      {step}
                    </span>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.div>

          {/* SimHPC Workflow */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            <div className="absolute -inset-px bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl" />
            <div className="relative bg-white dark:bg-slate-800 rounded-2xl p-8">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                SimHPC Workflow
              </h3>
              <ul className="space-y-4">
                {simhpcWorkflow.map((step, index) => (
                  <motion.li
                    key={step}
                    initial={{ opacity: 0, x: 20 }}
                    animate={isInView ? { opacity: 1, x: 0 } : {}}
                    transition={{
                      duration: 0.5,
                      delay: 0.4 + index * 0.1,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                    className="flex items-center gap-3"
                  >
                    <span className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-sm font-medium text-white">
                      {index + 1}
                    </span>
                    <span className="text-slate-900 dark:text-white font-medium">
                      {step}
                    </span>
                    <Check className="w-5 h-5 text-green-500 ml-auto" />
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
