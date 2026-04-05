import { Link } from 'react-router-dom';
import { ArrowLeft, Play, Clock, BarChart3, FileDown, GitCompare, Upload, AlertCircle, Cpu, Zap, Mail, CheckCircle2, ArrowRight } from 'lucide-react';

const steps = [
  {
    num: 1,
    title: 'Run Your First Simulation',
    steps: [
      'Go to **Templates** in the Sidebar.',
      'Select any starter simulation (e.g., Battery Cell V4).',
      'Click **Run Robustness Analysis**.',
    ],
    note: 'This creates your baseline.',
    icon: Play,
  },
  {
    num: 2,
    title: 'Wait for Completion',
    steps: [
      'Open **Job Queue** or watch the live status.',
      'Status will cycle from *Queued → Running → Completed*.',
    ],
    note: 'Free tier uses shared compute, so short waits are normal.',
    icon: Clock,
  },
  {
    num: 3,
    title: 'View Results',
    steps: [
      'Open your completed job from the **Simulations** history.',
      'Look at the **Output graph**, **Runtime**, and **AI Insight**.',
    ],
    note: 'This is your reference result.',
    icon: BarChart3,
  },
  {
    num: 4,
    title: 'Change ONE Parameter',
    steps: [
      'Click **Modify / Re-run** on the results card.',
      'Change only one value: **Iterations** (speed vs accuracy) or **Grid size** (resolution).',
    ],
    note: 'Keep changes small to see clear trends.',
    icon: Upload,
  },
  {
    num: 5,
    title: 'Re-run Simulation',
    steps: [
      'Click **Run** again and wait for completion.',
    ],
    note: 'Your second job is now processing on the NVIDIA GPU cluster.',
    icon: Play,
  },
  {
    num: 6,
    title: 'Compare Results',
    steps: [
      'Open both runs from your history.',
      'Compare the **Runtime** and **Output differences**.',
    ],
    note: 'This is where real engineering value happens.',
    icon: GitCompare,
  },
  {
    num: 7,
    title: 'Download Report',
    steps: [
      'Click **Download PDF** to save your analysis.',
    ],
    note: 'You now have a shareable engineering artifact.',
    icon: FileDown,
  },
];

export default function Documentation() {
  return (
    <div className="min-h-screen bg-background dark:bg-slate-950">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to SimHPC
          </Link>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">SimHPC — Quick Start</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-2">Welcome to the SimHPC Pilot! This guide will help you run your first physics-based simulation and master the core workflow in 10 minutes.</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
        {/* What You Can Do */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">What You Can Do</h2>
          <div className="grid sm:grid-cols-2 gap-3">
            {[
              'Run real simulations',
              'Change parameters and re-run',
              'Compare results',
              'Download PDF reports',
              '10 Free runs per week',
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3">
                <CheckCircle2 className="w-5 h-5 text-cyan-500 flex-shrink-0" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{item}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Step-by-Step */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-8">Step-by-Step (Do This First)</h2>
          <div className="space-y-6">
            {steps.map((step) => (
              <div key={step.num} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                <div className="flex items-start gap-4 p-6">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center flex-shrink-0">
                    <step.icon className="w-5 h-5 text-cyan-500" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
                      <span className="text-cyan-500 mr-2">{step.num}.</span>
                      {step.title}
                    </h3>
                    <ul className="space-y-2 mb-4">
                      {step.steps.map((s, i) => (
                        <li key={i} className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2">
                          <ArrowRight className="w-4 h-4 text-cyan-500 mt-0.5 flex-shrink-0" />
                          <span dangerouslySetInnerHTML={{ __html: s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>') }} />
                        </li>
                      ))}
                    </ul>
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-cyan-50 dark:bg-cyan-500/10 rounded-lg text-xs text-cyan-700 dark:text-cyan-400 font-medium">
                      <Zap className="w-3.5 h-3.5" />
                      {step.note}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* How to Get the Most Value */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">How to Get the Most Value</h2>
          <div className="bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-500/5 dark:to-blue-500/5 border border-cyan-200 dark:border-cyan-500/20 rounded-xl p-6">
            <p className="text-sm text-slate-700 dark:text-slate-300 mb-4">
              Do this loop 3–5 times: <strong>Run → Change → Re-run → Compare</strong>.
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-400">You'll quickly learn:</p>
            <ul className="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-400">
              <li>• What affects performance</li>
              <li>• What affects accuracy</li>
              <li>• Where compute is wasted</li>
            </ul>
          </div>
        </section>

        {/* Free Tier Limits */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">What to Expect (Free Tier Limits)</h2>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-start gap-2"><AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" /> Slower runs (shared system)</li>
              <li className="flex items-start gap-2"><AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" /> Queue wait times</li>
              <li className="flex items-start gap-2"><AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" /> Limited parallel jobs</li>
            </ul>
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-3">This is normal and intentional for the Alpha phase.</p>
          </div>
        </section>

        {/* When to Upgrade */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">When to Upgrade</h2>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">Upgrade makes sense if:</p>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-start gap-2"><CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" /> You want faster runs (dedicated A40/RTX 3090)</li>
              <li className="flex items-start gap-2"><CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" /> You need multiple simulations at once</li>
              <li className="flex items-start gap-2"><CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" /> You're doing serious structural optimization</li>
            </ul>
          </div>
        </section>

        {/* Key Insight */}
        <section className="bg-slate-900 dark:bg-slate-800 rounded-xl p-8 text-white">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            Key Insight
          </h3>
          <p className="text-slate-300 leading-relaxed mb-4">
            SimHPC is not just about running simulations. It's about <strong className="text-white">Running → Changing → Comparing → Improving</strong>. That loop is the core workflow.
          </p>
          <div className="bg-slate-800 dark:bg-slate-700 rounded-lg p-4 text-sm text-slate-300">
            <strong className="text-cyan-400">TL;DR:</strong> Run a simulation → change one thing → run again → compare. That's how you unlock value.
          </div>
        </section>

        {/* Troubleshooting */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Troubleshooting & Feedback</h2>
          <div className="space-y-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-500" />
                404 on Refresh
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                If you refresh the page and see a 404, just navigate back to the root URL <a href="https://simhpc.com" className="text-cyan-600 dark:text-cyan-400 hover:underline">https://simhpc.com</a>. We are optimizing our Nginx routing for the pilot.
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500" />
                Service Status
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                If any indicator is red, the service may be temporarily unavailable. The <strong>Recent Jobs</strong> log underneath will show if your job failed or is still queued.
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-500" />
                Worker Status
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                GPU Pods are managed by a cost-aware autoscaler (v2.5.0) that "hibernates" (STOP instead of TERMINATE) pods after 5 minutes of idle.
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <Zap className="w-4 h-4 text-blue-500" />
                Wake GPU
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                If the dashboard shows "Stopped," click the blue <strong>"Wake GPU"</strong> button. This will resume your pod from hibernation. It takes about 90 seconds. We recommend doing this while you introduce your use case to others.
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <Clock className="w-4 h-4 text-slate-500" />
                Job Queuing
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                If you don't wake it manually, your first simulation run will trigger the wake-up automatically.
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-green-500" />
                Performance
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                We are running on dedicated <strong>RTX 3090/A40 GPU</strong> clusters with <strong>Network Volume persistence</strong>. This means your solver caches and intermediate weights are preserved even when the pod sleeps.
              </p>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <Mail className="w-4 h-4 text-purple-500" />
                Found a Bug?
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                We'd love to hear from you. Send your feedback directly to <a href="mailto:deploy@simhpc.com" className="text-cyan-600 dark:text-cyan-400 hover:underline">deploy@simhpc.com</a>
              </p>
            </div>
          </div>
        </section>

        {/* Thank you */}
        <div className="text-center py-8">
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Thank you for helping us build the future of deterministic simulation!
          </p>
        </div>
      </div>
    </div>
  );
}
