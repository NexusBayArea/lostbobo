import { useEffect, useState, useCallback, createContext, useContext, ReactNode } from 'react';
import { supabase } from '@/lib/supabase';
import { User, Session } from '@supabase/supabase-js';
import { api } from '@/lib/api';

export type UserTier = 'free' | 'professional' | 'enterprise' | 'demo_general' | 'demo_full';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  userTier: UserTier;
  loading: boolean;
  getToken: () => string | null;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [userTier, setUserTier] = useState<UserTier>('free');
  const [loading, setLoading] = useState(true);

  const refreshTier = useCallback(async (_token: string) => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      setUserTier((user?.user_metadata?.plan as UserTier) || 'free');
    } catch (error) {
      console.error('Failed to refresh user tier:', error);
    }
  }, []);

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.access_token) {
        refreshTier(session.access_token);
      }
      setLoading(false);
    });

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

  return (
    <AuthContext.Provider value={{ user, session, userTier, loading, getToken, signInWithGoogle, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      session: null,
      userTier: 'free' as UserTier,
      loading: true,
      getToken: () => null,
      signInWithGoogle: async () => {},
      signOut: async () => {},
    };
  }
  return context;
}