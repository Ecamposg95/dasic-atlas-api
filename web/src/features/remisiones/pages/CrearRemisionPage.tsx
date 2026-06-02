import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Truck, ArrowLeft, Package, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/lib/toast';
import { DocumentCartTable } from '@/components/document/DocumentCartTable';
import { DocumentTotalsBar } from '@/components/document/DocumentTotalsBar';
import { DocumentSectionDivider } from '@/components/document/DocumentSectionDivider';
import type { DocRowCaps, DocRowCallbacks, DocRowVM } from '@/components/document/types';
import { useRemisionBorrador, useCrearRemision, useOrdenesRemisionables } from '../hooks/useRemisiones';
import { useRemision } from '../store';
import { remisionLineaToVM } from '../lib/vm';
import { RemisionProductSearch } from '../components/RemisionProductSearch';
import { AgregarLineaFantasmaModal } from '../components/AgregarLineaFantasmaModal';

function fmtMoney(n: number, moneda: string) {
  return `${moneda} $${n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function CrearRemisionPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const ordenParam = params.get('orden');
  const ordenId = ordenParam ? parseInt(ordenParam, 10) : null;

  const { data: borrador, isLoading } = useRemisionBorrador(ordenId);
  const { data: ordenes } = useOrdenesRemisionables();
  const crear = useCrearRemision();
  const [modalFantasma, setModalFantasma] = useState(false);

  const s = useRemision();

  useEffect(() => {
    if (borrador && ordenId != null) s.hydrateFromBorrador(borrador, ordenId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [borrador, ordenId]);
  useEffect(() => () => useRemision.getState().reset(), []);

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

  if (isLoading) return <div className="p-6 text-sm text-slate-500">Cargando orden…</div>;

  const REMISION_CAPS: DocRowCaps = {
    showCosto: false,
    showUtilidad: false,
    showDescuento: false,
    showEntrega: false,
    showImporte: s.mostrarPrecios,
    editableQty: true,
  };

  const rows: DocRowVM[] = s.lineas.map((l) => remisionLineaToVM(l, s.moneda));
  const cb: DocRowCallbacks = {
    onQty: (uid, qty) => s.setQty(uid, qty),
    onRemove: (uid) => s.removeLinea(uid),
    onToggleExpand: (uid) => s.toggleExpand(uid),
  };

  const subtotal = s.lineas.reduce((acc, l) => acc + l.precio_unitario * l.cantidad, 0);
  const incluidas = s.lineas.filter((l) => l.cantidad > 0);

  function onGuardar() {
    if (incluidas.length === 0) {
      toast({ kind: 'warning', title: 'Incluye al menos una línea con cantidad > 0' });
      return;
    }
    crear.mutate(
      {
        orden_venta_id: ordenId!,
        transportista: s.transportista.trim() || null,
        observaciones: s.observaciones.trim() || null,
        mostrar_precios: s.mostrarPrecios,
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

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)]">
      <div className="flex-1 p-4 max-w-7xl mx-auto w-full space-y-3">
        <header className="flex items-center justify-between gap-2 flex-wrap">
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <Truck className="h-5 w-5 text-accent-glow" /> Nueva remisión
          </h1>
          <div className="flex items-center gap-1.5">
            {s.ordenFolio && (
              <span className="text-xs bg-cyan-900/30 text-cyan-300 border border-cyan-700/50 px-2 py-1 rounded font-mono">
                {s.ordenFolio}
              </span>
            )}
            <button
              type="button"
              onClick={() => s.setMostrarPrecios(!s.mostrarPrecios)}
              className="text-[11px] px-2 py-1 rounded border border-slate-300 dark:border-slate-700 hover:border-accent-glow text-slate-700 dark:text-slate-300 hover:text-accent-glow transition flex items-center gap-1"
            >
              {s.mostrarPrecios ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
              {s.mostrarPrecios ? 'Precios visibles' : 'Precios ocultos'}
            </button>
            <Button variant="ghost" size="sm" onClick={() => navigate('/spa/remisiones')}>
              <ArrowLeft className="h-4 w-4 mr-1" /> Volver
            </Button>
          </div>
        </header>

        {s.clienteNombre && (
          <div className="text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md px-4 py-2">
            <span className="text-slate-500">{s.clienteNombre}</span>
            <span className="ml-3 text-slate-500">{s.moneda}</span>
          </div>
        )}

        <DocumentSectionDivider icon={<Package className="h-3 w-3" />} label="Productos" />
        <RemisionProductSearch onOpenManualFantasma={() => setModalFantasma(true)} />

        <DocumentCartTable rows={rows} caps={REMISION_CAPS} cb={cb} />

        <div>
          <label className="block text-xs text-slate-500 mb-1">Transportista</label>
          <Input value={s.transportista} onChange={(e) => s.setTransportista(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Observaciones generales</label>
          <Input value={s.observaciones} onChange={(e) => s.setObservaciones(e.target.value)} />
        </div>
      </div>

      <DocumentTotalsBar
        stats={
          s.mostrarPrecios
            ? [{ label: 'Subtotal', value: fmtMoney(subtotal, s.moneda), emphasis: 'big' }]
            : [{ label: 'Líneas', value: String(incluidas.length), emphasis: 'big' }]
        }
        actions={
          <Button size="sm" onClick={onGuardar} disabled={crear.isPending}>
            {crear.isPending ? 'Guardando…' : 'Generar remisión'}
          </Button>
        }
      />

      <AgregarLineaFantasmaModal
        open={modalFantasma}
        onClose={() => setModalFantasma(false)}
        onAdd={(linea) =>
          useRemision.getState().addFantasmaManual({
            descripcion: linea.descripcion,
            sku: linea.sku,
            precio_unitario: linea.precio_unitario,
            clave_unidad_sat: linea.clave_unidad_sat,
            cantidad: linea.cantidad,
          })
        }
      />
    </div>
  );
}
