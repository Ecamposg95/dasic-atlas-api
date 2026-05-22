// web/src/features/usuarios/types.ts
// Shape derived from GET /api/usuarios/ + UsuarioResponse schema.

export type RolUsuario =
  | 'administrador'
  | 'gerente_comercial'
  | 'ventas'
  | 'operativo'
  | 'superadmin';

export type Usuario = {
  id: number;
  nombre: string;
  email: string;
  rol: RolUsuario | string;
  activo: boolean;
};

export type UsuarioCreate = {
  nombre: string;
  email: string;
  rol: RolUsuario;
  activo?: boolean;
  password: string;
};

export type UsuarioUpdate = {
  nombre?: string;
  rol?: RolUsuario;
  activo?: boolean;
};
