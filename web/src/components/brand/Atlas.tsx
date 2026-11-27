import { cn } from '@/lib/utils';

// Firma de Atlas Tech (skill atlas-tech-brand). La marca es la "A" dentro del
// círculo, siempre en `currentColor`: nunca deformada ni con degradado.

export function AtlasMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 375.71 340" aria-hidden="true" className={cn('h-5 w-auto shrink-0', className)}>
      <g fill="currentColor">
        <polygon points="252.36 236.3 195.47 110.84 140.66 236.21 98.8 235.8 174.88 71.93 216.92 71.85 295.23 235.73 252.36 236.3" />
        <polygon points="235.1 264.18 156.85 264.18 169.04 236.37 222.59 236.45 235.1 264.18" />
        <path d="M322.77,271.46c-5.63,7.02-12.31,13.43-18.68,19.74-31,30.74-75.65,46.25-119.14,44.73-92.04-3.23-164.14-80-162.22-171.68C24.29,89.2,76.26,23.61,149.63,4.95,164.96,1.05,180.47-.39,196.78.09c49.74,1.45,95.91,25.54,126.33,64.35,47.43,60.52,48.14,146.58-.34,207.02ZM285.77,268.38c61.55-58.4,56.66-157.12-9.84-209.36-54.27-42.64-132.41-38.36-181.82,10.11-54.43,53.4-55.5,140.38-2.56,195.07,52.52,54.26,139.28,56.32,194.22,4.19Z" />
      </g>
    </svg>
  );
}

/** Lockup: marca + "Atlas" (500) + segundo nombre (300, atenuado). */
export function AtlasLockup({
  name = 'Tech',
  className,
  markClassName,
}: {
  /** Segundo nombre: "Tech" (marca madre) o el producto ("ONE"). */
  name?: string;
  className?: string;
  markClassName?: string;
}) {
  return (
    <span className={cn('inline-flex items-center gap-2 leading-none tracking-[-0.01em]', className)}>
      <AtlasMark className={markClassName} />
      <span>
        <span className="font-medium">Atlas</span> <span className="font-light opacity-60">{name}</span>
      </span>
    </span>
  );
}

export const ATLAS_URL = 'https://atlastech.mx';
