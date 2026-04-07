import { motion } from 'framer-motion';
import { PageLayout } from '@/components/PageLayout';

const sections = [
  {
    title: '1. Agreement to Terms',
    content: `These Terms of Service ("Terms") govern access to and use of the SimHPC platform, including:
• Web application
• Simulation infrastructure
• APIs
• Robustness analysis engine
• AI-generated reporting tools

By using the Platform, you agree to these Terms on behalf of yourself and/or your organization.`,
  },
  {
    title: '2. Description of Services',
    content: `SimHPC provides a cloud-hosted computational platform offering:
• GPU-accelerated finite element simulation
• Time integration solvers
• Automated parameter perturbation and sensitivity analysis
• Confidence interval computation
• Structured AI-generated technical summaries

The Platform is a computational analysis tool only.

SimHPC does not provide:
• Licensed engineering services
• Regulatory certification
• Safety validation
• Physical system approval

All outputs require independent professional validation.`,
  },
  {
    title: '3. Commercial Use',
    content: `The Platform is intended for professional, commercial, and research use.

You represent that:
• You are authorized to bind your organization
• You will comply with all applicable laws
• You will not use the Platform for unlawful or prohibited applications`,
  },
  {
    title: '4. Export Control Compliance',
    content: `You agree not to use the Platform in violation of U.S. export control laws, including but not limited to:
• International Traffic in Arms Regulations (ITAR)
• Export Administration Regulations (EAR)

You are responsible for determining whether uploaded data is subject to export restrictions.

SimHPC does not guarantee ITAR compliance unless expressly contracted.`,
  },
  {
    title: '5. Account Responsibility',
    content: `You are responsible for:
• Account credentials
• All activity under your account
• Accuracy of input data

Unauthorized access must be reported immediately.`,
  },
  {
    title: '6. Data Ownership',
    content: `You retain ownership of:
• Uploaded models
• Simulation inputs
• Simulation outputs

SimHPC claims no ownership of customer engineering IP.`,
  },
  {
    title: '7. Limited Data Usage',
    content: `SimHPC may collect and use anonymized, aggregated system performance metadata for:
• Infrastructure optimization
• Runtime prediction modeling
• GPU allocation efficiency
• Solver reliability monitoring

We will not use identifiable simulation content for model training or commercial reuse without explicit written consent.`,
  },
  {
    title: '8. AI-Generated Reporting Disclaimer',
    content: `AI-generated summaries:
• Are interpretive in nature
• Are derived from structured simulation outputs
• May contain inaccuracies or incomplete interpretations
• Do not replace licensed engineering review

Users must independently validate engineering conclusions before real-world implementation.`,
  },
  {
    title: '9. No Warranty; Limitation of Liability',
    content: `The Platform is provided "AS IS" and "AS AVAILABLE."

To the maximum extent permitted under Delaware law:

SimHPC disclaims all warranties including:
• Merchantability
• Fitness for a particular purpose
• Non-infringement

SimHPC shall not be liable for:
• Engineering failures
• Manufacturing losses
• Regulatory penalties
• Lost profits
• Consequential or indirect damages

Total liability shall not exceed fees paid in the preceding 12 months.`,
  },
  {
    title: '10. Indemnification',
    content: `You agree to indemnify and hold harmless SimHPC against claims arising from:
• Misuse of simulation outputs
• Violation of export laws
• Unauthorized use of the Platform
• Deployment of simulated systems without validation`,
  },
  {
    title: '11. Payment & Suspension',
    content: `Failure to pay fees may result in:
• Suspension of compute access
• Data retention limitations
• Account termination

Fees are non-refundable unless required by law.`,
  },
  {
    title: '12. Termination',
    content: `Either party may terminate at any time.

Upon termination:
• Access is revoked
• Data retention policies apply
• Outstanding fees remain due`,
  },
  {
    title: '13. Governing Law & Venue',
    content: `These Terms are governed by the laws of the State of Delaware.

Any disputes shall be resolved in state or federal courts located in Delaware.

Effective Date: January 1, 2025
Company: SimHPC, Inc., a Delaware corporation ("SimHPC", "Company", "we", "us", "our")
Principal Place of Business: California, United States`,
  },
];

export function Terms() {
  return (
    <PageLayout>
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 dark:text-white mb-4">
              Terms of Service
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mb-12 text-lg">
              Effective Date: January 1, 2025
            </p>

            <div className="space-y-12">
              {sections.map((section, index) => (
                <motion.section
                  key={section.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.05 }}
                >
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                    {section.title}
                  </h2>
                  <div className="text-slate-600 dark:text-slate-400 whitespace-pre-line leading-relaxed text-lg">
                    {section.content}
                  </div>
                </motion.section>
              ))}
            </div>

            {/* Contact */}
            <div className="mt-16 pt-8 border-t border-slate-200 dark:border-slate-800">
              <p className="text-slate-600 dark:text-slate-400 text-lg">
                Questions about these Terms? Contact us at{' '}
                <a href="mailto:info@simhpc.com" className="text-blue-600 dark:text-blue-400 font-bold hover:underline">
                  info@simhpc.com
                </a>
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </PageLayout>
  );
}
