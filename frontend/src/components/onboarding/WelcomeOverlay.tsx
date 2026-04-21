import React, { useEffect, useState } from 'react';
import { useOnboarding } from '@/hooks/useOnboarding';
import { useUserProfile } from '@/hooks/useUserProfile';

export const WelcomeOverlay = () => {
  const { profile, refreshProfile } = useUserProfile();
  const { startOnboarding, isProcessing } = useOnboarding();
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (profile && profile.is_new_user) {
      setShow(true);
    }
  }, [profile]);

  const handleClaim = async () => {
    const result = await startOnboarding();
    if (result?.success) {
      await refreshProfile(); 
      setShow(false);
    }
  };

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white p-8 rounded-2xl max-w-md text-center shadow-2xl border border-slate-200">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Welcome to SimHPC Beta</h2>
        <p className="text-slate-600 mb-6">
          Your account has been provisioned. We've added 10 credits to your vault to get your first physics simulation running.
        </p>
        <button 
          onClick={handleClaim}
          disabled={isProcessing}
          className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {isProcessing ? 'Provisioning Assets...' : 'Claim 10 Credits & Launch Demo'}
        </button>
      </div>
    </div>
  );
};