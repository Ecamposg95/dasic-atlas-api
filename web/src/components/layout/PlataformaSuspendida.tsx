import { useState } from 'react';
import { AtlasLockup, AtlasMark, ATLAS_URL } from '@/components/brand/Atlas';
import { api } from '@/lib/api';
import { useAuth, type User } from '@/stores/auth';
import { useSuspension } from '@/stores/suspension';

// Pantalla que tapa toda la app cuando el backend responde 423 (acceso
// suspendido desde la consola de plataforma). No es un error ni una sesión
// caducada: la cuenta sigue ahí y vuelve tal cual cuando se reactiva.
export function PlataformaSuspendida({ mensaje }: { mensaje: string }) {
  const setUser = useAuth((s) => s.setUser);
  const limpiar = useSuspension((s) => s.limpiar);
  const [verificando, setVerificando] = useState(false);
  const [sigue, setSigue] = useState(false);

  async function reintentar() {
    if (verificando) return;
    setVerificando(true);
    setSigue(false);
    try {
      const me = await api.get<User>('/api/auth/me');
      setUser(me);
      limpiar();
    } catch (e) {
      const status = (e as { status?: number }).status;
      if (status === 401 || status === 403) {
        // La sesión caducó mientras tanto: al login, sin la pantalla encima.
        limpiar();
        setUser(null);
        window.location.assign('/');
        return;
      }
      setSigue(true);
    } finally {
      setVerificando(false);
    }
  }

  async function cerrarSesion() {
    try {
      await api.post('/api/auth/logout');
    } catch {
      // Aunque falle el POST, salimos igual.
    }
    limpiar();
    setUser(null);
    window.location.assign('/');
  }

  const pill =
    'rounded-full px-5 py-2 text-sm font-medium transition-colors disabled:opacity-60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[3px] focus-visible:outline-atlas-amber';

  // Pantalla de Atlas Tech (modo Horizon), igual en tema claro y oscuro: quien
  // suspende es la plataforma, no la empresa cliente.
  return (
    <div className="app-frame relative isolate overflow-hidden flex flex-col bg-atlas-black text-atlas-ink">
      {/* Horizonte: única composición de luz, detrás del contenido */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -z-10 left-1/2 -translate-x-1/2 top-[76%] h-[900px] w-[2600px] rounded-[50%] border-t-2 border-[#FFB27A]"
        style={{
          boxShadow: '0 -6px 40px rgba(255,140,60,.9), 0 -30px 140px rgba(255,106,31,.55)',
          background:
            'radial-gradient(50% 30% at 50% 0%, rgba(255,140,60,.55), rgba(122,36,10,.35) 45%, rgba(5,5,5,0) 75%)',
        }}
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -z-10 -top-40 -right-40 h-[520px] w-[820px] rounded-full blur-3xl"
        style={{ background: 'radial-gradient(50% 50% at 50% 50%, rgba(91,88,184,.40), rgba(91,88,184,0))' }}
      />

      <header className="flex items-center justify-between px-6 sm:px-10 pt-7">
        <AtlasLockup name="ONE" className="text-xl" markClassName="h-6" />
        <a
          href={ATLAS_URL}
          target="_blank"
          rel="noreferrer"
          className="rounded-full border border-white/15 bg-white/[0.03] px-4 py-1.5 text-xs text-atlas-ink hover:border-white/30 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[3px] focus-visible:outline-atlas-amber"
        >
          atlastech.mx
        </a>
      </header>

      <main className="flex-1 flex items-center justify-center px-6 pb-[18vh]">
        <div role="alert" className="w-full max-w-xl text-center">
          <p className="text-[11px] uppercase tracking-[0.24em] text-[#8A837B]">Estado de la plataforma</p>
          <h1 className="mt-4 text-4xl sm:text-6xl font-light leading-none tracking-[-0.035em]">
            Acceso <span className="text-atlas-ember">suspendido.</span>
          </h1>
          <p className="mt-6 text-base sm:text-lg font-light text-[#A8A29A] whitespace-pre-line">{mensaje}</p>
          <p className="mt-3 text-sm text-[#8A837B]">Tu información está resguardada y no se ha modificado.</p>
          <div className="mt-8 flex flex-wrap gap-3 justify-center">
            <button
              type="button"
              disabled={verificando}
              onClick={() => void reintentar()}
              className={`${pill} bg-atlas-ink text-atlas-black hover:bg-white`}
            >
              {verificando ? 'Verificando…' : 'Reintentar'}
            </button>
            <button
              type="button"
              onClick={() => void cerrarSesion()}
              className={`${pill} border border-white/15 bg-white/[0.03] text-atlas-ink hover:border-white/30`}
            >
              Cerrar sesión
            </button>
          </div>
          <p className="mt-4 min-h-[1.25rem] text-sm text-[#A8A29A]" aria-live="polite">
            {sigue ? 'El acceso sigue suspendido.' : ''}
          </p>
        </div>
      </main>

      <footer className="flex items-center justify-between px-6 sm:px-10 pb-6 text-[11px] uppercase tracking-[0.2em] text-[rgba(255,220,190,.7)]">
        <span className="inline-flex items-center gap-2">
          <AtlasMark className="h-3.5" />
          Atlas Tech
        </span>
        <span className="font-mono normal-case tracking-normal">Atlas ONE</span>
      </footer>
    </div>
  );
}
