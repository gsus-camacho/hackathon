/**
 * BioAlert+ API client utilities.
 * Server-side fetches use INTERNAL_BACKEND_URL (loopback, fast).
 * Browser-side fetches use PUBLIC_BACKEND_URL (ingress).
 */

export const PUBLIC_BACKEND_URL =
  import.meta.env.PUBLIC_BACKEND_URL || "";

const INTERNAL_BACKEND_URL =
  import.meta.env.INTERNAL_BACKEND_URL || "http://localhost:8001";

/** Use from .astro server side. */
export async function serverGet<T = any>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = `${INTERNAL_BACKEND_URL}/api${path}`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 90000);
  try {
    const res = await fetch(url, {
      ...init,
      signal: ctrl.signal,
      headers: { "content-type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) {
      throw new Error(`GET ${path} -> ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(t);
  }
}

export async function serverPost<T = any>(
  path: string,
  body: any
): Promise<T> {
  const url = `${INTERNAL_BACKEND_URL}/api${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST ${path} -> ${res.status}`);
  }
  return res.json();
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
