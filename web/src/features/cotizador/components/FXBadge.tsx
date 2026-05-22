import { RefreshCw } from 'lucide-react';
import { useFX, useFXRefresh } from '../hooks/useFX';
import { toast } from '@/lib/toast';
import { useCotizador } from '../store';
import type { ApiError } from '@/lib/api';

export function FXBadge() {
  const { data, isLoading } = useFX();
  const refresh = useFXRefresh();
  const setTc = useCotizador((s) => s.setTc);

  if (isLoading || !data) {
    return <span className="text-[10px] text-slate-500">Cargando TC…</span>;
  }

  // `usd_mxn` puede venir como string por la serialización Decimal de Pydantic.
  const tcNum = Number(data.usd_mxn);

  async function onClick() {
    try {
      const r = await refresh.mutateAsync();
      const nuevoTc = Number(r.usd_mxn);
      if (Number.isFinite(nuevoTc) && nuevoTc > 0) {
        setTc(nuevoTc);
        toast({
          kind: 'success',
          title: 'TC actualizado',
          description: `${r.fuente}: $${nuevoTc.toFixed(4)} (${r.fecha})`,
        });
      }
    } catch (e) {
      const err = e as ApiError;
      toast({
        kind: 'error',
        title: 'No se pudo refrescar',
        description: err.detail,
      });
    }
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={refresh.isPending}
      className="text-[10px] flex items-center gap-1 text-slate-400 hover:text-accent-glow transition disabled:opacity-50"
      title={`Fuente: ${data.fuente}. Click para refrescar y aplicar al TC de la cotización.`}
    >
      <RefreshCw className={`h-2.5 w-2.5 ${refresh.isPending ? 'animate-spin' : ''}`} />
      <span>
        TC oficial: <strong className="text-slate-200">${tcNum.toFixed(4)}</strong> (
        {data.fecha} · {data.fuente})
      </span>
    </button>
  );
}
