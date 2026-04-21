import { useState, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/hooks/useAuth';

export const useOnboarding = () => {
  const { user } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);

  const startOnboarding = useCallback(async () => {
    if (!user) return;
    setIsProcessing(true);

    try {
      const { data, error } = await supabase.rpc('gift_signup_bonus', {
        target_user_id: user.id
      });

      if (error) throw error;

      return { success: true, creditsAdded: 10, demoRunId: data.run_id };

    } catch (err) {
      console.error('Onboarding failed:', err);
      return { success: false, error: err };
    } finally {
      setIsProcessing(false);
    }
  }, [user]);

  return { startOnboarding, isProcessing };
};
