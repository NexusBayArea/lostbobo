import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BookOpen, ChevronDown, ChevronRight, Copy, Check, ArrowLeft } from 'lucide-react';

const concepts = [
  { term: 'Simulation', def: 'A single execution of a scenario' },
  { term: 'Scenario', def: 'Input configuration defining a simulation' },
  { term: 'Job', def: 'Backend compute task (GPU/CPU execution)' },
  { term: 'Result', def: 'Output data generated from a simulation' },
];

const endpoints = [
  {
    method: 'POST',
    path: '/simulations',
    title: 'Create Simulation',
    description: 'Start a new simulation run.',
    body: `{
  "scenario_name": "flood-risk-downtown",
  "parameters": {
    "rainfall": 120,
    "duration": 48
  }
}`,
    response: `{
  "id": "sim_123",
  "status": "queued",
  "created_at": "2026-04-04T12:00:00Z"
}`,
  },
  {
    method: 'GET',
    path: '/simulations/{id}',
    title: 'Get Simulation',
    description: 'Retrieve a specific simulation.',
    response: `{
  "id": "sim_123",
  "status": "running",
  "scenario_name": "flood-risk-downtown",
  "result_summary": null,
  "created_at": "...",
  "updated_at": "..."
}`,
  },
  {
    method: 'GET',
    path: '/simulations',
    title: 'List Simulations',
    description: 'Fetch all simulations for a user.',
    queryParams: [
      { name: 'status', type: 'string', desc: 'Filter by status' },
      { name: 'limit', type: 'number', desc: 'Max results' },
    ],
    response: `[
  {
    "id": "sim_123",
    "status": "completed"
  }
]`,
  },
  {
    method: 'POST',
    path: '/simulations/{id}/cancel',
    title: 'Cancel Simulation',
    description: 'Stop a running or queued simulation.',
    response: `{
  "id": "sim_123",
  "status": "cancelled"
}`,
  },
  {
    method: 'GET',
    path: '/simulations/{id}/results',
    title: 'Get Results',
    description: 'Retrieve simulation outputs.',
    response: `{
  "result_summary": {
    "flooded_area": 1200,
    "risk_score": 0.82
  },
  "gpu_result": {
    "mesh_data": "...",
    "heatmap": "..."
  }
}`,
  },
];

const statusLifecycle = [
  { status: 'queued', desc: 'Waiting for compute resources' },
  { status: 'running', desc: 'Actively executing' },
  { status: 'completed', desc: 'Finished successfully' },
  { status: 'failed', desc: 'Execution error' },
  { status: 'cancelled', desc: 'Stopped by user' },
];

const rateLimits = [
  { plan: 'Free', limit: '10 simulations / week' },
  { plan: 'Paid', limit: 'Configurable' },
];

const errorCodes = [
  { code: 'UNAUTHORIZED', meaning: 'Invalid API key' },
  { code: 'NOT_FOUND', meaning: 'Resource missing' },
  { code: 'RATE_LIMITED', meaning: 'Too many requests' },
  { code: 'INVALID_REQUEST', meaning: 'Bad input' },
];

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="bg-slate-950 dark:bg-black text-slate-300 dark:text-slate-400 p-4 rounded-xl text-sm font-mono overflow-x-auto border border-slate-800">
        <code>{code}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
      >
        {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
      </button>
    </div>
  );
}

function MethodBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET: 'bg-green-500/10 text-green-400 border-green-500/20',
    POST: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    PUT: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    DELETE: 'bg-red-500/10 text-red-400 border-red-500/20',
  };
  return (
    <span className={`px-2.5 py-1 text-xs font-bold font-mono rounded-md border ${colors[method] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'}`}>
      {method}
    </span>
  );
}

function CollapsibleSection({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden mb-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
      >
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h3>
        {open ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
      </button>
      {open && <div className="px-6 py-4 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-800">{children}</div>}
    </div>
  );
}

export default function ApiReference() {
  return (
    <div className="min-h-screen bg-background dark:bg-slate-950">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to SimHPC
          </Link>
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-cyan-500" />
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">API Reference</h1>
              <p className="text-slate-500 dark:text-slate-400 mt-1">SimHPC Simulation API v1</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        {/* Core Concepts */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Core Concepts</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {concepts.map((c) => (
              <div key={c.term} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5">
                <dt className="text-sm font-semibold text-cyan-600 dark:text-cyan-400 mb-1">{c.term}</dt>
                <dd className="text-sm text-slate-600 dark:text-slate-400">{c.def}</dd>
              </div>
            ))}
          </div>
        </section>

        {/* Endpoints */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Endpoints</h2>
          <div className="space-y-4">
            {endpoints.map((ep) => (
              <CollapsibleSection key={ep.path} title={ep.title} defaultOpen={false}>
                <div className="space-y-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400">{ep.description}</p>
                  <div className="flex items-center gap-3">
                    <MethodBadge method={ep.method} />
                    <code className="text-sm font-mono text-slate-900 dark:text-white">{ep.path}</code>
                  </div>

                  {ep.queryParams && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Query Parameters</h4>
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-200 dark:border-slate-700">
                            <th className="text-left py-2 text-slate-500 font-medium">Param</th>
                            <th className="text-left py-2 text-slate-500 font-medium">Type</th>
                            <th className="text-left py-2 text-slate-500 font-medium">Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ep.queryParams.map((qp) => (
                            <tr key={qp.name} className="border-b border-slate-100 dark:border-slate-800">
                              <td className="py-2 font-mono text-cyan-600 dark:text-cyan-400">{qp.name}</td>
                              <td className="py-2 text-slate-500">{qp.type}</td>
                              <td className="py-2 text-slate-600 dark:text-slate-400">{qp.desc}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {ep.body && (
                    <div>
                      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Request Body</h4>
                      <CodeBlock code={ep.body} />
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Response</h4>
                    <CodeBlock code={ep.response} />
                  </div>
                </div>
              </CollapsibleSection>
            ))}
          </div>
        </section>

        {/* Status Lifecycle */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Simulation Status Lifecycle</h2>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left px-6 py-3 text-slate-500 font-medium">Status</th>
                  <th className="text-left px-6 py-3 text-slate-500 font-medium">Description</th>
                </tr>
              </thead>
              <tbody>
                {statusLifecycle.map((s) => (
                  <tr key={s.status} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
                    <td className="px-6 py-3">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono">
                        {s.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{s.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Rate Limits */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Rate Limits</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">Burst Limit: <code className="text-cyan-600 dark:text-cyan-400">5 requests/sec</code></p>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left px-6 py-3 text-slate-500 font-medium">Plan</th>
                  <th className="text-left px-6 py-3 text-slate-500 font-medium">Limit</th>
                </tr>
              </thead>
              <tbody>
                {rateLimits.map((r) => (
                  <tr key={r.plan} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
                    <td className="px-6 py-3 font-medium text-slate-900 dark:text-white">{r.plan}</td>
                    <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{r.limit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Errors */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Errors</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">Standard Error Format:</p>
          <CodeBlock code={`{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing scenario parameters"
  }
}`} />
          <div className="mt-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left px-6 py-3 text-slate-500 font-medium">Code</th>
                  <th className="text-left px-6 py-3 text-slate-500 font-medium">Meaning</th>
                </tr>
              </thead>
              <tbody>
                {errorCodes.map((e) => (
                  <tr key={e.code} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
                    <td className="px-6 py-3 font-mono text-red-500 text-xs">{e.code}</td>
                    <td className="px-6 py-3 text-slate-600 dark:text-slate-400">{e.meaning}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Best Practices */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Best Practices</h2>
          <ul className="space-y-3">
            {[
              'Poll sparingly; prefer WebSocket updates',
              'Validate scenario inputs before submission',
              'Handle all status states (including failed)',
              'Store simulation IDs for later retrieval',
            ].map((tip) => (
              <li key={tip} className="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 mt-2 flex-shrink-0" />
                {tip}
              </li>
            ))}
          </ul>
        </section>

        {/* Versioning */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Versioning</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            The API is versioned via the URL: <code className="text-cyan-600 dark:text-cyan-400">/v1/</code>. Breaking changes will be released under new versions.
          </p>
        </section>

        {/* Support */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Support</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">For issues or enterprise access:</p>
          <ul className="space-y-2 text-sm">
            <li className="text-slate-600 dark:text-slate-400">
              Email: <a href="mailto:support@simhpc.com" className="text-cyan-600 dark:text-cyan-400 hover:underline">support@simhpc.com</a>
            </li>
            <li className="text-slate-600 dark:text-slate-400">Dedicated Slack (paid plans)</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
