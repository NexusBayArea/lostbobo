import { frontendSchema } from './schema';

const parsed = frontendSchema.safeParse(import.meta.env);

if (!parsed.success) {
  throw new Error(
    'Invalid frontend environment variables. ' +
    'Check build-time injection. ' +
    JSON.stringify(parsed.error.format(), null, 2)
  );
}

export const env = parsed.data;
