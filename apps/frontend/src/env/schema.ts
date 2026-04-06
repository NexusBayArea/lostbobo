import { z } from 'zod';

export const frontendSchema = z.object({
  VITE_SUPABASE_URL: z.string().optional().default(''),
  VITE_SUPABASE_ANON: z.string().optional().default(''),
  VITE_SUPABASE_ANON_KEY: z.string().optional().default(''),
  SUPABASE_URL: z.string().optional().default(''),
  SUPABASE_ANON_KEY: z.string().optional().default(''),
  VITE_API_URL: z.string().optional().default(''),
});

export const backendSchema = z.object({
  REDIS_URL: z.string().min(5),
  RUNPOD_API_KEY: z.string().min(10),
  SUPABASE_SERVICE_ROLE_KEY: z.string().min(10),
});

export const fullSchema = frontendSchema.merge(backendSchema);
