import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Shape real del backend (`app/routers/catalogos.py`):
//   GET /api/catalogos/marcas             → MarcaResponse[]
//   GET /api/catalogos/categorias-producto → { items: [{ categoria, n_productos }] }
//
// Importante: el endpoint de categorías NO devuelve `id` — son strings libres
// del campo `productos.categoria`. Por eso usamos `nombre` como identidad.

type Marca = {
  id: number;
  nombre: string;
  abreviatura: string;
  categoria: string | null;
  n_productos: number;
};

type CategoriasResponse = {
  items: Array<{ categoria: string; n_productos: number }>;
};

type Props = {
  tipo: 'producto' | 'servicio';
  onTipoChange: (t: 'producto' | 'servicio') => void;
  marcaId: number | null;
  marcaNombre: string | null;
  onMarcaChange: (id: number | null, nombre: string | null) => void;
  categoriaNombre: string | null;
  onCategoriaChange: (nombre: string | null) => void;
};

export function CatalogoFiltros(props: Props) {
  const { data: marcas } = useQuery<Marca[]>({
    queryKey: ['catalogos', 'marcas'],
    queryFn: () => api.get<Marca[]>('/api/catalogos/marcas'),
    staleTime: 5 * 60_000,
  });
  const { data: categoriasResp } = useQuery<CategoriasResponse>({
    queryKey: ['catalogos', 'categorias-producto'],
    queryFn: () => api.get<CategoriasResponse>('/api/catalogos/categorias-producto'),
    staleTime: 5 * 60_000,
  });

  const categorias = categoriasResp?.items ?? [];

  return (
    <div className="flex flex-col gap-2 mb-2">
      <div className="flex gap-1 border-b border-slate-800">
        <button
          type="button"
          onClick={() => props.onTipoChange('producto')}
          className={`px-3 py-1 text-xs border-b-2 transition ${
            props.tipo === 'producto'
              ? 'text-accent-glow border-accent-glow'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Productos
        </button>
        <button
          type="button"
          onClick={() => props.onTipoChange('servicio')}
          className={`px-3 py-1 text-xs border-b-2 transition ${
            props.tipo === 'servicio'
              ? 'text-emerald-300 border-emerald-400'
              : 'text-slate-400 border-transparent hover:text-slate-200'
          }`}
        >
          Servicios
        </button>
      </div>
      {props.tipo === 'producto' && (
        <div className="flex gap-2">
          <select
            value={props.marcaId ?? ''}
            onChange={(e) => {
              const raw = e.target.value;
              if (!raw) {
                props.onMarcaChange(null, null);
                return;
              }
              const id = Number(raw);
              const m = (marcas ?? []).find((x) => x.id === id);
              props.onMarcaChange(id, m?.nombre ?? null);
            }}
            className="h-8 rounded border border-slate-700 bg-slate-900 px-2 text-xs flex-1 focus:border-accent-glow outline-none"
          >
            <option value="">Todas las marcas</option>
            {(marcas ?? []).map((m) => (
              <option key={m.id} value={m.id}>
                {m.nombre}
                {m.n_productos > 0 ? ` (${m.n_productos})` : ''}
              </option>
            ))}
          </select>
          <select
            value={props.categoriaNombre ?? ''}
            onChange={(e) => props.onCategoriaChange(e.target.value || null)}
            className="h-8 rounded border border-slate-700 bg-slate-900 px-2 text-xs flex-1 focus:border-accent-glow outline-none"
          >
            <option value="">Todas las categorías</option>
            {categorias.map((c) => (
              <option key={c.categoria} value={c.categoria}>
                {c.categoria}
                {c.n_productos > 0 ? ` (${c.n_productos})` : ''}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
