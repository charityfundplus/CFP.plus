// CFP+ website/app read-only API client (ES module). Configure API origin through reviewed deployment.
export async function getEntity(id, apiBase = "") {
  if (!/^[0-9]{1,32}$/.test(String(id))) throw new Error("Invalid numeric ID");
  const res = await fetch(apiBase + "/api/entities/" + encodeURIComponent(id), {
    headers: { Accept: "application/json" },
    credentials: "omit"
  });
  if (!res.ok) throw new Error("Entity lookup failed: " + res.status);
  return res.json();
}
// Never put privileged CFP_API_TOKEN in browser or mobile client code.
// Consent-based event capture requires a separate authenticated user-facing gateway.
