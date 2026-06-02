import type { ReactNode } from 'react';

export function DocumentSectionDivider({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.15em] text-slate-400 dark:text-slate-500 mt-2">
      {icon}
      <span>{label}</span>
      <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />
    </div>
  );
}
