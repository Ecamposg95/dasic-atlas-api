import { useState } from 'react';
import { Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
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

  return (
    <div className="app-frame flex items-center justify-center bg-background text-foreground p-6">
      <div
        role="alert"
        className="max-w-md w-full rounded-md border border-border bg-card p-6 text-center space-y-3"
      >
        <Lock className="h-8 w-8 mx-auto text-muted-foreground" aria-hidden="true" />
        <h1 className="text-base font-semibold">Acceso suspendido</h1>
        <p className="text-sm text-muted-foreground whitespace-pre-line">{mensaje}</p>
        <p className="text-xs text-muted-foreground">
          Tu información está resguardada y no se ha modificado.
        </p>
        {sigue && (
          <p className="text-xs text-muted-foreground" aria-live="polite">
            El acceso sigue suspendido.
          </p>
        )}
        <div className="flex gap-2 justify-center pt-1">
          <Button type="button" size="sm" disabled={verificando} onClick={() => void reintentar()}>
            {verificando ? 'Verificando…' : 'Reintentar'}
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={() => void cerrarSesion()}>
            Cerrar sesión
          </Button>
        </div>
      </div>
    </div>
  );
}
