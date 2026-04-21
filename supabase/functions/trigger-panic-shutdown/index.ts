import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const FOUNDER_EMAIL = "arche@simhpc.com";

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
      Deno.env.get("SB_URL") ?? "",
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
      Deno.env.get("SB_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const runpodApiKey = Deno.env.get("RUNPOD_API_KEY");
    if (!runpodApiKey) throw new Error("RUNPOD_API_KEY not configured");

    const report: string[] = [];

    // 1. Fetch all RunPod pods
    const podsRes = await fetch("https://api.runpod.io/graphql", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${runpodApiKey}`,
      },
      body: JSON.stringify({
        query: "{ myself { pods { id status } } }",
      }),
    });

    const podsData = await podsRes.json();
    const pods = podsData?.data?.myself?.pods ?? [];

    // 2. Terminate all pods
    let terminatedCount = 0;
    for (const pod of pods) {
      try {
        const termRes = await fetch("https://api.runpod.io/graphql", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${runpodApiKey}`,
          },
          body: JSON.stringify({
            query: `mutation { terminatePod(input: { podId: "${pod.id}" }) { id } }`,
          }),
        });
        const termData = await termRes.json();
        if (termData.errors) {
          report.push(`⚠️ Failed to terminate ${pod.id}: ${JSON.stringify(termData.errors)}`);
        } else {
          report.push(`🛑 Terminated Pod: ${pod.id}`);
          terminatedCount++;
        }
      } catch (e) {
        report.push(`⚠️ Error terminating ${pod.id}: ${(e as Error).message}`);
      }
    }

    // 3. Log to platform_alerts
    await supabaseAdmin.from("platform_alerts").insert({
      type: "system",
      severity: "critical",
      message: `🚨 GLOBAL PANIC TRIGGERED: ${terminatedCount} compute resources terminated by Admin.`,
      metadata: { terminated_count: terminatedCount, total_pods: pods.length },
    });

    return new Response(
      JSON.stringify({
        success: true,
        terminated_count: terminatedCount,
        total_pods: pods.length,
        report,
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
