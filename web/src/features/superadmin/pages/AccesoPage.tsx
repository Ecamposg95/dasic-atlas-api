import { useEffect, useState } from 'react';
import { Lock, Unlock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/lib/toast';
import { QueryError } from '@/components/ui/query-error';
import { PlatformShell } from '../components/PlatformShell';
import { useAcceso, useSetAcceso, type AccesoCambio, type AccesoEstado } from '../hooks/useAcceso';

const MENSAJE_MAX = 500;

function fechaLegible(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' });
}

function Panel({ estado }: { estado: AccesoEstado }) {
  const set = useSetAcceso();
  const [mensaje, setMensaje] = useState(estado.mensaje_personalizado ? estado.mensaje : '');
  const [confirmando, setConfirmando] = useState(false);

  // Si el servidor devuelve otro mensaje (p.ej. tras guardar), el borrador lo sigue.
  useEffect(() => {
    setMensaje(estado.mensaje_personalizado ? estado.mensaje : '');
  }, [estado.mensaje, estado.mensaje_personalizado]);

  const guardado = estado.mensaje_personalizado ? estado.mensaje : '';
  const mensajeCambio = mensaje.trim() !== guardado;
  const cuando = fechaLegible(estado.actualizado_en);

  function enviar(cambio: AccesoCambio, exito: string) {
    set.mutate(cambio, {
      onSuccess: () => {
        setConfirmando(false);
        toast({ kind: 'success', title: exito });
      },
      onError: (e) => {
        if (e.status === 401) {
          window.location.href = '/spa/login';
          return;
        }
        toast({ kind: 'error', title: 'No se pudo aplicar el cambio', description: e.detail });
      },
    });
  }

  return (
    <div className="space-y-6">
      {/* ── Estado actual ───────────────────────────────────────────────── */}
      <div
        className="rounded-xl border border-emerald-500/20 bg-card p-4 flex items-start gap-4 flex-wrap"
        aria-live="polite"
      >
        {estado.suspendida ? (
          <Lock className="h-6 w-6 text-muted-foreground mt-0.5" aria-hidden="true" />
        ) : (
          <Unlock className="h-6 w-6 text-emerald-400 mt-0.5" aria-hidden="true" />
        )}
        <div className="flex-1 min-w-[220px]">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm font-semibold text-foreground">
              {estado.suspendida ? 'Acceso suspendido' : 'Acceso activo'}
            </span>
            {estado.suspendida ? (
              <Badge variant="slate">nadie puede entrar</Badge>
            ) : (
              <Badge variant="emerald">operando normal</Badge>
            )}
          </div>
          <p className="font-mono text-[11px] text-muted-foreground mt-1">
            {estado.suspendida
              ? `${estado.usuarios_afectados} usuario(s) activos bloqueados. Tú, como super-administrador, sigues entrando.`
              : `${estado.usuarios_afectados} usuario(s) activos con acceso.`}
          </p>
          {cuando && (
            <p className="font-mono text-[10px] text-muted-foreground mt-1">
              Último cambio: {cuando}
              {estado.actualizado_por ? ` · ${estado.actualizado_por}` : ''}
            </p>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          {estado.suspendida ? (
            <Button
              type="button"
              size="sm"
              disabled={set.isPending}
              onClick={() => enviar({ suspendida: false }, 'Acceso reactivado')}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              Reactivar acceso
            </Button>
          ) : confirmando ? (
            <>
              <Button
                type="button"
                size="sm"
                variant="destructive"
                disabled={set.isPending}
                onClick={() =>
                  enviar({ suspendida: true, mensaje: mensaje.trim() }, 'Acceso suspendido')
                }
              >
                Sí, suspender ahora
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                disabled={set.isPending}
                onClick={() => setConfirmando(false)}
              >
                Cancelar
              </Button>
            </>
          ) : (
            <Button type="button" size="sm" variant="outline" onClick={() => setConfirmando(true)}>
              Suspender acceso
            </Button>
          )}
        </div>
      </div>

      {confirmando && !estado.suspendida && (
        <p role="alert" className="font-mono text-[11px] text-muted-foreground">
          Al confirmar, las {estado.usuarios_afectados} cuenta(s) quedan fuera de inmediato,
          incluidas las sesiones abiertas. No se borra ni se modifica ningún dato.
        </p>
      )}

      {/* ── Mensaje ─────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-emerald-500/20 bg-card p-4 space-y-2">
        <label htmlFor="acceso-mensaje" className="block font-mono text-[11px] text-muted-foreground">
          Mensaje que ve el usuario mientras está suspendido
        </label>
        <Textarea
          id="acceso-mensaje"
          value={mensaje}
          maxLength={MENSAJE_MAX}
          onChange={(e) => setMensaje(e.target.value)}
          placeholder={estado.mensaje_default}
          className="font-mono text-sm border-emerald-500/20 focus-visible:ring-emerald-500"
        />
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <span className="font-mono text-[10px] text-muted-foreground">
            {mensaje.trim() ? `${mensaje.trim().length}/${MENSAJE_MAX}` : 'Vacío = se usa el mensaje genérico.'}
          </span>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            disabled={set.isPending || !mensajeCambio}
            onClick={() =>
              enviar({ suspendida: estado.suspendida, mensaje: mensaje.trim() }, 'Mensaje guardado')
            }
            className="text-muted-foreground hover:text-foreground"
          >
            Guardar mensaje
          </Button>
        </div>
      </div>
    </div>
  );
}

export function AccesoPage() {
  const { data, isLoading, isError, error, refetch } = useAcceso();

  return (
    <PlatformShell title="Acceso a la plataforma">
      <div className="max-w-2xl">
        <p className="font-mono text-[11px] text-muted-foreground mb-6">
          Suspende o reactiva el acceso de todas las cuentas que no son super-administrador.
          Aplica al instante y sin redeploy; los datos no se tocan.
        </p>
        {isLoading ? (
          <p className="font-mono text-sm text-muted-foreground">Cargando estado…</p>
        ) : isError || !data ? (
          <QueryError error={error} onRetry={() => void refetch()} />
        ) : (
          <Panel estado={data} />
        )}
      </div>
    </PlatformShell>
  );
}
