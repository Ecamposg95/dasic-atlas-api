import { create } from 'zustand';
import type { CartItem, LineaNoSoportada, Moneda, OrdenVentaDetail, Producto } from './types';

type CotizadorState = {
  // Modo:
  editingId: number | null;
  editingFolio: string | null;
  editingEstatus: string | null;

  // Header:
  cliente_id: number | null;
  moneda: Moneda;
  tc: number;
  fecha_creacion: string | null;
  fecha_vencimiento: string | null;
  observaciones: string;
  terminos_condiciones: string;

  // Carrito:
  cart: CartItem[];
  // Líneas no soportadas en MVP (fantasmas/servicios) que vinieron en una cot. cargada.
  lineasNoSoportadas: LineaNoSoportada[];

  // Setters:
  setCliente: (id: number | null) => void;
  setMoneda: (m: Moneda) => void;
  setTc: (tc: number) => void;
  setFechaCreacion: (d: string | null) => void;
  setFechaVencimiento: (d: string | null) => void;
  setObservaciones: (s: string) => void;
  setTerminos: (s: string) => void;

  // Cart ops:
  addProducto: (p: Producto, qty?: number, utilidadOverride?: number) => void;
  removeLinea: (uid: string) => void;
  updateLinea: (uid: string, patch: Partial<CartItem>) => void;
  moverLinea: (uid: string, delta: number) => void;
  reset: () => void;
  hydrateFromOrden: (orden: OrdenVentaDetail) => void;
};

const initialState = {
  editingId: null as number | null,
  editingFolio: null as string | null,
  editingEstatus: null as string | null,
  cliente_id: null as number | null,
  moneda: 'MXN' as Moneda,
  tc: 1,
  fecha_creacion: null as string | null,
  fecha_vencimiento: null as string | null,
  observaciones: '',
  terminos_condiciones: '',
  cart: [] as CartItem[],
  lineasNoSoportadas: [] as LineaNoSoportada[],
};

let _uidCounter = 0;
function nextUid(prefix: string): string {
  _uidCounter += 1;
  return `${prefix}-${Date.now()}-${_uidCounter}`;
}

export const useCotizador = create<CotizadorState>((set) => ({
  ...initialState,

  setCliente: (cliente_id) => set({ cliente_id }),
  setMoneda: (moneda) => set({ moneda }),
  setTc: (tc) => set({ tc }),
  setFechaCreacion: (fecha_creacion) => set({ fecha_creacion }),
  setFechaVencimiento: (fecha_vencimiento) => set({ fecha_vencimiento }),
  setObservaciones: (observaciones) => set({ observaciones }),
  setTerminos: (terminos_condiciones) => set({ terminos_condiciones }),

  addProducto: (p, qty = 1, utilidadOverride) =>
    set((s) => {
      // Si el producto ya está en el carrito, sumar cantidad en vez de duplicar.
      // (No tocamos `utilidad` del existente — el override sólo aplica al primer add.)
      const existente = s.cart.find((x) => x.producto_id === p.id);
      if (existente) {
        return {
          cart: s.cart.map((x) =>
            x.uid === existente.uid ? { ...x, qty: x.qty + qty } : x,
          ),
        };
      }
      const snapshot = {
        sku: p.sku_comercial || p.sku || '—',
        nom: p.nombre,
        cost: Number(p.costo_compra ?? 0),
      };
      const utilidad = utilidadOverride != null && Number.isFinite(utilidadOverride)
        ? utilidadOverride
        : 30;
      const nueva: CartItem = {
        uid: nextUid('nuevo'),
        producto_id: p.id,
        sku: snapshot.sku,
        nom: snapshot.nom,
        cost: snapshot.cost,
        productCurrency: (p.moneda_compra || 'MXN').toUpperCase() as Moneda,
        sku_original: snapshot.sku,
        nom_original: snapshot.nom,
        cost_original: snapshot.cost,
        max: p.stock_actual,
        qty,
        utilidad,
        descuento: 0,
        entrega_min: null,
        entrega_max: null,
        entrega_unidad: null,
        observaciones_linea: '',
      };
      return { cart: [...s.cart, nueva] };
    }),

  removeLinea: (uid) => set((s) => ({ cart: s.cart.filter((x) => x.uid !== uid) })),

  updateLinea: (uid, patch) =>
    set((s) => ({
      cart: s.cart.map((x) => (x.uid === uid ? { ...x, ...patch } : x)),
    })),

  moverLinea: (uid, delta) =>
    set((s) => {
      const idx = s.cart.findIndex((x) => x.uid === uid);
      const nuevoIdx = idx + delta;
      if (idx < 0 || nuevoIdx < 0 || nuevoIdx >= s.cart.length) return {};
      const next = s.cart.slice();
      const [it] = next.splice(idx, 1);
      next.splice(nuevoIdx, 0, it);
      return { cart: next };
    }),

  reset: () => set({ ...initialState }),

  hydrateFromOrden: (orden) =>
    set(() => {
      const monedaOrden = (orden.moneda?.toUpperCase() || 'MXN') as Moneda;
      const noSoportadas: LineaNoSoportada[] = orden.detalles
        .filter((d) => d.producto_id == null)
        .map((d) => ({
          detalle_id: d.id,
          descripcion: d.descripcion_libre || d.servicio?.nombre || '—',
          cantidad: d.cantidad,
        }));
      const cart: CartItem[] = orden.detalles
        .filter((d) => d.producto_id != null && d.producto != null)
        .map((d) => {
          const prod = d.producto!;
          const skuCat = prod.sku_comercial || prod.sku || '';
          const nomCat = prod.nombre || '';
          const costCat = Number(prod.costo_compra ?? 0);
          return {
            uid: `linea-${d.id}`,
            detalle_id: d.id,
            producto_id: d.producto_id!,
            sku: d.sku_libre || skuCat || '—',
            nom: d.descripcion_libre || nomCat || '—',
            cost: Number(d.costo_base_linea),
            productCurrency: ((d.moneda_origen_linea || monedaOrden).toUpperCase()) as Moneda,
            sku_original: skuCat,
            nom_original: nomCat,
            cost_original: costCat,
            max: 0,
            qty: d.cantidad,
            utilidad: Number(d.utilidad_aplicada),
            descuento: Number(d.descuento_aplicado),
            entrega_min: d.entrega_min,
            entrega_max: d.entrega_max,
            entrega_unidad: (d.entrega_unidad === 'dias' || d.entrega_unidad === 'semanas'
              ? d.entrega_unidad
              : null) as 'dias' | 'semanas' | null,
            observaciones_linea: d.observaciones_linea || '',
          };
        });
      return {
        editingId: orden.id,
        editingFolio: orden.folio,
        editingEstatus: orden.estatus,
        cliente_id: orden.cliente_id,
        moneda: monedaOrden,
        tc: Number(orden.tipo_cambio) || 1,
        fecha_creacion: orden.fecha_creacion?.slice(0, 10) ?? null,
        fecha_vencimiento: orden.fecha_vencimiento?.slice(0, 10) ?? null,
        observaciones: orden.observaciones ?? '',
        terminos_condiciones: orden.terminos_condiciones ?? '',
        cart,
        lineasNoSoportadas: noSoportadas,
      };
    }),
}));
