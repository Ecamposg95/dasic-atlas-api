// web/src/features/servicios/types.ts
// Shape derived from GET /api/servicios/ + ServicioResponse schema.

export type Servicio = {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  categoria_servicio: string | null;
  costo: number | string;
  moneda: string;
  tiempo_estimado: number | string | null;
  unidad_tiempo: string | null;
  clave_prod_serv: string | null;
  clave_unidad_sat: string | null;
  objeto_imp: string | null;
  descripcion_fiscal: string | null;
  activo: boolean;
  creado_por_id: number | null;
  organization_id: string | null;
  creado_en: string | null;
  actualizado_en: string | null;
};

export type ServicioCreate = {
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  categoria_servicio?: string | null;
  costo?: number;
  moneda?: string;
  tiempo_estimado?: number | null;
  unidad_tiempo?: string | null;
  clave_prod_serv?: string | null;
  clave_unidad_sat?: string | null;
  objeto_imp?: string | null;
  descripcion_fiscal?: string | null;
  activo?: boolean;
};

export type ServicioUpdate = Partial<ServicioCreate>;

export type CategoriaItem = {
  categoria: string;
  n: number;
};

export type CategoriasResponse = {
  items: CategoriaItem[];
  sugeridas: string[];
};
