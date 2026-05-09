'use client';

import { useEffect, useState } from 'react';
import Confetti from 'react-confetti';
import { useRouter } from 'next/navigation';
import { simhpcFetch } from '@/lib/simhpc-client';

export default function BillingSuccess() {
  const router = useRouter();
  const [countdown, setCountdown] = useState(6);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          clearInterval(timer);
          router.push('/dashboard/simulation');
          return 0;
        }
        return c - 1;
      });
    }, 1000);

    // Refresh user tier from backend (Infisical-backed)
    simhpcFetch('/api/v1/user/profile')
      .then(console.log)
      .catch(console.error);

    return () => clearInterval(timer);
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-slate-950 to-black text-center px-6">
      <Confetti
        width={typeof window !== 'undefined' ? window.innerWidth : 800}
        height={typeof window !== 'undefined' ? window.innerHeight : 600}
        recycle={false}
        numberOfPieces={400}
      />

      <div className="max-w-md">
        <div className="text-6xl mb-6">🎉</div>
        <h1 className="text-5xl font-bold tracking-tight mb-4">
          Professional Tier Unlocked!
        </h1>
        <p className="text-xl text-slate-400 mb-8">
          Unlimited GPU runs • Tier 2/3 Certificates • Full Flywheel Access
        </p>

        <div className="text-sm text-slate-500 animate-pulse">
          Redirecting to Simulation Workspace in {countdown} seconds...
        </div>
      </div>
    </div>
  );
}
