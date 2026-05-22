export function Footer() {
  return (
    <footer className="h-9 shrink-0 border-t border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-500 bg-white/60 dark:bg-slate-900/60">
      <span>
        Powered by <strong className="text-slate-600 dark:text-slate-400">Atlas Tech</strong>
      </span>
      <span className="font-mono hidden sm:inline">
        DASIC <span className="text-slate-400 dark:text-slate-600">·</span> Atlas ONE v2.0
      </span>
    </footer>
  );
}
