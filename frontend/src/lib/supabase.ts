import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SB_URL;
const supabaseAnonKey = import.meta.env.VITE_SB_PUB_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error("Supabase environment variables are missing.");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export async function signInWithGoogle() {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin + '/dashboard',
    },
  });
  if (error) console.error("Login failed:", error.message);
}