import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Cpu, Shield, Database, Zap, GitBranch, Lock } from 'lucide-react';

const features = [
  {
    icon: Cpu,
    title: 'GPU-Accelerated',
    description: 'Run on A40 and H100 GPUs with CUDA 12.4 for 100x speedup.',
    items: ['SUNDIALS time integration', 'MFEM discretization', 'GPU acceleration'],
  },
  {
    icon: Shield,
    title: 'Deterministic',
    description: 'Reproducible results with seeded random numbers and contract enforcement.',
    items: ['Seeded randomness', 'Verified results', 'Audit trails'],
  },
  {
    icon: Database,
    title: 'Supabase-Backed',
    description: 'PostgreSQL persistence with RLS policies and complete audit trails.',
    items: ['Row-level security', 'Audit logging', 'Type-safe queries'],
  },
  {
    icon: Zap,
    title: 'Real-Time API',
    description: 'WebSocket streaming for live execution updates and telemetry.',
    items: ['Live status', 'WebSocket streaming', 'REST endpoints'],
  },
  {
    icon: GitBranch,
    title: 'DAG Execution',
    description: 'Topologically-ordered CI/physics DAG with automatic parallelization.',
    items: ['Graph execution', 'Auto-dependencies', 'Parallel nodes'],
  },
  {
    icon: Lock,
    title: 'Enterprise Ready',
    description: 'ITAR/EAR compliant, zero-trust secrets, non-root Docker containers.',
    items: ['Export compliant', 'Vault secrets', 'Secure containers'],
  },
];

export function Stack() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section
      id="features"
      ref={ref}
      className="py-24 lg:py-32 bg-slate-50 dark:bg-slate-800/50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white tracking-tight mb-6">
            Technical Stack
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Built with production-grade infrastructure and modern best practices.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 40 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{
                duration: 0.7,
                delay: index * 0.1,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="group relative bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                <feature.icon className="w-6 h-6 text-white" />
              </div>

              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm mb-4 leading-relaxed">
                {feature.description}
              </p>

              <ul className="space-y-1.5">
                {feature.items.map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"
                  >
                    <svg
                      className="w-3.5 h-3.5 text-green-500 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}