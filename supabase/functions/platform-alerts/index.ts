import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const USAGE_THRESHOLD = 10.00; 

serve(async (req) => {
  const supabaseAdmin = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  );

  const currentSpend = 12.50; // Mock current spend for alpha testing

  if (currentSpend > USAGE_THRESHOLD) {
    const oneHourAgo = new Date(Date.now() - 3600000).toISOString();
    
    const { data: existingAlert } = await supabaseAdmin
      .from('platform_alerts')
      .select('id')
      .eq('type', 'billing')
      .gt('created_at', oneHourAgo)
      .limit(1);

    if (!existingAlert || existingAlert.length === 0) {
      await supabaseAdmin.from('platform_alerts').insert({
        type: 'billing',
        severity: 'critical',
        message: `Usage Alert: Current burn rate is $${currentSpend.toFixed(2)}/hr, exceeding the $${USAGE_THRESHOLD} limit.`,
        metadata: { 
          hourly_spend: currentSpend, 
          triggered_at: new Date().toISOString()
        }
      });
    }
  }

  return new Response(JSON.stringify({ success: true, spend: currentSpend }), {
    headers: { "Content-Type": "application/json" },
  });
})
