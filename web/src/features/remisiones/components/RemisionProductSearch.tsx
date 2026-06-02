import { ProductSearch, type ProductSearchHandlers } from '@/features/cotizador/components/ProductSearch';
import { useRemision } from '../store';

export function RemisionProductSearch({ onOpenManualFantasma }: { onOpenManualFantasma: () => void }) {
  const addProductoCatalogo = useRemision((s) => s.addProductoCatalogo);
  const addServicio = useRemision((s) => s.addServicio);
  const addFantasma = useRemision((s) => s.addFantasma);

  const handlers: ProductSearchHandlers = {
    onPickProducto: (p, qty) => addProductoCatalogo(p, qty),
    onPickServicio: (s, qty) => addServicio(s, qty),
    onPickFantasma: (f, qty) => addFantasma(f, qty),
    onOpenAddFantasma: () => onOpenManualFantasma(),
  };
  return <ProductSearch handlers={handlers} />;
}
