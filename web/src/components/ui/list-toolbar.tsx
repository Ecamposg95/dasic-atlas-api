import * as React from 'react';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ListToolbar({
  search, onSearchChange, searchPlaceholder = 'Buscar…', filters, actions, className,
}: {
  search?: string;
  onSearchChange?: (v: string) => void;
  searchPlaceholder?: string;
  filters?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      {onSearchChange && (
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            value={search ?? ''}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-8 pr-3 py-1.5 text-sm rounded-md bg-surface-2 border border-border focus:outline-none focus:ring-1 focus:ring-accent-glow"
          />
        </div>
      )}
      {filters}
      {actions && <div className="ml-auto flex items-center gap-2">{actions}</div>}
    </div>
  );
}
