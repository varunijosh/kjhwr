// Empty base = same origin (Docker/Heroku, or Vite dev proxy).
// For a separate frontend deploy (e.g. Vercel), set VITE_API_URL.
const BASE = import.meta.env.VITE_API_URL || "";

export async function api(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = (await res.json()).detail || msg; } catch { /* ignore */ }
    throw new Error(msg);
  }
  return res.json();
}

export const fmtMW = (v) => (v == null ? "-" : `${Math.round(v).toLocaleString("en-GB")} MW`);
export const fmtTime = (iso) =>
  new Date(iso).toLocaleString("en-GB", { timeZone: "Europe/London", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
export const hhmm = (iso) =>
  new Date(iso).toLocaleTimeString("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit" });
