import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/lib/supabase';
import { Loader2 } from 'lucide-react';

export const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // 1. Listen for the moment Supabase successfully processes the URL hash
    const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' || session) {
        // Token is secured, redirect to mission control
        navigate('/dashboard', { replace: true });
      }
    });

    // 2. Fallback check: If the session was processed instantly before the listener caught it
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        navigate('/dashboard', { replace: true });
      }
    });

    // Cleanup listener on unmount
    return () => {
      authListener.subscription.unsubscribe();
    };
  }, [navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
        <p className="text-slate-600 dark:text-slate-400 font-medium animate-pulse">
          Securing authentication tokens...
        </p>
      </div>
    </div>
  );
};
