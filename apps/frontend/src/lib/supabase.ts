import { createClient } from '@supabase/supabase-js';
import { env } from '../env/client';

export const supabase =
  env.VITE_SUPABASE_URL && env.VITE_SUPABASE_URL.length > 0 &&
  env.VITE_SUPABASE_ANON && env.VITE_SUPABASE_ANON.length > 0
    ? createClient(env.VITE_SUPABASE_URL, env.VITE_SUPABASE_ANON)
    : null;
