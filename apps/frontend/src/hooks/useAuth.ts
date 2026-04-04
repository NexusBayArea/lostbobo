import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import type { User } from '@supabase/supabase-js';

const FOUNDER_EMAIL = 'arche@simhpc.com';

interface AuthState {
  user: User | null;
  loading: boolean;
  isLoading: boolean;
  isAdmin: boolean;
  getToken: () => Promise<string>;
}

export function useAuth(): AuthState {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  const isAdmin =
    user?.app_metadata?.role === 'admin' || user?.email === FOUNDER_EMAIL;

  const getToken = async (): Promise<string> => {
    if (!supabase) return '';
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? '';
  };

  return { user, loading, isLoading: loading, isAdmin, getToken };
}
