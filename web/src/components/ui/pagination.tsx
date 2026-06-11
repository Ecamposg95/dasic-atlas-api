import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function Pagination({
  page, totalPages, onPageChange, isLoading, className,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
  className?: string;
}) {
  if (totalPages <= 1) return null;
  const hasPrev = page > 1;
  const hasNext = page < totalPages;
  return (
    <div className={cn('flex items-center justify-between text-sm text-muted-foreground', isLoading && 'opacity-50', className)}>
      <Button variant="outline" size="sm" disabled={!hasPrev || isLoading} onClick={() => onPageChange(Math.max(1, page - 1))}>
        <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
      </Button>
      <span>Página {page} de {totalPages}</span>
      <Button variant="outline" size="sm" disabled={!hasNext || isLoading} onClick={() => onPageChange(page + 1)}>
        Siguiente <ChevronRight className="h-4 w-4 ml-1" />
      </Button>
    </div>
  );
}
