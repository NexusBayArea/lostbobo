import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/lib/supabase';
import { toast } from 'sonner';

export function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleAuth = async () => {
      // 1. Manually exchange the code if it's a code-flow (optional, but good)
      // 2. Just let Supabase client handle the fragment
      const { data, error } = await supabase.auth.getSession();

      if (error) {
        toast.error(error.message);
        navigate('/signin');
        return;
      }

      if (data.session) {
        navigate('/dashboard', { replace: true });
      } else {
        // Fallback: wait a moment for the subscription to fire
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
          if (event === 'SIGNED_IN' || session) {
            navigate('/dashboard', { replace: true });
          }
        });
        return () => subscription.unsubscribe();
      }
    };

    handleAuth();
  }, [navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-xl font-semibold">Authenticating...</h2>
      </div>
    </div>
  );
}
