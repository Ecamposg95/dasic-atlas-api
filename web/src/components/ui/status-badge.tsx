import { cn } from '@/lib/utils';
import { statusTone, toneClasses, type StatusTone } from '@/lib/status-tones';

export function StatusBadge({
  status, tone, label, className,
}: {
  status?: string | null;
  tone?: StatusTone;
  label?: string;
  className?: string;
}) {
  const t = tone ?? statusTone(status);
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
        toneClasses(t),
        className,
      )}
    >
      {label ?? status ?? '—'}
    </span>
  );
}
