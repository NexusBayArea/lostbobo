import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Cpu, Monitor, BarChart3, FileText } from 'lucide-react';

const features = [
  {
    icon: Cpu,
    title: 'Deterministic Physics Core',
    description: 'SUNDIALS for time integration, MFEM for high-order finite element discretization, with GPU-accelerated execution.',
    items: ['SUNDIALS time integration', 'MFEM discretization', 'GPU acceleration'],
  },
  {
    icon: Monitor,
    title: 'Browser-Native Visualization',
    description: 'GLVis WebGL streaming enables interactive field exploration and mesh inspection directly in your browser.',
    items: ['GLVis WebGL streaming', 'Interactive fields', 'Mesh inspection'],
  },
  {
    icon: BarChart3,
    title: 'Integrated Robustness Analysis',
    description: 'Automated parameter perturbation with sensitivity ranking and confidence interval quantification.',
    items: ['Parameter perturbation', 'Sensitivity ranking', 'Confidence intervals'],
  },
  {
    icon: FileText,
    title: 'AI Technical Report Layer',
    description: 'Structured engineering summaries with sensitivity interpretation and suggested next simulation steps.',
    items: ['Structured summaries', 'Sensitivity interpretation', 'Exportable documentation'],
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
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white tracking-tight mb-6">
            Built on Proven Scientific Infrastructure
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Enterprise-grade simulation stack combining deterministic physics solvers 
            with modern cloud infrastructure.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
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
              className="group relative bg-white dark:bg-slate-800 rounded-2xl p-8 border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
            >
              {/* Icon */}
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <feature.icon className="w-7 h-7 text-white" />
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
                {feature.title}
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-6 leading-relaxed">
                {feature.description}
              </p>

              {/* Items */}
              <ul className="space-y-2">
                {feature.items.map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400"
                  >
                    <svg
                      className="w-4 h-4 text-green-500 flex-shrink-0"
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
