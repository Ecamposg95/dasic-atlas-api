import type { ReactNode } from 'react';

export type DocStat = {
  label: ReactNode;
  value: ReactNode;
  emphasis?: 'big' | 'normal' | 'accent';
  valueClass?: string;
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
    <div className="sticky bottom-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 px-3 md:px-4 py-3">
      {warnings}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 md:gap-3">
        <div className="flex items-center gap-4 md:gap-6 overflow-x-auto md:flex-wrap md:overflow-visible">
          {stats.map((s, i) => (
            <div className="flex flex-col shrink-0" key={i}>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1">
                {s.label}
              </span>
              <span
                className={
                  s.valueClass ??
                  (s.emphasis === 'big'
                    ? 'font-mono text-lg md:text-2xl font-semibold text-slate-900 dark:text-slate-100'
                    : s.emphasis === 'accent'
                      ? 'font-mono text-lg md:text-2xl font-bold text-accent-glow'
                      : 'font-mono text-xs text-slate-600 dark:text-slate-400')
                }
              >
                {s.value}
              </span>
            </div>
          ))}
          {trailing}
        </div>
        <div className="flex gap-2 justify-end">{actions}</div>
      </div>
    </div>
  );
}
