import * as React from 'react';
import { cn } from '@/lib/utils';

// Tabla genérica reutilizable para listados de seguimiento/borradores/fantasmas.
// El consumidor maneja sus propias columnas y filas — esto solo provee shell.

export function DataTable({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <table className={cn('w-full text-sm', className)} {...props} />
    </div>
  );
}

export function DataTableHead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="bg-slate-800/50 text-[10px] text-slate-400 uppercase tracking-wider">
      {children}
    </thead>
  );
}

export function DataTableBody({ children }: { children: React.ReactNode }) {
  return <tbody>{children}</tbody>;
}

export function DataTableRow({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn('border-b border-slate-800 hover:bg-slate-800/30 transition', className)}
      {...props}
    />
  );
}

export function DataTableEmpty({ children, colSpan }: { children: React.ReactNode; colSpan: number }) {
  return (
    <tr>
      <td colSpan={colSpan} className="p-12 text-center text-sm text-slate-500">
        {children}
      </td>
    </tr>
  );
}
