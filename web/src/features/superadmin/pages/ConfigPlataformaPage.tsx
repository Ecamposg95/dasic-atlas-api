import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SlidersHorizontal, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/lib/toast';
import { useIsSuperadmin } from '@/lib/permissions';
import { useConfigPlataforma, useSetConfigPlataforma, type ConfigItem } from '../hooks/useConfigPlataforma';

const LABELS: Record<string, string> = {
  iva_rate: 'IVA (proporción, ej. 0.16 = 16%)',
  quote_validity_days: 'Vigencia de cotización (días)',
};

function Row({ item }: { item: ConfigItem }) {
  const [val, setVal] = useState(String(item.valor_efectivo));
  const set = useSetConfigPlataforma();
  return (
    <div className="flex items-end gap-3 flex-wrap border-b border-slate-100 dark:border-slate-800 py-3">
      <div className="flex-1 min-w-[200px]">
        <label className="block text-xs text-slate-500 mb-1">{LABELS[item.clave] ?? item.clave}</label>
        <Input value={val} onChange={(e) => setVal(e.target.value)} className="max-w-[200px]" />
        <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
          Default: {item.default}{' '}
          {item.overrideado ? (
            <Badge variant="cyan">override activo</Badge>
          ) : (
            <Badge variant="slate">usando default</Badge>
          )}
        </div>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={set.isPending}
          onClick={() =>
            set.mutate(
              { clave: item.clave, valor: val.trim() },
              {
                onSuccess: () => toast({ kind: 'success', title: 'Configuración guardada' }),
                onError: (e) => {
                  if (e.status === 401) {
                    window.location.href = '/spa/login';
                    return;
                  }
                  toast({ kind: 'error', title: 'No se pudo guardar', description: e.detail });
                },
              },
            )
          }
        >
          Guardar
        </Button>
        {item.overrideado && (
          <Button
            size="sm"
            variant="ghost"
            disabled={set.isPending}
            onClick={() =>
              set.mutate(
                { clave: item.clave, valor: null },
                {
                  onSuccess: () => {
                    toast({ kind: 'success', title: 'Restaurado al default' });
                    setVal(String(item.default));
                  },
                },
              )
            }
          >
            Restaurar default
          </Button>
        )}
      </div>
    </div>
  );
}

export function ConfigPlataformaPage() {
  const navigate = useNavigate();
  const isSuper = useIsSuperadmin();
  const { data, isLoading } = useConfigPlataforma();
  if (!isSuper) return <div className="p-6 text-sm text-slate-500">Solo el super-administrador.</div>;
  return (
    <div className="p-6 max-w-3xl mx-auto space-y-4">
      <header className="flex items-center justify-between gap-2 flex-wrap">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <SlidersHorizontal className="h-5 w-5 text-accent-glow" /> Configuración de plataforma
        </h1>
        <Button variant="ghost" size="sm" onClick={() => navigate('/spa/superadmin')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Volver
        </Button>
      </header>
      <p className="text-sm text-slate-500">Cambios aplican sin redeploy. Afectan cotizaciones nuevas.</p>
      {isLoading ? (
        <p className="text-sm text-slate-400">Cargando…</p>
      ) : (
        (data?.items ?? []).map((it) => <Row key={it.clave} item={it} />)
      )}
    </div>
  );
}
