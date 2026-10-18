import type { HealthResponse } from "./types";

/** GET /api/health. Returns null when the server is unreachable instead of throwing. */
export async function getHealth(signal?: AbortSignal): Promise<HealthResponse | null> {
  try {
    const r = await fetch("/api/health", { signal });
    return r.ok ? ((await r.json()) as HealthResponse) : null;
  } catch {
    return null;
  }
}
