let cachedUrl: string | null = null;
let lastFetch = 0;

const CACHE_TTL = 60_000; // 60s
const MAX_RETRIES = 5;

async function sleep(ms: number) {
  return new Promise(res => setTimeout(res, ms));
}

async function getRunpodUrl() {
  // cache to avoid hitting RunPod API every request
  if (cachedUrl && Date.now() - lastFetch < CACHE_TTL) {
    return cachedUrl;
  }

  const res = await fetch("https://api.runpod.io/graphql", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.RUNPOD_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: `
        query {
          myself {
            pods {
              id
              name
              runtime {
                ports {
                  ip
                  publicPort
                }
              }
            }
          }
        }
      `,
    }),
  });

  const json = await res.json();

  const pods = json?.data?.myself?.pods || [];

  if (!pods.length) {
    throw new Error("NO_PODS");
  }

  // Filter by name or pick the first one
  const pod = pods.find(
    (p: any) => p.name === process.env.RUNPOD_POD_NAME
  ) || pods[0];

  const port = pod.runtime.ports.find(
    (p: any) => p.publicPort === 8888
  );

  if (!port) {
    throw new Error("PORT_NOT_READY");
  }

  cachedUrl = `https://${port.ip}-${port.publicPort}.proxy.runpod.net`;
  lastFetch = Date.now();

  return cachedUrl;
}

async function fetchWithRetry(url: string, options: any) {
  let attempt = 0;

  while (attempt < MAX_RETRIES) {
    try {
      const res = await fetch(url, options);

      if (res.ok) return res;

      // Retry on 5xx (Gateway errors, cold starts)
      if (res.status >= 500) {
        throw new Error(`SERVER_${res.status}`);
      }

      return res; // 4xx -> don't retry (client error)
    } catch (err: any) {
      attempt++;
      const delay = Math.min(1000 * 2 ** attempt, 8000);
      console.log(`[Proxy] Retry ${attempt}/${MAX_RETRIES} in ${delay}ms: ${err.message}`);
      await sleep(delay);
    }
  }

  throw new Error("MAX_RETRIES_EXCEEDED");
}

export default async function handler(req, res) {
  try {
    const path = req.query.path?.join("/") || "";
    let baseUrl;

    // Resolve pod with retry for cold starts
    for (let i = 0; i < 3; i++) {
      try {
        baseUrl = await getRunpodUrl();
        break;
      } catch (err: any) {
        if (err.message === "NO_PODS" || err.message === "PORT_NOT_READY") {
          console.log(`[Proxy] Pod not ready, attempt ${i+1}/3...`);
          await sleep(2000 * (i + 1));
          continue;
        }
        throw err;
      }
    }

    if (!baseUrl) {
      return res.status(503).json({
        error: "no_active_pods",
        message: "RunPod fleet is currently offline or starting up. Please retry in a few moments.",
      });
    }

    const url = `${baseUrl}/${path}`;

    const response = await fetchWithRetry(url, {
      method: req.method,
      headers: {
        "Content-Type": "application/json",
        Authorization: req.headers.authorization || "",
      },
      body:
        req.method !== "GET" && req.method !== "HEAD"
          ? JSON.stringify(req.body)
          : undefined,
    });

    const text = await response.text();
    res.status(response.status).send(text);

  } catch (err: any) {
    console.error("[Proxy Error]:", err.message);

    res.status(500).json({
      error: "proxy_failed",
      message: err.message,
    });
  }
}
