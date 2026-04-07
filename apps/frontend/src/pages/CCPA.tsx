import { PageLayout } from '@/components/PageLayout';
import { ShieldCheck } from 'lucide-react';

export function CCPA() {
    return (
        <PageLayout>
            <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-2 text-slate-900 dark:text-white">California Privacy Notice</h1>
                <p className="text-slate-600 dark:text-slate-400 mb-8">
                    Effective Date: 3/3/2026 | Last Updated: 3/3/2026
                </p>
                
                <div className="space-y-8 text-slate-800 dark:text-slate-200">
                    <p>
                        This California Privacy Notice supplements the SimHPC Privacy Policy and applies solely to
                        residents of the State of California. It is provided pursuant to the California Consumer Privacy Act (CCPA), as amended by the California Privacy Rights Act (CPRA).
                    </p>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">1. Categories of Personal Information We Collect</h2>
                        <p className="mb-4">In the past 12 months, SimHPC has collected the following categories of personal information:</p>
                        
                        <h3 className="text-xl font-semibold mb-3 mt-4">A. Identifiers</h3>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Name</li>
                            <li>Email address</li>
                            <li>Account username</li>
                            <li>IP address</li>
                            <li>API keys (associated with user accounts)</li>
                        </ul>

                        <h3 className="text-xl font-semibold mb-3 mt-4">B. Commercial Information</h3>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Subscription tier</li>
                            <li>Billing status</li>
                            <li>Transaction history (processed via Stripe)</li>
                            <li>Service usage history</li>
                        </ul>

                        <h3 className="text-xl font-semibold mb-3 mt-4">C. Internet or Network Activity</h3>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Log data</li>
                            <li>Browser type</li>
                            <li>Device metadata</li>
                            <li>Platform interaction logs</li>
                            <li>API usage metrics</li>
                        </ul>

                        <h3 className="text-xl font-semibold mb-3 mt-4">D. Professional Information (If Provided)</h3>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Company name</li>
                            <li>Job title</li>
                            <li>Industry</li>
                            <li>Business contact information</li>
                        </ul>

                        <h3 className="text-xl font-semibold mb-3 mt-4">E. Inferences</h3>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Subscription preferences</li>
                            <li>Feature usage patterns</li>
                            <li>Platform engagement metrics</li>
                        </ul>

                        <p className="mt-4">We do not collect:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Biometric data</li>
                            <li>Precise geolocation</li>
                            <li>Sensitive personal health information</li>
                            <li>Social security numbers</li>
                            <li>Driver's license numbers</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">2. Sources of Personal Information</h2>
                        <p className="mb-4">We collect personal information directly from:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>You (account registration, form submissions)</li>
                            <li>Your device (via standard web technologies)</li>
                            <li>Third-party authentication providers (e.g., Google OAuth)</li>
                            <li>Payment processors (e.g., Stripe)</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">3. Purpose for Collecting Personal Information</h2>
                        <p className="mb-4">We collect personal information to:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Provide and maintain the SimHPC platform</li>
                            <li>Authenticate users</li>
                            <li>Process subscriptions and billing</li>
                            <li>Monitor system performance and security</li>
                            <li>Provide customer support</li>
                            <li>Improve platform features</li>
                            <li>Prevent fraud and abuse</li>
                            <li>Comply with legal obligations</li>
                        </ul>
                        <p className="mt-4">We do not collect personal information for resale.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">4. Sale or Sharing of Personal Information</h2>
                        <p className="mb-4">SimHPC does not sell personal information.</p>
                        <p className="mb-4">SimHPC does not share personal information for cross-context behavioral advertising.</p>
                        <p className="mb-4">We do not operate as a data broker.</p>
                        <p>If this practice changes in the future, this notice will be updated accordingly.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">5. Retention of Personal Information</h2>
                        <p className="mb-4">We retain personal information only for as long as necessary to:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Provide services</li>
                            <li>Fulfill contractual obligations</li>
                            <li>Maintain security and audit records</li>
                            <li>Comply with legal requirements</li>
                        </ul>
                        <p className="mt-4">Account data may be retained following subscription termination for operational, security, or compliance purposes.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">6. Your Rights Under California Law</h2>
                        <p className="mb-4">If you are a California resident, you have the right to:</p>
                        
                        <h3 className="text-xl font-semibold mb-3 mt-4">A. Right to Know</h3>
                        <p className="mb-2">Request disclosure of:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Categories of personal information collected</li>
                            <li>Sources of information</li>
                            <li>Business purposes for collection</li>
                            <li>Categories of third parties receiving data</li>
                        </ul>

                        <h3 className="text-xl font-semibold mb-3 mt-4">B. Right to Access</h3>
                        <p>Request a copy of personal information we maintain about you.</p>

                        <h3 className="text-xl font-semibold mb-3 mt-4">C. Right to Delete</h3>
                        <p>Request deletion of your personal information, subject to legal exceptions.</p>

                        <h3 className="text-xl font-semibold mb-3 mt-4">D. Right to Correct</h3>
                        <p>Request correction of inaccurate personal information.</p>

                        <h3 className="text-xl font-semibold mb-3 mt-4">E. Right to Limit Use of Sensitive Personal Information</h3>
                        <p>We do not use sensitive personal information beyond what is necessary to provide services.</p>

                        <h3 className="text-xl font-semibold mb-3 mt-4">F. Right to Non-Discrimination</h3>
                        <p>We will not discriminate against you for exercising your privacy rights.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">7. How to Submit a Request</h2>
                        <p className="mb-4">To exercise your California privacy rights, please contact:</p>
                        <p className="mb-4">
                            Email: <a href="mailto:info@simhpc.com" className="text-blue-600 dark:text-blue-400 font-bold hover:underline">info@simhpc.com</a>
                        </p>
                        <p>Subject Line: "California Privacy Request"</p>
                        <p className="mt-4">We may verify your identity before fulfilling your request.</p>
                        <p className="mt-2">Authorized agents may submit requests on behalf of a California resident with proper documentation.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">8. Verification Process</h2>
                        <p className="mb-4">To protect your privacy, we may request:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Confirmation of email address</li>
                            <li>Verification of account ownership</li>
                            <li>Additional identity verification if necessary</li>
                        </ul>
                        <p className="mt-4">We will respond within the timeframe required by California law.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">9. Do Not Track Signals</h2>
                        <p className="mb-4">Some browsers transmit "Do Not Track" signals.</p>
                        <p>SimHPC does not currently respond differently to such signals due to lack of standardized implementation.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">10. Updates to This Notice</h2>
                        <p>We may update this California Privacy Notice from time to time. The "Last Updated" date reflects the most recent revision.</p>
                    </section>
                </div>
            </div>
        </PageLayout>
    );
}
