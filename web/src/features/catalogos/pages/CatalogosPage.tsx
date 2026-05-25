import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BookMarked, Tags, Layers, Ruler, Wrench } from 'lucide-react';
import { api } from '@/lib/api';
import type { ResumenCatalogo } from '../types';
import { MarcasTab } from '../components/MarcasTab';
import { CategoriasTab } from '../components/CategoriasTab';
import { UnidadesTab } from '../components/UnidadesTab';
import { CategoriasServicioTab } from '../components/CategoriasServicioTab';

type Tab = 'marcas' | 'categorias' | 'unidades' | 'categorias-servicio';

const TABS: { key: Tab; label: string; Icon: typeof Tags }[] = [
  { key: 'marcas', label: 'Marcas', Icon: Tags },
  { key: 'categorias', label: 'Categorías de producto', Icon: Layers },
  { key: 'unidades', label: 'Unidades', Icon: Ruler },
  { key: 'categorias-servicio', label: 'Categorías de servicio', Icon: Wrench },
];

export function CatalogosPage() {
  const [tab, setTab] = useState<Tab>('marcas');

  const { data: resumen, error } = useQuery<ResumenCatalogo>({
    queryKey: ['catalogos', 'resumen'],
    queryFn: () => api.get<ResumenCatalogo>('/api/catalogos/resumen'),
    staleTime: 60_000,
  });

  // 401 → login
  useEffect(() => {
    const status = (error as { status?: number } | undefined)?.status;
    if (status === 401) window.location.href = '/spa/login';
  }, [error]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <header className="flex items-center gap-2">
        <BookMarked className="h-5 w-5 text-accent-glow" />
        <h1 className="text-2xl font-semibold">Catálogos</h1>
      </header>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-3">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Marcas</div>
            <div className="text-2xl font-bold">{resumen.total_marcas}</div>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-3">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Productos</div>
            <div className="text-2xl font-bold">{resumen.total_productos}</div>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-3">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Categorías</div>
            <div className="text-2xl font-bold">{resumen.total_categorias_producto}</div>
          </div>
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-3">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Unidades</div>
            <div className="text-2xl font-bold">{resumen.total_unidades}</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-800 flex gap-1 flex-wrap">
        {TABS.map(({ key, label, Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium transition border-b-2 -mb-px inline-flex items-center gap-1.5 ${
              tab === key
                ? 'border-accent-glow text-accent-glow'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {tab === 'marcas' && <MarcasTab />}
        {tab === 'categorias' && <CategoriasTab />}
        {tab === 'unidades' && <UnidadesTab />}
        {tab === 'categorias-servicio' && <CategoriasServicioTab />}
      </div>
    </div>
  );
}
