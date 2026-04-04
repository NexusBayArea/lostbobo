import { frontendSchema, fullSchema } from '../src/env/schema';

const ENV = process.env.APP_ENV || 'dev';

console.log(`\n🔍 Validating environment: ${ENV}\n`);

if (ENV === 'prod') {
  const result = fullSchema.safeParse(process.env);
  if (!result.success) {
    console.error('❌ Full env validation failed:\n');
    console.error(result.error.format());
    process.exit(1);
  }
  console.log('✅ Full env valid (prod)');
} else {
  const result = frontendSchema.safeParse(process.env);
  if (!result.success) {
    console.error('❌ Frontend env validation failed:\n');
    console.error(result.error.format());
    process.exit(1);
  }
  console.log('✅ Frontend env valid');
}
