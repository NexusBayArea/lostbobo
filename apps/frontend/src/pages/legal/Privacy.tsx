import LegalLayout from './LegalLayout';

export default function Privacy() {
  return (
    <LegalLayout title="Privacy Policy">
      <section>
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">1. Data Sovereignty</h2>
        <p>Your simulation data and infrastructure secrets (handled via <strong>Infisical</strong>) belong to you. We do not sell or trade your personal information.</p>
      </section>
      <section>
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">2. Security Architecture</h2>
        <p>We use industry-standard encryption. Authentication is handled by <strong>Supabase</strong>, and payment processing is secured by <strong>Stripe</strong>.</p>
      </section>
      <section>
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">3. Data Collection</h2>
        <p>We collect only the data necessary to provide our services: account information, simulation parameters, and usage telemetry. No personal data is shared with third parties.</p>
      </section>
      <section>
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">4. Data Retention</h2>
        <p>Simulation data and notebook entries are retained until you delete them or close your account. Upon account deletion, all associated data is permanently removed within 30 days.</p>
      </section>
      <section>
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">5. Your Rights</h2>
        <p>You have the right to access, export, modify, or delete your data at any time through your account settings or by contacting support.</p>
      </section>
    </LegalLayout>
  );
}
