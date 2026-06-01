import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Truck, Plus, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/lib/toast';
import {
  useRemisionBorrador,
  useCrearRemision,
  useOrdenesRemisionables,
} from '../hooks/useRemisiones';
import { AgregarLineaFantasmaModal } from '../components/AgregarLineaFantasmaModal';
import type { RemisionLineaEdit } from '../types';

export function CrearRemisionPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const ordenParam = params.get('orden');
  const ordenId = ordenParam ? parseInt(ordenParam, 10) : null;

  const { data: borrador, isLoading } = useRemisionBorrador(ordenId);
  const { data: ordenes } = useOrdenesRemisionables();
  const crear = useCrearRemision();

  const [lineas, setLineas] = useState<RemisionLineaEdit[]>([]);
  const [mostrarPrecios, setMostrarPrecios] = useState(false);
  const [transportista, setTransportista] = useState('');
  const [observaciones, setObservaciones] = useState('');
  const [modalFantasma, setModalFantasma] = useState(false);

  // Precargar las líneas cuando llega el borrador.
  useEffect(() => {
    if (!borrador) return;
    setLineas(
      borrador.lineas.map((l) => ({
        detalle_orden_id: l.detalle_orden_id,
        incluir: true,
        descripcion: l.descripcion,
        sku: l.sku,
        clave_unidad_sat: l.clave_unidad_sat,
        precio_unitario: l.precio_unitario,
        cantidad: l.cantidad_orden,
        cantidad_max: l.cantidad_orden,
        observaciones_linea: '',
      })),
    );
  }, [borrador]);

  const incluidas = useMemo(() => lineas.filter((l) => l.incluir && l.cantidad > 0), [lineas]);

  function updateLinea(idx: number, patch: Partial<RemisionLineaEdit>) {
    setLineas((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }

  function onGuardar() {
    if (!ordenId) { toast({ kind: 'warning', title: 'Selecciona una orden primero' }); return; }
    if (incluidas.length === 0) { toast({ kind: 'warning', title: 'Incluye al menos una línea' }); return; }
    crear.mutate(
      {
        orden_venta_id: ordenId,
        transportista: transportista.trim() || null,
        observaciones: observaciones.trim() || null,
        mostrar_precios: mostrarPrecios,
        detalles: incluidas.map((l) => ({
          detalle_orden_id: l.detalle_orden_id,
          descripcion: l.descripcion,
          sku: l.sku,
          cantidad: l.cantidad,
          observaciones_linea: l.observaciones_linea || null,
          clave_unidad_sat: l.clave_unidad_sat,
          precio_unitario: l.detalle_orden_id == null ? l.precio_unitario : null,
        })),
      },
      {
        onSuccess: (r) => {
          toast({ kind: 'success', title: `Remisión ${r.folio} creada` });
          window.open(`/api/remisiones/${r.id}/imprimir`, '_blank');
          navigate('/spa/remisiones');
        },
        onError: (e) => {
          const err = e as unknown as { status?: number; detail?: string };
          if (err.status === 401) { window.location.href = '/spa/login'; return; }
          toast({ kind: 'error', title: 'No se pudo crear', description: err.detail });
        },
      },
    );
  }

  // Sin orden seleccionada → selector de orden.
  if (!ordenId) {
    return (
      <div className="p-6 max-w-3xl mx-auto space-y-4">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Truck className="h-5 w-5 text-cyan-400" /> Nueva remisión
        </h1>
        <p className="text-sm text-slate-500">Selecciona la orden de venta a remisionar:</p>
        <div className="border border-slate-200 dark:border-slate-800 rounded-md divide-y divide-slate-100 dark:divide-slate-800">
          {(ordenes ?? []).map((o) => (
            <button
              key={o.id}
              type="button"
              onClick={() => navigate(`/spa/remisiones-nueva?orden=${o.id}`)}
              className="w-full text-left px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center justify-between"
            >
              <span className="font-mono text-sm text-accent-glow">{o.folio}</span>
              <span className="text-xs text-slate-500">{o.cliente ?? ''}</span>
            </button>
          ))}
          {(ordenes ?? []).length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-slate-500">No hay órdenes de venta remisionables.</div>
          )}
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <div className="p-6 text-sm text-slate-500">Cargando orden…</div>;
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Truck className="h-5 w-5 text-cyan-400" /> Nueva remisión
        </h1>
        <Button variant="ghost" size="sm" onClick={() => navigate('/spa/remisiones')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Volver
        </Button>
      </div>

      {borrador && (
        <div className="text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md px-4 py-2">
          <span className="font-mono text-accent-glow">{borrador.orden_folio}</span>
          {borrador.cliente_nombre && <span className="ml-3 text-slate-500">{borrador.cliente_nombre}</span>}
          {borrador.moneda && <span className="ml-3 text-slate-500">{borrador.moneda}</span>}
        </div>
      )}

      <div className="border border-slate-200 dark:border-slate-800 rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 dark:bg-slate-800 text-xs uppercase text-slate-500">
            <tr>
              <th className="p-2 text-center w-10">Incl.</th>
              <th className="p-2 text-left">Descripción</th>
              <th className="p-2 text-center w-28">Cantidad</th>
              <th className="p-2 text-left">Observaciones</th>
            </tr>
          </thead>
          <tbody>
            {lineas.map((l, idx) => (
              <tr key={idx} className="border-t border-slate-100 dark:border-slate-800">
                <td className="p-2 text-center">
                  <input type="checkbox" checked={l.incluir} onChange={(e) => updateLinea(idx, { incluir: e.target.checked })} />
                </td>
                <td className="p-2">
                  <div className="text-slate-800 dark:text-slate-200">{l.descripcion}</div>
                  {l.sku && <div className="text-[11px] font-mono text-slate-500">{l.sku}</div>}
                </td>
                <td className="p-2 text-center">
                  <Input
                    type="number"
                    min="1"
                    max={l.cantidad_max ?? undefined}
                    value={l.cantidad}
                    onChange={(e) => {
                      const v = parseInt(e.target.value, 10) || 0;
                      const capped = l.cantidad_max != null ? Math.min(v, l.cantidad_max) : v;
                      updateLinea(idx, { cantidad: Math.max(0, capped) });
                    }}
                    className="h-8 text-xs text-center w-20 inline-block"
                  />
                  {l.cantidad_max != null && <div className="text-[10px] text-slate-400">de {l.cantidad_max}</div>}
                </td>
                <td className="p-2">
                  <Input
                    value={l.observaciones_linea}
                    onChange={(e) => updateLinea(idx, { observaciones_linea: e.target.value })}
                    className="h-8 text-xs"
                    placeholder="Nota de la línea"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Button variant="outline" size="sm" onClick={() => setModalFantasma(true)}>
        <Plus className="h-4 w-4 mr-1" /> Agregar fantasma
      </Button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Transportista</label>
          <Input value={transportista} onChange={(e) => setTransportista(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Observaciones generales</label>
          <Input value={observaciones} onChange={(e) => setObservaciones(e.target.value)} />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={mostrarPrecios} onChange={(e) => setMostrarPrecios(e.target.checked)} />
        Mostrar precios en el PDF
      </label>

      <div className="flex justify-end">
        <Button size="sm" onClick={onGuardar} disabled={crear.isPending}>
          {crear.isPending ? 'Guardando…' : 'Generar remisión'}
        </Button>
      </div>

      <AgregarLineaFantasmaModal
        open={modalFantasma}
        onClose={() => setModalFantasma(false)}
        onAdd={(linea) => setLineas((prev) => [...prev, linea])}
      />
    </div>
  );
}
