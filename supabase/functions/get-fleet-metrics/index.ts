import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

// v2.5.0 Configuration
const RUNPOD_HOURLY_RATE = 0.44; // e.g., RTX 3090 pricing
const JOBS_PER_POD = 2; // Matches your worker's MAX_CONCURRENT_JOBS

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // 1. Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // 2. Initialize Supabase Client
    const supabaseClient = createClient(
      Deno.env.get('SB_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    )

    // 3. Verify the user making the request is logged in
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser()
    if (authError || !user) throw new Error('Unauthorized')

    // 4. Verify Admin Status
    const isAdmin = user.app_metadata?.role === 'admin' || user.email === 'nexusbayarea@gmail.com'
    if (!isAdmin) {
      return new Response(JSON.stringify({ error: 'Forbidden: Admin access required' }), {
        status: 403,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // 5. Query the simulation_history table for active jobs
    const supabaseAdmin = createClient(
      Deno.env.get('SB_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { count, error: dbError } = await supabaseAdmin
      .from('simulation_history')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'processing')

    if (dbError) throw dbError

    const activeSims = count || 0
    
    // 6. Calculate the Fleet Metrics
    const activeRunPods = Math.ceil(activeSims / JOBS_PER_POD)
    const hourlySpend = (activeRunPods * RUNPOD_HOURLY_RATE).toFixed(2)

    return new Response(
      JSON.stringify({ 
        active_simulations: activeSims,
        active_pods: activeRunPods,
        hourly_spend_usd: hourlySpend,
        timestamp: new Date().toISOString()
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
    )

  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
