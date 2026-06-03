import * as React from 'react';
import { cn } from '@/lib/utils';

// Tabla genérica reutilizable para listados de seguimiento/borradores/fantasmas.
// El consumidor maneja sus propias columnas y filas — esto solo provee shell.

export function DataTable({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto dark:bg-slate-900 dark:border-slate-800">
      <table className={cn('w-full text-sm min-w-[640px] md:min-w-0', className)} {...props} />
    </div>
  );
}

export function DataTableHead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="bg-slate-100 text-[10px] text-slate-500 uppercase tracking-wider dark:bg-slate-800/50 dark:text-slate-400">
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
      className={cn('border-b border-slate-200 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/30', className)}
      {...props}
    />
  );
}

export function DataTableEmpty({ children, colSpan }: { children: React.ReactNode; colSpan: number }) {
  return (
    <tr>
      <td colSpan={colSpan} className="p-12 text-center text-sm text-slate-500 dark:text-slate-500">
        {children}
      </td>
    </tr>
  );
}
