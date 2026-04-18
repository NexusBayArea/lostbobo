import { useEffect, useState, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { User, Session } from '@supabase/supabase-js';
import { api } from '@/lib/api';

export type UserTier = 'free' | 'professional' | 'enterprise' | 'demo_general' | 'demo_full';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [userTier, setUserTier] = useState<UserTier>('free');
  const [loading, setLoading] = useState(true);

  const refreshTier = useCallback(async (_token: string) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      // Assuming plan is stored in user_metadata or similar; adapt to your schema
      setUserTier((user?.user_metadata?.plan as UserTier) || 'free');
    } catch (error) {
      console.error('Failed to refresh user tier:', error);
    }
  }, []);

  useEffect(() => {
    // Check active sessions
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.access_token) {
        refreshTier(session.access_token);
      }
      setLoading(false);
    });

    // Listen for changes (login/logout)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.access_token) {
        refreshTier(session.access_token);
      } else {
        setUserTier('free');
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, [refreshTier]);

  const getToken = () => session?.access_token;

  return { user, session, userTier, loading, getToken, refreshTier };
}
