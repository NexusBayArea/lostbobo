import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Building2, Zap, Shield, TrendingUp } from 'lucide-react';

const audiences = [
  {
    icon: Building2,
    title: 'Engineering Teams',
    description: 'Run robustness analysis and sensitivity studies 100x faster with GPU acceleration and built-in confidence intervals.',
    features: ['Fast iteration', 'Statistical confidence', 'Team collaboration'],
  },
  {
    icon: Zap,
    title: 'Research Institutions',
    description: 'Publish reproducible results with deterministic, audited execution and complete computational transparency.',
    features: ['Reproducible science', 'Audit trails', 'Paper-ready outputs'],
  },
  {
    icon: Shield,
    title: 'Defense & Aerospace',
    description: 'ITAR/EAR compliant infrastructure with zero-trust secrets, on-prem options, and enterprise controls.',
    features: ['Export compliant', 'Secure infrastructure', 'Audit logs'],
  },
  {
    icon: TrendingUp,
    title: 'Design Optimization',
    description: 'Accelerate design iterations with parametric studies and sensitivity ranking to guide decision-making.',
    features: ['Fast optimization', 'Parameter sweeps', 'Design insights'],
  },
];

export function WhoItsFor() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section
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
            Who It's For
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            From design teams to research labs, SimHPC powers anyone doing serious FEM work.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
          {audiences.map((audience, index) => (
            <motion.div
              key={audience.title}
              initial={{ opacity: 0, y: 40 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{
                duration: 0.7,
                delay: index * 0.1,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="group bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                <audience.icon className="w-6 h-6 text-white" />
              </div>

              <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                {audience.title}
              </h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm mb-4 leading-relaxed">
                {audience.description}
              </p>

              <div className="flex flex-wrap gap-2">
                {audience.features.map((feature) => (
                  <span
                    key={feature}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full"
                  >
                    <span className="w-1 h-1 rounded-full bg-blue-500" />
                    {feature}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}