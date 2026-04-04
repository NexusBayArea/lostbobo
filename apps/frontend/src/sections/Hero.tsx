import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Play } from 'lucide-react';
import { AnimatedMesh } from '@/components/AnimatedMesh';
import { ConfidenceGraph } from '@/components/ConfidenceGraph';

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-white dark:bg-slate-900">
      {/* Animated Mesh Background */}
      <div className="absolute inset-0 opacity-60">
        <AnimatedMesh />
      </div>

      {/* Gradient Overlays */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-blue-50/30 dark:to-blue-900/10 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-tl from-purple-50/20 dark:from-purple-900/5 via-transparent to-transparent pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-[72px]">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center min-h-[calc(100vh-72px)] py-16">
          {/* Left Column - Text */}
          <div className="space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            >
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-sm font-medium">
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                Now with AI-assisted reporting
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 dark:text-white leading-[1.1]"
            >
              Simulation with{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
                Quantified Confidence.
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
              className="text-lg sm:text-xl text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed"
            >
              AI-assisted, GPU-accelerated finite element simulation with integrated 
              robustness analysis and structured technical reporting — built for 
              engineering teams that need answers they can trust.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-col sm:flex-row gap-4"
            >
              <Link
                to="/signup"
                className="inline-flex items-center justify-center gap-2 px-6 py-4 text-base font-medium text-white bg-slate-900 dark:bg-white dark:text-slate-900 rounded-xl hover:bg-slate-800 dark:hover:bg-slate-100 transition-all hover:scale-[1.02] hover:shadow-lg"
              >
                Run a Simulation
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/dashboard"
                className="inline-flex items-center justify-center gap-2 px-6 py-4 text-base font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-all hover:scale-[1.02]"
              >
                <Play className="w-5 h-5" />
                See Robustness in Action
              </Link>
            </motion.div>

            {/* Trust Badges */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
              className="flex items-center gap-6 pt-4"
            >
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                GPU Accelerated
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                No Setup Required
              </div>
            </motion.div>
          </div>

          {/* Right Column - Visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            <div className="relative bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm rounded-3xl border border-slate-200 dark:border-slate-700 p-6 sm:p-8 shadow-2xl">
              {/* Confidence Graph */}
              <div className="mb-6">
                <ConfidenceGraph />
              </div>

              {/* Stats Cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-50 dark:bg-slate-800/80 rounded-xl p-4 text-center">
                  <div className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">2.1M</div>
                  <div className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">Mesh Elements</div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/80 rounded-xl p-4 text-center">
                  <div className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">48.2s</div>
                  <div className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">Convergence</div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/80 rounded-xl p-4 text-center">
                  <div className="text-2xl sm:text-3xl font-bold text-green-600 dark:text-green-400">±3.1%</div>
                  <div className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">Confidence</div>
                </div>
              </div>

              {/* AI Report Preview */}
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400">AI Report Generated</span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                  "Model output indicates peak temperature is primarily driven by boundary heat flux variation. 
                  System stability is sensitive to cooling efficiency..."
                </p>
              </div>
            </div>

            {/* Floating Elements */}
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -top-4 -right-4 w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg"
            >
              <span className="text-white font-bold text-lg">MFEM</span>
            </motion.div>

            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
              className="absolute -bottom-4 -left-4 w-24 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg"
            >
              <span className="text-white font-bold">SUNDIALS</span>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Gradient Fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white dark:from-slate-900 to-transparent pointer-events-none" />
    </section>
  );
}
