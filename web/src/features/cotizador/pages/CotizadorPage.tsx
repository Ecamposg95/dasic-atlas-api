import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { HeaderCotizacion } from '../components/HeaderCotizacion';
import { useCotizador } from '../store';

export function CotizadorPage() {
  const [params] = useSearchParams();
  const editId = params.get('edit');
  const reset = useCotizador((s) => s.reset);
  const editingFolio = useCotizador((s) => s.editingFolio);
  const editingId = useCotizador((s) => s.editingId);

  useEffect(() => {
    // Al desmontar la página, limpiamos el store para que la próxima visita
    // arranque limpia.
    return () => reset();
  }, [reset]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">
          {editingId ? 'Editar cotización' : 'Nueva cotización'}
        </h1>
        {editingFolio && (
          <span className="text-sm bg-amber-900/30 text-amber-300 border border-amber-700/50 px-3 py-1 rounded">
            Editando <strong className="font-mono">{editingFolio}</strong>
          </span>
        )}
      </header>

      <HeaderCotizacion />

      {/* Phase 1b: ProductSearch + Cart + TotalsBar irán aquí */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500">
        <p className="text-sm">
          {editId
            ? `Modo edit (id=${editId}). Phase 1b agregará carga y carrito.`
            : 'Carrito y búsqueda de productos llegan en Phase 1b.'}
        </p>
      </div>
    </div>
  );
}
