import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Battery, Rocket, Building2, Landmark, Factory } from 'lucide-react';

const audiences = [
  {
    icon: Battery,
    title: 'Battery & Energy R&D Teams',
    description: 'Thermal simulation for lithium-ion cells and energy storage systems.',
  },
  {
    icon: Rocket,
    title: 'Hardware Startups',
    description: 'Rapid prototyping validation with cloud-scale compute.',
  },
  {
    icon: Building2,
    title: 'Engineering Consultancies',
    description: 'Client-ready reports with quantified confidence metrics.',
  },
  {
    icon: Landmark,
    title: 'National Labs',
    description: 'HPC-class simulation without infrastructure overhead.',
  },
  {
    icon: Factory,
    title: 'Advanced Manufacturing',
    description: 'Process optimization and quality control simulation.',
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
        {/* Section Header */}
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
            Built for teams that require stable, defensible simulation results.
          </p>
        </motion.div>

        {/* Audience Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-6">
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
              className="group bg-background dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg text-center"
            >
              {/* Icon */}
              <div className="w-14 h-14 mx-auto rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                <audience.icon className="w-7 h-7 text-white" />
              </div>

              {/* Content */}
              <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-2">
                {audience.title}
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                {audience.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
