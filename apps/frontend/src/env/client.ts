import { frontendSchema } from './schema';

const parsed = frontendSchema.safeParse(import.meta.env);

export const env = parsed.success ? parsed.data : {
  VITE_SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL || import.meta.env.SUPABASE_URL || '',
  VITE_SUPABASE_ANON: import.meta.env.VITE_SUPABASE_ANON || import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.SUPABASE_ANON_KEY || '',
  VITE_API_URL: import.meta.env.VITE_API_URL || '',
};

if (!parsed.success) {
  console.warn('⚠️ Environment variables failed validation. Check VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, and VITE_API_URL.');
}
