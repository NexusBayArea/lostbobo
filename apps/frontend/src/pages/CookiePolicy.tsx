import { PageLayout } from '@/components/PageLayout';
import { Cookie } from 'lucide-react';

export function CookiePolicy() {
    return (
        <PageLayout>
            <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-6 text-slate-900 dark:text-white">Cookie Policy</h1>
                <p className="text-slate-600 dark:text-slate-400 mb-8">
                    Effective Date: 3/3/2026
                </p>
                
                <div className="space-y-8 text-slate-800 dark:text-slate-200">
                    <section>
                        <h2 className="text-2xl font-semibold mb-4">1. Overview</h2>
                        <p className="mb-4">
                            SimHPC ("we", "our", "us") uses cookies and similar technologies to operate, secure, and improve our platform.
                        </p>
                        <p className="mb-4">This Cookie Policy explains:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>What cookies are</li>
                            <li>What types we use</li>
                            <li>Why we use them</li>
                            <li>How you can control them</li>
                        </ul>
                        <p className="mt-4">
                            By using our website or services, you consent to the use of cookies as described below.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">2. What Are Cookies?</h2>
                        <p className="mb-4">
                            Cookies are small text files placed on your device when you visit a website.
                        </p>
                        <p className="mb-4">They allow websites to:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Recognize your device</li>
                            <li>Store session information</li>
                            <li>Remember preferences</li>
                            <li>Improve performance and security</li>
                        </ul>
                        <p className="mt-4">
                            Cookies do not give us access to your computer or personal files.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">3. Types of Cookies We Use</h2>
                        
                        <h3 className="text-xl font-semibold mb-3 mt-6">A. Essential Cookies (Required)</h3>
                        <p className="mb-4">These cookies are necessary for the website to function. They enable:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Account login and authentication</li>
                            <li>Secure session management</li>
                            <li>API access control</li>
                            <li>Load balancing</li>
                            <li>Security and fraud prevention</li>
                        </ul>
                        <p className="mt-4">Without these cookies, the platform cannot operate properly.</p>

                        <h3 className="text-xl font-semibold mb-3 mt-6">B. Authentication Cookies</h3>
                        <p className="mb-4">Used when you:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Sign up with email</li>
                            <li>Sign in with Google</li>
                            <li>Access protected dashboards</li>
                        </ul>
                        <p className="mt-4">These cookies:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Maintain your login session</li>
                            <li>Secure authenticated requests</li>
                            <li>Prevent unauthorized access</li>
                        </ul>

                        <h3 className="text-xl font-semibold mb-3 mt-6">C. Payment Processing Cookies</h3>
                        <p className="mb-4">
                            When you subscribe or manage billing, Stripe may place cookies necessary for:
                        </p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Fraud prevention</li>
                            <li>Payment authentication</li>
                            <li>Subscription management</li>
                        </ul>
                        <p className="mt-4">We do not store your credit card details on our servers.</p>

                        <h3 className="text-xl font-semibold mb-3 mt-6">D. Analytics Cookies</h3>
                        <p className="mb-4">We may use analytics services to understand:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Page performance</li>
                            <li>Feature usage</li>
                            <li>Aggregate user behavior</li>
                        </ul>
                        <p className="mt-4">These cookies help us improve:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Reliability</li>
                            <li>User experience</li>
                            <li>Product features</li>
                        </ul>
                        <p className="mt-4">Analytics data is aggregated and not used to personally identify you.</p>

                        <h3 className="text-xl font-semibold mb-3 mt-6">E. Performance & Infrastructure Cookies</h3>
                        <p className="mb-4">Used to:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Monitor API latency</li>
                            <li>Track system reliability</li>
                            <li>Diagnose system errors</li>
                            <li>Maintain uptime targets</li>
                        </ul>
                        <p className="mt-4">These cookies support platform stability and security.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">4. Third-Party Cookies</h2>
                        <p className="mb-4">
                            Some cookies may be placed by trusted third parties, including:
                        </p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Stripe (payment processing)</li>
                            <li>Google (authentication services)</li>
                            <li>Infrastructure providers (e.g., hosting services)</li>
                            <li>Analytics providers (if enabled)</li>
                        </ul>
                        <p className="mt-4">
                            We do not control third-party cookies directly. Please refer to those providers' privacy policies for more information.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">5. How Long Cookies Remain</h2>
                        <p className="mb-4">Cookies may be:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Session-based (deleted when you close your browser)</li>
                            <li>Persistent (stored for a defined period)</li>
                        </ul>
                        <p className="mt-4">Retention depends on purpose, security requirements, and legal obligations.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">6. Managing Cookies</h2>
                        <p className="mb-4">You may control cookies through your browser settings.</p>
                        <p className="mb-4">Most browsers allow you to:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Block cookies</li>
                            <li>Delete cookies</li>
                            <li>Receive alerts when cookies are set</li>
                        </ul>
                        <p className="mt-4">
                            Disabling essential cookies may prevent you from accessing secure features or using the platform.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">7. Do Not Track Signals</h2>
                        <p className="mb-4">Some browsers transmit "Do Not Track" signals.</p>
                        <p>At this time, SimHPC does not respond differently to such signals due to lack of standardized implementation.</p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold mb-4">8. Updates to This Policy</h2>
                        <p className="mb-4">We may update this Cookie Policy to reflect changes in:</p>
                        <ul className="list-disc pl-6 space-y-2">
                            <li>Technology</li>
                            <li>Legal requirements</li>
                            <li>Platform features</li>
                        </ul>
                        <p className="mt-4">The "Last Updated" date will reflect revisions.</p>
                    </section>
                </div>
            </div>
        </PageLayout>
    );
}
