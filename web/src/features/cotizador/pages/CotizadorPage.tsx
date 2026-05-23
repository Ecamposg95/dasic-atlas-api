import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  FileText,
  ClipboardList,
  Download,
  Upload,
  Package,
  MessageSquare,
  FileOutput,
  Pencil,
  Truck,
} from 'lucide-react';
import { HeaderCotizacion } from '../components/HeaderCotizacion';
import { ProductSearch } from '../components/ProductSearch';
import { Cart } from '../components/Cart';
import { TotalsBar } from '../components/TotalsBar';
import { EditLineModal } from '../components/EditLineModal';
import { TabsCotizador, type CotizadorTab } from '../components/TabsCotizador';
import { HistorialTab } from '../components/HistorialTab';
import { AtajosPopover } from '../components/AtajosPopover';
import { PlantillasModal } from '../components/PlantillasModal';
import { SuggestRelacionados } from '../components/SuggestRelacionados';
import { DrawerBorradores } from '../components/DrawerBorradores';
import { PreviewOCDrawer } from '../components/PreviewOCDrawer';
import { ModalNotaLinea } from '../components/ModalNotaLinea';
import { ModalTerminos } from '../components/ModalTerminos';
import { ModalConceptoPDF } from '../components/ModalConceptoPDF';
import { ModalPisarTC } from '../components/ModalPisarTC';
import { AgregarFantasmaModal } from '../components/AgregarFantasmaModal';
import { GenerarReporteServicioModal } from '@/features/reportes_servicio_docs/components/GenerarReporteServicioModal';
import { useCotizador } from '../store';
import { useCotizacionLoader } from '../hooks/useCotizacion';
import { useAtajos, type AtajoHandler } from '../hooks/useAtajos';
import { exportBorrador, importBorrador } from '../lib/jsonExport';
import { api } from '@/lib/api';
import type { Producto } from '../types';
import { toast } from '@/lib/toast';

export function CotizadorPage() {
  const [params] = useSearchParams();
  const editId = params.get('edit');
  const editIdNum = editId ? parseInt(editId, 10) : null;
  const [tab, setTab] = useState<CotizadorTab>('editor');

  const reset = useCotizador((s) => s.reset);
  const hydrateFromOrden = useCotizador((s) => s.hydrateFromOrden);
  const editingFolio = useCotizador((s) => s.editingFolio);
  const editingId = useCotizador((s) => s.editingId);
  const editingEstatus = useCotizador((s) => s.editingEstatus);
  const cliente_id = useCotizador((s) => s.cliente_id);
  const observaciones = useCotizador((s) => s.observaciones);
  const setObservaciones = useCotizador((s) => s.setObservaciones);
  const terminos = useCotizador((s) => s.terminos_condiciones);
  const pdfConceptoEnabled = useCotizador((s) => s.pdf_concepto_enabled);
  const pdfConceptoUnificado = useCotizador((s) => s.pdf_concepto_unificado);
  const setPdfConceptoEnabled = useCotizador((s) => s.setPdfConceptoEnabled);

  const { data: orden, isLoading, error } = useCotizacionLoader(editIdNum);

  // Phase 5 (Task 5.2): Export / Import del borrador a JSON.
  // `useRef` para mantener el <input type=file> oculto que se dispara al
  // hacer click en el botón Upload.
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleExport() {
    const s = useCotizador.getState();
    const json = exportBorrador({
      cliente_id: s.cliente_id,
      moneda: s.moneda,
      tc: s.tc,
      observaciones: s.observaciones,
      terminos_condiciones: s.terminos_condiciones,
      cart: s.cart,
    });
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    a.download = `cotizacion-borrador-${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    toast({ kind: 'success', title: 'Borrador exportado', description: a.download });
  }

  async function handleImportFile(file: File) {
    let snap: ReturnType<typeof importBorrador>;
    try {
      const text = await file.text();
      snap = importBorrador(text);
    } catch (err) {
      toast({
        kind: 'error',
        title: 'No se pudo importar',
        description: (err as Error).message || 'Archivo inválido',
      });
      return;
    }
    const st = useCotizador.getState();
    st.reset();
    if (snap.cliente_id != null) st.setCliente(snap.cliente_id);
    st.setMoneda(snap.moneda);
    st.setTc(snap.tc);
    st.setObservaciones(snap.observaciones);
    st.setTerminos(snap.terminos_condiciones);

    let agregadas = 0;
    let saltadas = 0;
    for (const it of snap.cart) {
      if (it.producto_id == null) {
        saltadas += 1;
        continue;
      }
      try {
        const p = await api.get<Producto>(`/api/productos/${it.producto_id}`);
        st.addProducto(p, it.qty, it.utilidad);
        const uid = useCotizador.getState().cart.slice(-1)[0]?.uid;
        if (uid) {
          st.updateLinea(uid, {
            descuento: it.descuento,
            sku: it.sku,
            nom: it.nom,
            cost: it.cost,
            entrega_min: it.entrega_min,
            entrega_max: it.entrega_max,
            entrega_unidad: it.entrega_unidad,
            observaciones_linea: it.observaciones_linea,
          });
        }
        agregadas += 1;
      } catch {
        // Producto eliminado del catálogo o sin permisos; lo saltamos
        // sin abortar la importación.
        saltadas += 1;
      }
    }
    toast({
      kind: saltadas > 0 ? 'warning' : 'success',
      title: 'Borrador importado',
      description: `${agregadas} línea(s) cargadas${saltadas > 0 ? ` · ${saltadas} omitida(s)` : ''}`,
    });
  }

  // Atajos globales del editor. Memoizado para que el effect del hook no
  // re-suscriba en cada render.
  const atajos = useMemo<AtajoHandler[]>(() => [
    {
      combo: '/',
      description: 'Enfocar búsqueda',
      handler: () => {
        (document.querySelector('[data-cot-search]') as HTMLInputElement | null)?.focus();
      },
    },
    {
      combo: 'ctrl+s',
      description: 'Guardar cotización',
      handler: () => {
        document.querySelector<HTMLButtonElement>('[data-cot-save]')?.click();
      },
    },
    {
      combo: 'p',
      description: 'Abrir plantillas',
      handler: () => {
        window.dispatchEvent(new CustomEvent('cot:open-plantillas'));
      },
    },
    {
      combo: '?',
      description: 'Mostrar este popover',
      handler: () => {
        window.dispatchEvent(new CustomEvent('cot:open-atajos'));
      },
    },
  ], []);
  useAtajos(atajos);

  // Hydrate when the GET resolves
  useEffect(() => {
    if (orden) hydrateFromOrden(orden);
  }, [orden, hydrateFromOrden]);

  // Reset store on unmount so the next visit starts fresh
  useEffect(() => () => reset(), [reset]);

  // Auth error → bounce to login
  useEffect(() => {
    const status = (error as { status?: number } | undefined)?.status;
    if (status === 401) window.location.href = '/spa/login';
  }, [error]);

  const noEditable = !!editingEstatus && editingEstatus.toUpperCase() !== 'COTIZACION';

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)]">
      <div className="flex-1 p-4 max-w-7xl mx-auto w-full space-y-3">
        <header className="flex items-center justify-between gap-2 flex-wrap">
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5 text-accent-glow" />
            {editingId ? 'Editar cotización' : 'Nueva cotización'}
          </h1>
          <div className="flex items-center gap-1.5">
            {editingFolio && (
              <span className="text-xs bg-amber-900/30 text-amber-300 border border-amber-700/50 px-2 py-1 rounded flex items-center gap-1">
                <Pencil className="h-3 w-3" />
                <span>Editando</span>
                <strong className="font-mono">{editingFolio}</strong>
              </span>
            )}
            <button
              type="button"
              onClick={() =>
                window.dispatchEvent(new CustomEvent('cot:open-borradores'))
              }
              className="text-[11px] px-2 py-1 rounded border border-slate-700 hover:border-accent-glow text-slate-300 hover:text-accent-glow transition flex items-center gap-1"
            >
              <ClipboardList className="h-3 w-3" /> Borradores
            </button>
            <button
              type="button"
              onClick={() =>
                window.dispatchEvent(new CustomEvent('cot:open-preview-oc'))
              }
              title="Preview de OCs que nacerán al guardar"
              className="text-[11px] px-2 py-1 rounded border border-slate-700 hover:border-accent-glow text-slate-300 hover:text-accent-glow transition flex items-center gap-1"
            >
              <Truck className="h-3 w-3" /> Preview OC
            </button>
            <button
              type="button"
              onClick={handleExport}
              title="Exportar borrador a JSON"
              className="text-[11px] px-2 py-1 rounded border border-slate-700 hover:border-accent-glow text-slate-300 hover:text-accent-glow transition flex items-center gap-1"
            >
              <Download className="h-3 w-3" />
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Importar borrador desde JSON"
              className="text-[11px] px-2 py-1 rounded border border-slate-700 hover:border-accent-glow text-slate-300 hover:text-accent-glow transition flex items-center gap-1"
            >
              <Upload className="h-3 w-3" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/json"
              className="hidden"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (file) await handleImportFile(file);
                // Permite reimportar el mismo archivo si el usuario lo necesita.
                e.target.value = '';
              }}
            />
            {editingId != null && (
              <a
                href={`/api/ventas/${editingId}/pdf`}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] px-2 py-1 rounded border border-slate-700 hover:border-accent-glow text-slate-300 hover:text-accent-glow transition flex items-center gap-1"
              >
                <FileText className="h-3 w-3" /> Ver PDF
              </a>
            )}
          </div>
        </header>

        <TabsCotizador active={tab} onChange={setTab} />

        {tab === 'editor' && (
          <>
            {isLoading && editIdNum != null && (
              <div className="text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded p-3">
                Cargando cotización #{editIdNum}…
              </div>
            )}
            {noEditable && (
              <div className="text-xs bg-rose-900/20 border border-rose-700/50 text-rose-300 rounded p-2">
                Esta orden ya no es editable (estatus <code>{editingEstatus}</code>). El botón Guardar está deshabilitado.
              </div>
            )}

            <HeaderCotizacion />

            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.15em] text-slate-400 dark:text-slate-500 mt-2">
              <Package className="h-3 w-3" />
              <span>Productos</span>
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />
            </div>
            <div>
              <ProductSearch />
            </div>

            <Cart />
            <SuggestRelacionados />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.15em] text-slate-400 dark:text-slate-500 mb-1">
                  <MessageSquare className="h-3 w-3" />
                  <span>Observaciones</span>
                  <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />
                </div>
                <textarea
                  value={observaciones}
                  onChange={(e) => setObservaciones(e.target.value)}
                  rows={4}
                  placeholder="Notas internas o para el cliente…"
                  className="w-full text-xs rounded-md border border-slate-700 bg-slate-900 px-2 py-2 focus:border-accent-glow outline-none"
                />
              </div>
              <div>
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.15em] text-slate-400 dark:text-slate-500 mb-1">
                  <FileText className="h-3 w-3" />
                  <span>Términos y condiciones</span>
                  <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />
                </div>
                <button
                  type="button"
                  onClick={() =>
                    window.dispatchEvent(new CustomEvent('cot:open-terminos'))
                  }
                  className="w-full text-left text-xs rounded-md border border-slate-700 bg-slate-900 px-2 py-2 hover:border-accent-glow text-slate-300 flex items-start gap-2 min-h-[5rem]"
                >
                  <FileText className="h-3.5 w-3.5 mt-0.5 text-slate-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] text-slate-500 mb-1">
                      {terminos.split('\n').filter((l) => l.trim()).length} cláusulas · click para editar
                    </div>
                    <div className="text-[11px] text-slate-400 line-clamp-3 whitespace-pre-wrap">
                      {terminos || 'Vacío — se usarán los defaults del backend al guardar.'}
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.15em] text-slate-400 dark:text-slate-500 mt-2">
              <FileOutput className="h-3 w-3" />
              <span>PDF unificado</span>
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />
            </div>
            <div className="flex items-center gap-3 text-[11px] flex-wrap">
              <label className="flex items-center gap-2 text-slate-300">
                <input
                  type="checkbox"
                  checked={pdfConceptoEnabled}
                  onChange={(e) => setPdfConceptoEnabled(e.target.checked)}
                  className="accent-cyan-500"
                />
                PDF con concepto unificado
              </label>
              <button
                type="button"
                onClick={() =>
                  window.dispatchEvent(new CustomEvent('cot:open-concepto'))
                }
                className="text-[11px] text-accent-glow hover:underline flex items-center gap-1"
              >
                <Pencil className="h-3 w-3" /> Editar concepto…
              </button>
              {pdfConceptoEnabled && pdfConceptoUnificado && (
                <span className="text-[10px] text-slate-500 truncate max-w-md">
                  «{pdfConceptoUnificado}»
                </span>
              )}
            </div>
          </>
        )}

        {tab === 'historial' && (
          <HistorialTab clienteIdFiltro={cliente_id} />
        )}
      </div>

      {tab === 'editor' && <TotalsBar />}
      <EditLineModal />
      <PlantillasModal />
      {/* Modales/drawer Phase 4 — viven fuera del tab conditional para que sigan
          disponibles incluso si el usuario cambia a "Historial" mientras hay un
          modal abierto. La apertura es vía window events. */}
      <DrawerBorradores />
      <PreviewOCDrawer />
      <ModalNotaLinea />
      <ModalTerminos />
      <ModalConceptoPDF />
      <ModalPisarTC />
      <AgregarFantasmaModal />
      <GenerarReporteServicioModal />
      {tab === 'editor' && <AtajosPopover atajos={atajos} />}
    </div>
  );
}
