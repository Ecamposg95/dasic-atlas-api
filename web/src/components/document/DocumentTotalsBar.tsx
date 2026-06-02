import type { ReactNode } from 'react';

export type DocStat = {
  label: ReactNode;   // incluye ícono si se desea
  value: string;
  emphasis?: 'big' | 'normal' | 'accent'; // big=2xl, accent=color glow
  valueClass?: string; // override fino del color del value
};

export function DocumentTotalsBar({
  stats,
  warnings,
  trailing,
  actions,
}: {
  stats: DocStat[];
  warnings?: ReactNode;
  trailing?: ReactNode;
  actions: ReactNode;
}) {
  return (
    <div className="sticky bottom-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 px-4 py-3">
      {warnings}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-6 flex-wrap">
          {stats.map((s, i) => (
            <div className="flex flex-col" key={i}>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1">
                {s.label}
              </span>
              <span
                className={
                  s.valueClass ??
                  (s.emphasis === 'big'
                    ? 'font-mono text-2xl font-semibold text-slate-900 dark:text-slate-100'
                    : s.emphasis === 'accent'
                      ? 'font-mono text-2xl font-bold text-accent-glow'
                      : 'font-mono text-xs text-slate-600 dark:text-slate-400')
                }
              >
                {s.value}
              </span>
            </div>
          ))}
          {trailing}
        </div>
        <div className="flex gap-2">{actions}</div>
      </div>
    </div>
  );
}
