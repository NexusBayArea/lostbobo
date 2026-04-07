import { PageLayout } from '@/components/PageLayout';

export function APIReference() {
    return (
        <PageLayout>
            <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-6 text-slate-900 dark:text-white">SimHPC API Reference</h1>
                
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                    The SimHPC API provides secure programmatic access to:
                </p>
                <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 mb-6 space-y-1">
                    <li>Simulation job submission</li>
                    <li>Job status retrieval</li>
                    <li>AI report generation</li>
                    <li>Robustness metrics</li>
                    <li>Results export</li>
                </ul>
                <p className="text-slate-600 dark:text-slate-400 mb-8">
                    All API endpoints require authentication.
                </p>

                <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Authentication</h2>
                <p className="text-slate-600 dark:text-slate-400 mb-2">SimHPC uses JWT-based authentication.</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">Authorization Header:</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">Authorization: Bearer [access_token]</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">API keys available for paid tiers. Enterprise customers may request scoped API tokens.</p>

                <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Base URL</h2>
                <p className="text-slate-600 dark:text-slate-400 mb-2">https://api.simhpc.com/v1</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">All requests must use HTTPS.</p>

                <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Core Endpoints</h2>
                
                <h3 className="text-xl font-medium mb-2 text-slate-900 dark:text-white">Submit Simulation Job</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-2">POST /simulations</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">Request: model_type, mesh_parameters, solver_config, robustness_sweep. Response: job_id, status</p>

                <h3 className="text-xl font-medium mb-2 text-slate-900 dark:text-white">Retrieve Simulation Status</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-2">GET /simulations/[job_id]</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">Response: job_id, status, progress</p>

                <h3 className="text-xl font-medium mb-2 text-slate-900 dark:text-white">Retrieve Simulation Results</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-2">GET /simulations/[job_id]/results</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">Response includes: Mesh metrics, Convergence data, Stability metrics, Robustness indicators</p>

                <h3 className="text-xl font-medium mb-2 text-slate-900 dark:text-white">Generate AI Report</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-2">POST /reports</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">Request: simulation_id, format. Response: report_id, status</p>

                <h3 className="text-xl font-medium mb-2 text-slate-900 dark:text-white">Retrieve AI Report</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-2">GET /reports/[report_id]</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">Response: executive_summary, robustness_score, confidence_level, flags</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">AI reports are generated using internally hosted models. Customer data is not transmitted to external AI service providers.</p>

                <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Rate Limits</h2>
                <p className="text-slate-600 dark:text-slate-400 mb-2">Free tier: Limited simulation runs. No API access.</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">Startup tiers: Tier-based job concurrency. Token-based compute allocation.</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">Enterprise tier: Custom concurrency limits. Dedicated compute options available.</p>

                <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Security and Data Handling</h2>
                <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 mb-8 space-y-1">
                    <li>All requests encrypted via TLS</li>
                    <li>Simulation workloads isolated per account</li>
                    <li>AI processing performed within SimHPC infrastructure</li>
                    <li>No third-party AI API calls</li>
                    <li>No data used for model training</li>
                </ul>

                <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Error Handling</h2>
                <p className="text-slate-600 dark:text-slate-400 mb-2">200 - Success</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">400 - Invalid request</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">401 - Unauthorized</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">403 - Forbidden</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">404 - Not found</p>
                <p className="text-slate-600 dark:text-slate-400 mb-2">429 - Rate limit exceeded</p>
                <p className="text-slate-600 dark:text-slate-400 mb-8">500 - Internal error</p>

                <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">Webhooks</h2>
                <p className="text-slate-600 dark:text-slate-400 mb-2">Enterprise customers may subscribe to webhooks for:</p>
                <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 mb-2 space-y-1">
                    <li>Simulation completion</li>
                    <li>Report completion</li>
                    <li>Subscription changes</li>
                </ul>
                <p className="text-slate-600 dark:text-slate-400">Webhook signatures are verified using HMAC.</p>
            </div>
        </PageLayout>
    );
}
