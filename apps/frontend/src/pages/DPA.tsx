import { PageLayout } from '@/components/PageLayout';

export function DPA() {
    return (
        <PageLayout>
            <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-2 text-slate-900 dark:text-white">DATA PROCESSING ADDENDUM (DPA)</h1>
                <p className="text-slate-600 dark:text-slate-400 mb-8">
                    Effective Date: March 4, 2026
                </p>
                <p className="text-slate-800 dark:text-slate-200 mb-8">
                    This Data Processing Addendum ("DPA") forms part of the SimHPC Terms of Service between SimHPC ("Service Provider") and Customer.
                </p>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">1. Roles</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-4">
                        Customer is the Business (as defined under CCPA/CPRA).
                    </p>
                    <p className="text-slate-600 dark:text-slate-400 mb-4">
                        SimHPC acts solely as a Service Provider and processes Personal Information only on documented instructions from Customer.
                    </p>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">SimHPC does not:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>Sell Personal Information</li>
                        <li>Share Personal Information for cross-context behavioral advertising</li>
                        <li>Use Personal Information for unrelated AI training</li>
                        <li>Transfer Personal Information to third-party LLM APIs</li>
                    </ul>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">2. Scope of Processing</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">SimHPC processes Personal Information solely to:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>Provide simulation services</li>
                        <li>Generate structured AI-assisted engineering reports</li>
                        <li>Authenticate users</li>
                        <li>Manage subscriptions and billing</li>
                        <li>Maintain platform security and integrity</li>
                    </ul>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">3. AI Processing & Model Use</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-4">
                        SimHPC may use internally hosted machine learning models to generate structured engineering reports.
                    </p>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">Important safeguards:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>All AI models are self-hosted within SimHPC-controlled infrastructure.</li>
                        <li>Customer data is not transmitted to external LLM APIs.</li>
                        <li>Customer data is not used to train general-purpose AI models.</li>
                        <li>Customer data is not retained for model training.</li>
                        <li>AI outputs are generated per-request and not incorporated into future model updates.</li>
                    </ul>
                    <p className="text-slate-600 dark:text-slate-400 mt-4">
                        AI systems are used solely for report synthesis and structured summarization of Customer-provided simulation data.
                    </p>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">4. Infrastructure & Subprocessors</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">SimHPC may use the following infrastructure providers:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>Cloud compute provider (e.g., Runpod) for GPU and CPU execution</li>
                        <li>Database provider (e.g., Supabase) for PostgreSQL storage</li>
                        <li>Payment processor (e.g., Stripe) for billing transactions</li>
                        <li>Domain and email provider (e.g., Spaceship)</li>
                    </ul>
                    <p className="text-slate-600 dark:text-slate-400 mt-4">
                        These providers process data solely to support the SimHPC service and are bound by contractual confidentiality and security obligations.
                    </p>
                    <p className="text-slate-600 dark:text-slate-400 mt-2">
                        SimHPC does not use third-party AI API providers for report generation.
                    </p>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">5. Data Security Measures</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">SimHPC implements reasonable technical and organizational safeguards including:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>TLS encryption in transit</li>
                        <li>Role-based access control</li>
                        <li>API authentication and authorization</li>
                        <li>Secure password hashing</li>
                        <li>JWT-based session management</li>
                        <li>Simulation job isolation</li>
                        <li>GPU instance isolation per workload</li>
                        <li>Access logging and audit capabilities (Enterprise tier)</li>
                    </ul>
                    <p className="text-slate-600 dark:text-slate-400 mt-4">
                        Customer simulation data is logically isolated between accounts.
                    </p>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">6. Data Retention</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">Customer data is retained only as long as necessary to:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>Provide services</li>
                        <li>Comply with contractual and legal obligations</li>
                        <li>Maintain audit and integrity logs</li>
                    </ul>
                    <p className="text-slate-600 dark:text-slate-400 mt-4">
                        Upon termination, Customer may request deletion of stored data, subject to legal retention requirements.
                    </p>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">7. Incident Response</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">In the event of confirmed unauthorized access to Personal Information under SimHPC control, SimHPC will:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>Notify Customer without unreasonable delay</li>
                        <li>Provide relevant information</li>
                        <li>Take commercially reasonable remediation steps</li>
                    </ul>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">8. No Sale / No Model Training Certification</h2>
                    <p className="text-slate-600 dark:text-slate-400 mb-2">SimHPC certifies that:</p>
                    <ul className="list-disc list-inside text-slate-600 dark:text-slate-400 space-y-1">
                        <li>Personal Information is not sold.</li>
                        <li>Personal Information is not used to train external or internal general-purpose AI models.</li>
                        <li>Personal Information is processed solely to deliver the contracted services.</li>
                    </ul>
                </section>

                <section className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-slate-900 dark:text-white">9. Governing Law</h2>
                    <p className="text-slate-600 dark:text-slate-400">
                        This DPA is governed by the governing law set forth in the SimHPC Terms of Service.
                    </p>
                </section>
            </div>
        </PageLayout>
    );
}
