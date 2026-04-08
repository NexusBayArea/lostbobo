export default async function handler(req, res) {
  const BASE_URL = process.env.RUNPOD_API_URL || "https://40n3yh92ugakps-8000.proxy.runpod.net";

  const path = req.query.path?.join("/") || "";
  const url = `${BASE_URL}/${path}`;

  try {
    const response = await fetch(url, {
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
  } catch (err) {
    res.status(500).json({ error: "proxy_failed" });
  }
}
