import { createClient } from '@supabase/supabase-js';

// PASTE your real credentials here:
const supabaseUrl = "https://ldzztrnghaaonparyggz.supabase.co";
const supabaseKey = "sb_publishable_BTPKB2cbCifXpkENl43thw_dxio3DkO";

export const supabase = createClient(supabaseUrl, supabaseKey);

export async function signInWithGoogle() {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin + '/dashboard',
    },
  });
  if (error) console.error("Login failed:", error.message);
}
