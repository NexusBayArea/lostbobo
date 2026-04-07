import { motion } from 'framer-motion';
import { PageLayout } from '@/components/PageLayout';

const sections = [
  {
    title: '1. Scope',
    content: `This Privacy Policy explains how SimHPC collects, uses, and protects information in connection with its services.

This policy is designed to comply with:
• California Consumer Privacy Act (CCPA)
• California Privacy Rights Act (CPRA)`,
  },
  {
    title: '2. Information We Collect',
    content: `Account Information
• Name
• Email
• Company
• Billing details

Simulation Data
• Uploaded files
• Parameter inputs
• Generated outputs

Technical Usage Data
• IP address
• Device/browser metadata
• Runtime logs
• Infrastructure performance metrics`,
  },
  {
    title: '3. How We Use Information',
    content: `We use information to:
• Deliver computational services
• Generate robustness analysis
• Produce AI-generated summaries
• Improve system performance
• Prevent abuse or fraud

We do not sell personal data.`,
  },
  {
    title: '4. AI Processing',
    content: `Structured simulation outputs may be processed by third-party AI providers solely to generate technical summaries.

SimHPC:
• Does not use identifiable customer simulation data for general AI training
• Does not sell engineering IP
• Uses contractual safeguards with AI providers`,
  },
  {
    title: '5. California Privacy Rights (CPRA)',
    content: `California residents may request:
• Access to collected personal information
• Deletion of personal information
• Correction of inaccurate information

Requests may be submitted to: info@simhpc.com

We do not sell personal information.`,
  },
  {
    title: '6. Data Retention',
    content: `We retain:
• Account information while active
• Simulation data according to subscription tier
• Logs for security and operational integrity

Data deletion requests are subject to contractual and legal requirements.`,
  },
  {
    title: '7. Security',
    content: `We implement:
• Encryption in transit (TLS)
• Cloud infrastructure access controls
• Role-based authentication
• Audit logging

However, no system is completely secure.`,
  },
  {
    title: '8. International Transfers',
    content: `Data may be processed in the United States.

Users outside the U.S. acknowledge this transfer.`,
  },
  {
    title: '9. Updates',
    content: `We may update this policy periodically.

Continued use of the Platform constitutes acceptance.

Effective Date: January 1, 2025
Company: SimHPC, Inc.`,
  },
];

export function Privacy() {
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
              Privacy Policy
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
                Questions about this Privacy Policy? Contact us at{' '}
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
