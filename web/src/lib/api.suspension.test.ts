import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';
import { useSuspension } from '@/stores/suspension';

function responder(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(body), { status })),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  useSuspension.getState().limpiar();
});

describe('api · acceso suspendido (423)', () => {
  it('enciende el store global con el mensaje del servidor y aun así rechaza', async () => {
    responder(423, { detail: 'Servicio suspendido por falta de pago.' });

    await expect(api.get('/api/auth/me')).rejects.toMatchObject({ status: 423 });
    expect(useSuspension.getState().mensaje).toBe('Servicio suspendido por falta de pago.');
  });

  it('un 401 o un 403 no se confunden con suspensión', async () => {
    for (const status of [401, 403, 500]) {
      responder(status, { detail: 'x' });
      await expect(api.get('/api/auth/me')).rejects.toMatchObject({ status });
      expect(useSuspension.getState().mensaje).toBeNull();
    }
  });
});
