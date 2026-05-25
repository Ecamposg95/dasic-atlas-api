// Wrapper de fetch para llamadas al backend FastAPI.
// Same-origin en prod; Vite dev proxea /api → :8000 (cookie se preserva).

const BASE_URL = '';

export type ApiError = {
  status: number;
  detail: string;
};

// FastAPI 422 manda `detail` como array de objetos Pydantic v2
// {type, loc, msg, input, ctx}. Si lo dejamos como objeto crudo y un
// componente lo pinta como children de React → error #31.
function normalizeDetail(detail: unknown, fallback: string): string {
  if (detail == null) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        if (typeof e === 'string') return e;
        if (e && typeof e === 'object') {
          const obj = e as { msg?: unknown; loc?: unknown };
          const msg = typeof obj.msg === 'string' ? obj.msg : '';
          const loc = Array.isArray(obj.loc)
            ? obj.loc.filter((p) => p !== 'body').join('.')
            : '';
          if (msg) return loc ? `${loc}: ${msg}` : msg;
          return JSON.stringify(e);
        }
        return String(e);
      })
      .join(' · ');
  }
  if (typeof detail === 'object') {
    const obj = detail as { msg?: unknown };
    if (typeof obj.msg === 'string') return obj.msg;
    return JSON.stringify(detail);
  }
  return String(detail);
}

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
    const body = await r.json().catch(() => ({}));
    const err: ApiError = {
      status: r.status,
      detail: normalizeDetail((body as { detail?: unknown }).detail, r.statusText),
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
