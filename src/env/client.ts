import { frontendSchema } from './schema';

const parsed = frontendSchema.safeParse(import.meta.env);

export const env = parsed.success ? parsed.data : {
  VITE_SUPABASE_URL: '',
  VITE_SUPABASE_ANON: '',
  VITE_API_URL: '',
};

if (!parsed.success) {
  console.warn('⚠️ Environment variables not set at build time. They must be available at runtime.');
}
