import { createClient } from '@supabase/supabase-js';

const supabaseUrl =
  (import.meta.env.VITE_SUPABASE_URL as string | undefined) ||
  (import.meta.env.SUPABASE_URL as string | undefined) ||
  '';

const supabaseAnonKey =
  (import.meta.env.VITE_SUPABASE_ANON as string | undefined) ||
  (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined) ||
  (import.meta.env.SUPABASE_ANON_KEY as string | undefined) ||
  '';

export const supabase =
  supabaseUrl.length > 0 && supabaseAnonKey.length > 0
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null;

if (!supabase) {
  console.error('Supabase client not initialized. Ensure VITE_SUPABASE_URL (or SUPABASE_URL) and VITE_SUPABASE_ANON (or VITE_SUPABASE_ANON_KEY or SUPABASE_ANON_KEY) are set in your environment.');
}
