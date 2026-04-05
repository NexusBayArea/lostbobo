import LegalLayout from './LegalLayout';

export default function Cookies() {
  return (
    <LegalLayout title="Cookie Policy">
      <p>SimHPC uses "Session Cookies" to keep you logged in and "Functional Cookies" to save your simulation parameters between sessions.</p>
      <ul className="list-disc pl-5 space-y-2">
        <li><strong>Auth Cookie:</strong> Manages your secure session via Supabase.</li>
        <li><strong>Preference Cookie:</strong> Remembers if you prefer Dark Mode or Light Mode.</li>
        <li><strong>Stripe Cookie:</strong> Necessary for secure checkout and subscription management.</li>
      </ul>
      <section>
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200 mt-6">Managing Cookies</h2>
        <p>You can control cookies through your browser settings. Disabling cookies may affect your ability to use certain features of SimHPC.</p>
      </section>
      <section>
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-200">Third-Party Cookies</h2>
        <p>We do not allow third-party advertising cookies. Only essential service cookies from Supabase and Stripe are used.</p>
      </section>
    </LegalLayout>
  );
}
