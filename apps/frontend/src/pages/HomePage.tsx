import { Link } from 'react-router-dom';
import { Navigation } from '@/components/Navigation';
import { Hero } from '@/sections/Hero';
import { Stack } from '@/sections/Stack';
import { ValueDifferentiator } from '@/sections/ValueDifferentiator';
import { WhoItsFor } from '@/sections/WhoItsFor';
import { Pricing } from '@/sections/Pricing';
import { Footer } from '@/sections/Footer';

function HomePage() {
  return (
    <>
      <Navigation />
      <main>
        <Hero />
        <Stack />
        <ValueDifferentiator />
        <WhoItsFor />
        <Pricing />
      </main>
      <Footer />
    </>
  );
}

function Terms() {
  return (
    <div className="min-h-screen bg-slate-950 pt-24 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-6">Terms of Service</h1>
        <div className="prose prose-invert text-slate-400">
          <p>Last updated: April 2026</p>
          <p>By using SimHPC, you agree to these terms. SimHPC provides AI-powered Monte Carlo simulation services for engineering and research purposes.</p>
        </div>
        <Link to="/" className="text-cyan-400 hover:text-cyan-300 mt-8 inline-block">← Back to Home</Link>
      </div>
    </div>
  );
}

function Privacy() {
  return (
    <div className="min-h-screen bg-slate-950 pt-24 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-6">Privacy Policy</h1>
        <div className="prose prose-invert text-slate-400">
          <p>Last updated: April 2026</p>
          <p>SimHPC respects your privacy. We collect minimal data necessary to provide our simulation services.</p>
        </div>
        <Link to="/" className="text-cyan-400 hover:text-cyan-300 mt-8 inline-block">← Back to Home</Link>
      </div>
    </div>
  );
}

export { HomePage, Terms, Privacy };
