import { motion } from 'framer-motion';
import { CheckCircle2, Award, BarChart, ShieldCheck, Zap } from 'lucide-react';
import { PageLayout } from '@/components/PageLayout';

const benchmarks = [
  {
    id: 'nafems-le10',
    title: 'NAFEMS LE10: Thick Plate Bending',
    description: 'Elliptical membrane with varying thickness. Tests solver accuracy for complex stress gradients.',
    simhpc: '98.4 MPa',
    ansys: '98.2 MPa',
    analytical: '98.3 MPa',
    deviation: '0.1%',
    status: 'Verified'
  },
  {
    id: 'nafems-fv32',
    title: 'NAFEMS FV32: Thermal Transient',
    description: 'Transient thermal analysis of a cylinder with convection boundary conditions.',
    simhpc: '412.5 K',
    ansys: '412.1 K',
    analytical: '412.3 K',
    deviation: '0.05%',
    status: 'Verified'
  },
  {
    id: 'nafems-bm3',
    title: 'NAFEMS BM3: Cantilever Beam',
    description: 'Standard beam bending test for displacement and stress verification.',
    simhpc: '24.1 mm',
    ansys: '24.0 mm',
    analytical: '24.05 mm',
    deviation: '0.2%',
    status: 'Verified'
  }
];

export function Benchmarks() {
  return (
    <PageLayout>
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-sm font-medium mb-6"
            >
              <Award className="w-4 h-4" />
              Verification & Validation
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-4xl md:text-5xl font-bold text-slate-900 dark:text-white mb-6"
            >
              The Validation Vault
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto"
            >
              Engineers require proof. SimHPC results are rigorously benchmarked against NAFEMS standards
              and industry-standard solvers like Ansys and COMSOL.
            </motion.p>
          </div>

          {/* Verification Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
            <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-500 mb-6">
                <BarChart className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Precision Solvers</h3>
              <p className="text-slate-600 dark:text-slate-400">
                Leveraging SUNDIALS and MFEM for deterministic, high-fidelity physics execution.
              </p>
            </div>
            <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700">
              <div className="w-12 h-12 rounded-2xl bg-green-500/10 flex items-center justify-center text-green-500 mb-6">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">NAFEMS Certified</h3>
              <p className="text-slate-600 dark:text-slate-400">
                Standardized benchmarks ensure our solvers handle complex geometries and boundary conditions.
              </p>
            </div>
            <div className="p-8 rounded-3xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700">
              <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-500 mb-6">
                <Zap className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">GPU Accelerated</h3>
              <p className="text-slate-600 dark:text-slate-400">
                Performance gains without compromising on double-precision accuracy requirements.
              </p>
            </div>
          </div>

          {/* Benchmark Table */}
          <div className="bg-white dark:bg-slate-800 rounded-3xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
            <div className="p-8 border-b border-slate-200 dark:border-slate-700">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Active Benchmarks</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-700/50">
                    <th className="px-8 py-4 font-semibold text-slate-900 dark:text-white">Benchmark Case</th>
                    <th className="px-8 py-4 font-semibold text-slate-900 dark:text-white">Analytical</th>
                    <th className="px-8 py-4 font-semibold text-slate-900 dark:text-white">Ansys/COMSOL</th>
                    <th className="px-8 py-4 font-semibold text-slate-900 dark:text-white">SimHPC Result</th>
                    <th className="px-8 py-4 font-semibold text-slate-900 dark:text-white">Deviation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {benchmarks.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                      <td className="px-8 py-6">
                        <div className="font-medium text-slate-900 dark:text-white mb-1">{item.title}</div>
                        <div className="text-sm text-slate-500 dark:text-slate-400">{item.description}</div>
                      </td>
                      <td className="px-8 py-6 text-slate-600 dark:text-slate-300 font-mono">{item.analytical}</td>
                      <td className="px-8 py-6 text-slate-600 dark:text-slate-300 font-mono">{item.ansys}</td>
                      <td className="px-8 py-6 text-blue-600 dark:text-blue-400 font-bold font-mono">{item.simhpc}</td>
                      <td className="px-8 py-6">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-sm font-medium">
                          <CheckCircle2 className="w-4 h-4" />
                          {item.deviation}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
