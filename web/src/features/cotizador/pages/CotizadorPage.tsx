import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FileText } from 'lucide-react';
import { HeaderCotizacion } from '../components/HeaderCotizacion';
import { ProductSearch } from '../components/ProductSearch';
import { Cart } from '../components/Cart';
import { TotalsBar } from '../components/TotalsBar';
import { EditLineModal } from '../components/EditLineModal';
import { useCotizador } from '../store';
import { useCotizacionLoader } from '../hooks/useCotizacion';

export function CotizadorPage() {
  const [params] = useSearchParams();
  const editId = params.get('edit');
  const editIdNum = editId ? parseInt(editId, 10) : null;

  const reset = useCotizador((s) => s.reset);
  const hydrateFromOrden = useCotizador((s) => s.hydrateFromOrden);
  const editingFolio = useCotizador((s) => s.editingFolio);
  const editingId = useCotizador((s) => s.editingId);
  const editingEstatus = useCotizador((s) => s.editingEstatus);
  const observaciones = useCotizador((s) => s.observaciones);
  const setObservaciones = useCotizador((s) => s.setObservaciones);
  const terminos = useCotizador((s) => s.terminos_condiciones);
  const setTerminos = useCotizador((s) => s.setTerminos);

  const { data: orden, isLoading, error } = useCotizacionLoader(editIdNum);

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
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-4">
        <header className="flex items-center justify-between gap-2 flex-wrap">
          <h1 className="text-2xl font-semibold">
            {editingId ? 'Editar cotización' : 'Nueva cotización'}
          </h1>
          <div className="flex items-center gap-2">
            {editingFolio && (
              <span className="text-sm bg-amber-900/30 text-amber-300 border border-amber-700/50 px-3 py-1 rounded">
                Editando <strong className="font-mono">{editingFolio}</strong>
              </span>
            )}
            {editingId != null && (
              <a
                href={`/api/ventas/${editingId}/pdf`}
                target="_blank"
                rel="noreferrer"
                className="text-xs px-3 py-1 rounded border border-slate-700 hover:border-accent-glow text-slate-300 hover:text-accent-glow transition flex items-center gap-1"
              >
                <FileText className="h-3.5 w-3.5" /> Ver PDF
              </a>
            )}
          </div>
        </header>

        {isLoading && editIdNum != null && (
          <div className="text-sm text-slate-400 bg-slate-900 border border-slate-800 rounded p-4">
            Cargando cotización #{editIdNum}…
          </div>
        )}

        {noEditable && (
          <div className="text-sm bg-rose-900/20 border border-rose-700/50 text-rose-300 rounded p-3">
            Esta orden ya no es editable (estatus <code>{editingEstatus}</code>). El botón Guardar está deshabilitado.
          </div>
        )}

        <HeaderCotizacion />

        <div>
          <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
            Agregar producto
          </label>
          <ProductSearch />
        </div>

        <Cart />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
              Observaciones
            </label>
            <textarea
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              rows={4}
              placeholder="Notas internas o para el cliente…"
              className="w-full text-sm rounded-md border border-slate-700 bg-slate-900 px-3 py-2 focus:border-accent-glow outline-none"
            />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">
              Términos y condiciones
            </label>
            <textarea
              value={terminos}
              onChange={(e) => setTerminos(e.target.value)}
              rows={4}
              placeholder="Una línea por cláusula. Vacío → usa los defaults del backend."
              className="w-full text-sm rounded-md border border-slate-700 bg-slate-900 px-3 py-2 focus:border-accent-glow outline-none"
            />
          </div>
        </div>
      </div>

      <TotalsBar />
      <EditLineModal />
    </div>
  );
}
