import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RUNPOD_HOURLY_RATE = 0.44;
const JOBS_PER_POD = 2;
const FOUNDER_EMAIL = "arche@simhpc.com";
const USAGE_THRESHOLD = 10.00;

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      {
        global: {
          headers: { Authorization: req.headers.get("Authorization")! },
        },
      }
    );

    const {
      data: { user },
      error: authError,
    } = await supabaseClient.auth.getUser();
    if (authError || !user) throw new Error("Unauthorized");

    const isAdmin =
      user.app_metadata?.role === "admin" ||
      user.email === FOUNDER_EMAIL;
    if (!isAdmin) {
      return new Response(
        JSON.stringify({ error: "Forbidden: Admin access required" }),
        {
          status: 403,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const supabaseAdmin = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const { count: activeCount, error: activeError } = await supabaseAdmin
      .from("simulations")
      .select("*", { count: "exact", head: true })
      .in("status", ["running", "processing"]);

    if (activeError) throw activeError;

    const { count: queuedCount, error: queuedError } = await supabaseAdmin
      .from("simulations")
      .select("*", { count: "exact", head: true })
      .eq("status", "queued");

    if (queuedError) throw queuedError;

    const activeSims = activeCount || 0;
    const queuedSims = queuedCount || 0;
    const activeRunPods = Math.ceil(activeSims / JOBS_PER_POD);
    const hourlySpend = (activeRunPods * RUNPOD_HOURLY_RATE).toFixed(2);

    // Billing alert: check if spend exceeds threshold and no recent alert exists
    if (parseFloat(hourlySpend) > USAGE_THRESHOLD) {
      const oneHourAgo = new Date(Date.now() - 3600000).toISOString();
      const { data: existingAlert } = await supabaseAdmin
        .from("platform_alerts")
        .select("id")
        .eq("type", "billing")
        .gt("created_at", oneHourAgo)
        .limit(1);

      if (!existingAlert || existingAlert.length === 0) {
        await supabaseAdmin.from("platform_alerts").insert({
          type: "billing",
          severity: "critical",
          message: `Usage Alert: Current burn rate is $${hourlySpend}/hr, exceeding the $${USAGE_THRESHOLD} limit.`,
          metadata: { hourly_spend: hourlySpend, active_pods: activeRunPods },
        });
      }
    }

    return new Response(
      JSON.stringify({
        active_simulations: activeSims,
        queued_simulations: queuedSims,
        active_pods: activeRunPods,
        hourly_spend_usd: hourlySpend,
        timestamp: new Date().toISOString(),
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    return new Response(JSON.stringify({ error: (error as Error).message }), {
      status: 400,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
