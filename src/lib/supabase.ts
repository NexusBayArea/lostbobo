import { createClient } from '@supabase/supabase-js';
import { env } from '../env/client';

export const supabase = env.VITE_SUPABASE_URL && env.VITE_SUPABASE_ANON
  ? createClient(env.VITE_SUPABASE_URL, env.VITE_SUPABASE_ANON)
  : null;
