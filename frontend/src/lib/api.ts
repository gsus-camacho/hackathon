/**
 * BioAlert+ API client utilities.
 * Server-side fetches use INTERNAL_BACKEND_URL (loopback, fast).
 * Browser-side fetches use PUBLIC_BACKEND_URL (ingress).
 *
 * Includes an in-memory SSR cache (per Astro process) to avoid re-fetching
 * heavy aggregations on every page render.
 */

import { demoFallback, demoPostFallback, demoDeleteFallback } from "./demo";

export const PUBLIC_BACKEND_URL =
  import.meta.env.PUBLIC_BACKEND_URL || "http://localhost:8000";

const INTERNAL_BACKEND_URL =
  import.meta.env.INTERNAL_BACKEND_URL || "http://localhost:8000";

interface CacheEntry { value: any; expires: number; promise?: Promise<any>; }
const ssrCache = new Map<string, CacheEntry>();
const DEFAULT_TTL_MS = 45_000;

function safeJson(res: Response) {
  return res.json().catch(() => ({}));
}

/** Use from .astro server side. Caches successful responses for `ttlMs`. */
export async function serverGet<T = any>(
  path: string,
  ttlMs: number = DEFAULT_TTL_MS
): Promise<T> {
  const now = Date.now();
  const key = `GET ${path}`;
  const cached = ssrCache.get(key);
  if (cached && cached.expires > now) {
    if (cached.promise) return cached.promise as Promise<T>;
    return cached.value as T;
  }

  const url = `${INTERNAL_BACKEND_URL}/api${path}`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 90_000);
  const promise = (async () => {
    try {
      const res = await fetch(url, {
        signal: ctrl.signal,
        headers: { "content-type": "application/json" },
      });
      if (!res.ok) {
        throw new Error(`GET ${path} -> ${res.status}`);
      }
      const data = await res.json();
      ssrCache.set(key, { value: data, expires: Date.now() + ttlMs });
      return data as T;
    } finally {
      clearTimeout(t);
    }
  })();

  ssrCache.set(key, { value: undefined, expires: now + ttlMs, promise });
  try {
    return await promise;
  } catch (e) {
    ssrCache.delete(key);
    return demoFallback(path) as T;
  }
}

export async function serverPost<T = any>(
  path: string,
  body: any
): Promise<T> {
  const url = `${INTERNAL_BACKEND_URL}/api${path}`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error(`POST ${path} -> ${res.status}`);
    }
    return res.json();
  } catch {
    return demoPostFallback(path, body) as T;
  }
}

export async function clientGet<T = any>(apiBase: string, path: string): Promise<T> {
  const url = `${apiBase}/api${path}`;
  try {
    const res = await fetch(url, {
      headers: { "content-type": "application/json" },
    });
    if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
    return await res.json();
  } catch {
    return demoFallback(path) as T;
  }
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function clientPost<T = any>(apiBase: string, path: string, body?: any): Promise<T> {
  const url = `${apiBase}/api${path}`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new ApiError(text || `POST ${path} -> ${res.status}`, res.status);
    }
    return await res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    return demoPostFallback(path, body) as T;
  }
}

export async function clientDelete<T = any>(apiBase: string, path: string): Promise<T> {
  const url = `${apiBase}/api${path}`;
  try {
    const res = await fetch(url, { method: "DELETE" });
    if (!res.ok) throw new Error(`DELETE ${path} -> ${res.status}`);
    return await safeJson(res);
  } catch {
    return demoDeleteFallback(path) as T;
  }
}

export function clientApiUrl(path: string): string {
  return `${PUBLIC_BACKEND_URL}/api${path}`;
}

export function formatCurrency(value: number | string | null | undefined): string {
  const n = Number(value || 0);
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatNumber(value: number | string | null | undefined): string {
  const n = Number(value || 0);
  return new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 }).format(n);
}
