import { Button } from '@/components/ui/button';
import { useBulkEstatus } from '../hooks/useClientes';
import { toast } from '@/lib/toast';
import { useNavigate } from 'react-router-dom';

export function BulkActionBar({ selectedIds, onClear }: { selectedIds: number[]; onClear: () => void }) {
  const bulk = useBulkEstatus();
  const navigate = useNavigate();
  if (!selectedIds.length) return null;

  const setEstatus = (estatus: string) =>
    bulk.mutate(
      { ids: selectedIds, estatus },
      {
        onSuccess: (r) => { toast({ kind: 'success', title: `${r.updated} empresa(s) → ${estatus}` }); onClear(); },
        onError: () => toast({ kind: 'error', title: 'No se pudo cambiar el estatus' }),
      },
    );

  return (
    <div className="flex items-center gap-2 rounded-lg border border-border bg-surface-2 px-3 py-2 mb-3">
      <span className="text-sm text-foreground">{selectedIds.length} seleccionada(s)</span>
      <div className="flex-1" />
      <select
        onChange={(e) => { if (e.target.value) setEstatus(e.target.value); e.target.value = ''; }}
        className="text-sm rounded-md border border-border-strong bg-card px-2 py-1"
        defaultValue=""
      >
        <option value="" disabled>Cambiar estatus…</option>
        <option value="activo">Activo</option>
        <option value="inactivo">Inactivo</option>
        <option value="prospecto">Prospecto</option>
      </select>
      <Button
        variant="secondary"
        size="sm"
        disabled={selectedIds.length < 2}
        onClick={() => navigate(`/spa/empresas-unificar?ids=${selectedIds.join(',')}`)}
      >Unificar</Button>
      <button onClick={onClear} className="text-xs text-muted-foreground hover:underline">Limpiar</button>
    </div>
  );
}
