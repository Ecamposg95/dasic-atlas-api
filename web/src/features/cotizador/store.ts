import { create } from 'zustand';
import type {
  CartItem,
  LineaNoSoportada,
  Moneda,
  OrdenVentaDetail,
  Producto,
  Servicio,
} from './types';

// Payload para crear una línea fantasma (sin SKU del catálogo).
// proveedor_sugerido_id es opcional pero recomendado: sin él, la línea
// cae en el bucket "sin proveedor" al generar OCs.
export type AddFantasmaInput = {
  descripcion: string;
  sku_libre?: string;
  costo: number;
  moneda: Moneda;
  proveedor_sugerido_id?: number | null;
  utilidad?: number; // default 30
  qty?: number;      // default 1
  // US-008: marca + claves SAT + notas del fantasma (todos opcionales).
  marca?: string | null;
  marca_id?: number | null;
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
  observaciones?: string | null;
};

type CotizadorState = {
  // Modo:
  editingId: number | null;
  editingFolio: string | null;
  editingEstatus: string | null;

  // Header:
  cliente_id: number | null;
  moneda: Moneda;
  // Modelo TC Excel V_03 (2026-05-23): `tc` representa el DOF (TC oficial
  // Banxico). Los otros 2 son los TCs efectivos por dirección, default
  // DOF±tolerancia_tc si están null. Ver `lib/calc.ts::resolveDirectionalTcs`.
  tc: number;
  tc_mn_a_usd: number | null;
  tc_usd_a_mn: number | null;
  // Spread simétrico configurable por cotización (0.1-1.0; default 1.0).
  tolerancia_tc: number;
  fecha_creacion: string | null;
  fecha_vencimiento: string | null;
  observaciones: string;
  terminos_condiciones: string;

  // PDF: concepto unificado (una sola línea descriptiva en lugar del detalle).
  // El backend aún no consume estos campos en POST/PUT /api/ventas; se envían
  // igual para future-proof (ver `lib/serialize.ts`).
  pdf_concepto_unificado: string;
  pdf_concepto_enabled: boolean;

  // Carrito:
  cart: CartItem[];
  // Líneas no soportadas en MVP (fantasmas/servicios) que vinieron en una cot. cargada.
  lineasNoSoportadas: LineaNoSoportada[];

  // UIDs de filas con panel expandido visible.
  expandedUids: Set<string>;

  // Setters:
  setCliente: (id: number | null) => void;
  setMoneda: (m: Moneda) => void;
  setTc: (tc: number) => void;
  setTcMnAUsd: (v: number | null) => void;
  setTcUsdAMn: (v: number | null) => void;
  setToleranciaTc: (v: number) => void;
  setFechaCreacion: (d: string | null) => void;
  setFechaVencimiento: (d: string | null) => void;
  setObservaciones: (s: string) => void;
  setTerminos: (s: string) => void;
  setPdfConcepto: (s: string) => void;
  setPdfConceptoEnabled: (b: boolean) => void;

  // Cart ops:
  addProducto: (p: Producto, qty?: number, utilidadOverride?: number) => void;
  addLineaAdhoc: (input: AddFantasmaInput) => void;
  addServicio: (s: Servicio, qty?: number) => void;
  removeLinea: (uid: string) => void;
  updateLinea: (uid: string, patch: Partial<CartItem>) => void;
  moverLinea: (uid: string, delta: number) => void;
  toggleExpand: (uid: string) => void;
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
  tc_mn_a_usd: null as number | null,
  tc_usd_a_mn: null as number | null,
  tolerancia_tc: 1,
  fecha_creacion: null as string | null,
  fecha_vencimiento: null as string | null,
  observaciones: '',
  terminos_condiciones: '',
  pdf_concepto_unificado: '',
  pdf_concepto_enabled: false,
  cart: [] as CartItem[],
  lineasNoSoportadas: [] as LineaNoSoportada[],
  expandedUids: new Set<string>() as Set<string>,
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
  setTcMnAUsd: (tc_mn_a_usd) => set({ tc_mn_a_usd }),
  setTcUsdAMn: (tc_usd_a_mn) => set({ tc_usd_a_mn }),
  setToleranciaTc: (tolerancia_tc) => {
    // Clamp al rango válido [0.1, 1.0]. UI usa step 0.1; backend valida igual.
    const clamped = Math.min(1, Math.max(0.1, Number(tolerancia_tc) || 1));
    set({ tolerancia_tc: clamped });
  },
  setFechaCreacion: (fecha_creacion) => set({ fecha_creacion }),
  setFechaVencimiento: (fecha_vencimiento) => set({ fecha_vencimiento }),
  setObservaciones: (observaciones) => set({ observaciones }),
  setTerminos: (terminos_condiciones) => set({ terminos_condiciones }),
  setPdfConcepto: (pdf_concepto_unificado) => set({ pdf_concepto_unificado }),
  setPdfConceptoEnabled: (pdf_concepto_enabled) => set({ pdf_concepto_enabled }),

  addProducto: (p, qty = 1, utilidadOverride) =>
    set((s) => {
      // Cart-merge solo para líneas de catálogo del MISMO producto. Fantasmas
      // (producto_id === null) nunca se mergean — cada fantasma es único.
      const existente = s.cart.find(
        (x) => x.tipo_linea === 'producto_catalogo' && x.producto_id === p.id,
      );
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
        tipo_linea: 'producto_catalogo',
        producto_id: p.id,
        servicio_id: null,
        sku: snapshot.sku,
        nom: snapshot.nom,
        cost: snapshot.cost,
        productCurrency: (p.moneda_compra || 'MXN').toUpperCase() as Moneda,
        sku_original: snapshot.sku,
        nom_original: snapshot.nom,
        cost_original: snapshot.cost,
        max: p.stock_actual,
        // Heredamos el proveedor principal del catálogo para que el
        // Preview OC pueda agrupar la línea sin esperar a guardar la cot.
        // Si el catálogo no tiene proveedor asignado, queda null → bucket
        // "sin proveedor".
        proveedor_sugerido_id: p.proveedor_principal_id ?? null,
        marca: p.marca ?? null,
        mostrar_marca: false,
        qty,
        utilidad,
        descuento: 0,
        descuento_proveedor: 0,
        entrega_min: null,
        entrega_max: null,
        entrega_unidad: null,
        observaciones_linea: '',
      };
      return { cart: [...s.cart, nueva] };
    }),

  addLineaAdhoc: (input) =>
    set((s) => {
      const utilidad =
        input.utilidad != null && Number.isFinite(input.utilidad) ? input.utilidad : 30;
      const qty = input.qty ?? 1;
      const sku = (input.sku_libre || '').trim() || '—';
      const nueva: CartItem = {
        uid: nextUid('fantasma'),
        tipo_linea: 'producto_fantasma',
        producto_id: null,
        servicio_id: null,
        sku,
        nom: input.descripcion,
        cost: input.costo,
        productCurrency: input.moneda,
        sku_original: '',
        nom_original: '',
        cost_original: 0,
        max: 0,
        proveedor_sugerido_id: input.proveedor_sugerido_id ?? null,
        marca: input.marca ?? null,
        marca_id: input.marca_id ?? null,
        clave_prod_serv: input.clave_prod_serv ?? null,
        clave_unidad_sat: input.clave_unidad_sat ?? null,
        observaciones: input.observaciones ?? null,
        qty,
        utilidad,
        descuento: 0,
        descuento_proveedor: 0,
        entrega_min: null,
        entrega_max: null,
        entrega_unidad: null,
        observaciones_linea: '',
      };
      return { cart: [...s.cart, nueva] };
    }),

  addServicio: (svc, qty = 1) =>
    set((s) => {
      // Cart-merge si el mismo servicio_id ya está → solo sumamos cantidad.
      // Match con el comportamiento de addProducto. Si el override del costo
      // ya está aplicado, se respeta — no lo regeneramos del catálogo.
      const existente = s.cart.find(
        (x) => x.tipo_linea === 'servicio_catalogo' && x.servicio_id === svc.id,
      );
      if (existente) {
        return {
          cart: s.cart.map((x) =>
            x.uid === existente.uid ? { ...x, qty: x.qty + qty } : x,
          ),
        };
      }
      const costo = Number(svc.costo ?? 0);
      const moneda = (svc.moneda || 'MXN').toUpperCase() as Moneda;
      const nueva: CartItem = {
        uid: nextUid('servicio'),
        tipo_linea: 'servicio_catalogo',
        producto_id: null,
        servicio_id: svc.id,
        sku: svc.codigo || '—',
        nom: svc.nombre,
        cost: costo,
        productCurrency: moneda,
        sku_original: svc.codigo || '',
        nom_original: svc.nombre,
        cost_original: costo,
        max: 0, // servicios no tienen stock
        proveedor_sugerido_id: null, // servicios son internos, sin OC al proveedor
        qty,
        utilidad: 30,
        descuento: 0,
        descuento_proveedor: 0,
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

  toggleExpand: (uid) =>
    set((s) => {
      const n = new Set(s.expandedUids);
      if (n.has(uid)) n.delete(uid);
      else n.add(uid);
      return { expandedUids: n };
    }),

  reset: () => set({ ...initialState, expandedUids: new Set<string>() }),

  hydrateFromOrden: (orden) =>
    set(() => {
      const monedaOrden = (orden.moneda?.toUpperCase() || 'MXN') as Moneda;
      // El endpoint /detalle-json NO devuelve `id` por detalle. Usamos el
      // índice del array como id sintético — estable dentro de la sesión de
      // edición y suficiente para keying React + ordenamiento.
      // TODO(backend): exponer `detalle.id` en /detalle-json para preservar
      // el id real entre saves (útil si el editor algún día hace PATCH por
      // línea en lugar de PUT completo).
      const indexed = orden.detalles.map((d, i) => ({ d, idx: i }));

      // Desde 2026-05-23: fantasmas y servicios_catalogo entran al cart.
      // `lineasNoSoportadas` queda como fallback defensivo para detalles
      // raros sin producto_id, sin servicio_id y sin descripcion_libre
      // (improbable; no se debería ver en producción).
      const noSoportadas: LineaNoSoportada[] = indexed
        .filter(
          ({ d }) =>
            d.producto_id == null &&
            d.servicio_id == null &&
            !d.descripcion_libre,
        )
        .map(({ d, idx }) => ({
          detalle_id: (d as any).id ?? idx,
          descripcion: d.descripcion_libre || d.servicio?.nombre || '—',
          cantidad: d.cantidad,
        }));

      const cartCatalogo: CartItem[] = indexed
        .filter(({ d }) => d.producto_id != null && d.producto != null)
        .map(({ d, idx }) => {
          const prod = d.producto!;
          // /detalle-json ya colapsa sku = sku_comercial || sku; no expone
          // `sku_comercial` por separado.
          const skuCat = prod.sku || '';
          const nomCat = prod.nombre || '';
          const costCat = Number(prod.costo_compra ?? 0);
          return {
            uid: `linea-${idx}`,
            detalle_id: (d as any).id ?? idx,
            tipo_linea: 'producto_catalogo' as const,
            producto_id: d.producto_id!,
            servicio_id: null,
            sku: d.sku_libre || skuCat || '—',
            nom: d.descripcion_libre || nomCat || '—',
            cost: Number(d.costo_base_linea),
            productCurrency: ((d.moneda_origen_linea || monedaOrden).toUpperCase()) as Moneda,
            sku_original: skuCat,
            nom_original: nomCat,
            cost_original: costCat,
            marca: d.marca ?? prod.marca ?? null,
            mostrar_marca: !!d.mostrar_marca,
            max: 0,
            qty: d.cantidad,
            utilidad: Number(d.utilidad_aplicada),
            descuento: Number(d.descuento_aplicado),
            descuento_proveedor: Number(d.descuento_proveedor ?? 0),
            entrega_min: d.entrega_min,
            entrega_max: d.entrega_max,
            entrega_unidad: (d.entrega_unidad === 'dias' || d.entrega_unidad === 'semanas'
              ? d.entrega_unidad
              : null) as 'dias' | 'semanas' | null,
            observaciones_linea: d.observaciones_linea || '',
          };
        });

      // Servicios del catálogo: servicio_id != null. La descripción y el
      // SKU vienen del snapshot persistido (`sku_libre`/`descripcion_libre`),
      // que el backend rellena con `servicio.codigo`/`servicio.nombre` al
      // crear el detalle (ver app/routers/ventas.py:634-635).
      const cartServicios: CartItem[] = indexed
        .filter(({ d }) => d.servicio_id != null)
        .map(({ d, idx }) => {
          const skuSnap = d.sku_libre || d.servicio?.codigo || '—';
          const nomSnap = d.descripcion_libre || d.servicio?.nombre || '—';
          return {
            uid: `linea-${idx}`,
            detalle_id: (d as any).id ?? idx,
            tipo_linea: 'servicio_catalogo' as const,
            producto_id: null,
            servicio_id: d.servicio_id,
            sku: skuSnap,
            nom: nomSnap,
            cost: Number(d.costo_base_linea),
            productCurrency: ((d.moneda_origen_linea || monedaOrden).toUpperCase()) as Moneda,
            sku_original: skuSnap,
            nom_original: nomSnap,
            cost_original: Number(d.costo_base_linea),
            marca: d.marca ?? null,
            mostrar_marca: !!d.mostrar_marca,
            max: 0,
            proveedor_sugerido_id: null,
            qty: d.cantidad,
            utilidad: Number(d.utilidad_aplicada),
            descuento: Number(d.descuento_aplicado),
            descuento_proveedor: Number(d.descuento_proveedor ?? 0),
            entrega_min: d.entrega_min,
            entrega_max: d.entrega_max,
            entrega_unidad: (d.entrega_unidad === 'dias' || d.entrega_unidad === 'semanas'
              ? d.entrega_unidad
              : null) as 'dias' | 'semanas' | null,
            observaciones_linea: d.observaciones_linea || '',
          };
        });

      // Fantasmas: producto_id NULL Y servicio_id NULL Y hay descripcion_libre.
      // La descripción viene de descripcion_libre; el SKU del sku_libre si lo hay.
      const cartFantasmas: CartItem[] = indexed
        .filter(
          ({ d }) =>
            d.producto_id == null &&
            d.servicio_id == null &&
            !!d.descripcion_libre,
        )
        .map(({ d, idx }) => ({
          uid: `linea-${idx}`,
          detalle_id: (d as any).id ?? idx,
          tipo_linea: 'producto_fantasma' as const,
          producto_id: null,
          servicio_id: null,
          sku: d.sku_libre || '—',
          nom: d.descripcion_libre || '—',
          cost: Number(d.costo_base_linea),
          productCurrency: ((d.moneda_origen_linea || monedaOrden).toUpperCase()) as Moneda,
          sku_original: '',
          nom_original: '',
          cost_original: 0,
          marca: d.marca ?? null,
          mostrar_marca: !!d.mostrar_marca,
          max: 0,
          proveedor_sugerido_id: d.proveedor_sugerido_id ?? null,
          qty: d.cantidad,
          utilidad: Number(d.utilidad_aplicada),
          descuento: Number(d.descuento_aplicado),
          descuento_proveedor: Number(d.descuento_proveedor ?? 0),
          entrega_min: d.entrega_min,
          entrega_max: d.entrega_max,
          entrega_unidad: (d.entrega_unidad === 'dias' || d.entrega_unidad === 'semanas'
            ? d.entrega_unidad
            : null) as 'dias' | 'semanas' | null,
          observaciones_linea: d.observaciones_linea || '',
        }));

      // Preservar orden original de la cotización (por detalle.id ascendente).
      const cart: CartItem[] = [...cartCatalogo, ...cartFantasmas, ...cartServicios].sort(
        (a, b) => {
          const ai = a.detalle_id ?? Number.MAX_SAFE_INTEGER;
          const bi = b.detalle_id ?? Number.MAX_SAFE_INTEGER;
          return ai - bi;
        },
      );
      return {
        editingId: orden.id,
        editingFolio: orden.folio,
        editingEstatus: orden.estatus,
        cliente_id: orden.cliente_id,
        moneda: monedaOrden,
        tc: Number(orden.tipo_cambio) || 1,
        tc_mn_a_usd:
          orden.tc_mn_a_usd != null ? Number(orden.tc_mn_a_usd) : null,
        tc_usd_a_mn:
          orden.tc_usd_a_mn != null ? Number(orden.tc_usd_a_mn) : null,
        tolerancia_tc:
          orden.tolerancia_tc != null ? Number(orden.tolerancia_tc) : 1,
        fecha_creacion: orden.fecha_creacion?.slice(0, 10) ?? null,
        fecha_vencimiento: orden.fecha_vencimiento?.slice(0, 10) ?? null,
        observaciones: orden.observaciones ?? '',
        terminos_condiciones: orden.terminos_condiciones ?? '',
        // El backend expone estos campos como `pdf_unificado`/`concepto_unificado`
        // en /detalle-json (ver app/routers/ventas.py:1439-1440). El store usa
        // el alias interno `pdf_concepto_*` (mapeado en buildSavePayload).
        pdf_concepto_unificado: orden.concepto_unificado ?? '',
        pdf_concepto_enabled: orden.pdf_unificado === 1,
        cart,
        lineasNoSoportadas: noSoportadas,
        expandedUids: new Set<string>(),
      };
    }),
}));
