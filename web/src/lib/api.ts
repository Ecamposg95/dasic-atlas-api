// Wrapper de fetch para llamadas al backend FastAPI.
// Same-origin en prod; Vite dev proxea /api → :8000 (cookie se preserva).

const BASE_URL = '';

export type ApiError = {
  status: number;
  detail: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE_URL}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    const err: ApiError = {
      status: r.status,
      detail: (detail as { detail?: string }).detail ?? r.statusText,
    };
    throw err;
  }
  if (r.status === 204) return undefined as T;
  return r.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
