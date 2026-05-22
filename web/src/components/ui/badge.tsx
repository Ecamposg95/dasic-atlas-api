import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-colors',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-slate-800 text-slate-200',
        cyan: 'border-cyan-700/50 bg-cyan-900/30 text-cyan-300',
        amber: 'border-amber-700/50 bg-amber-900/30 text-amber-300',
        emerald: 'border-emerald-700/50 bg-emerald-900/30 text-emerald-300',
        rose: 'border-rose-700/50 bg-rose-900/30 text-rose-300',
        violet: 'border-violet-700/50 bg-violet-900/30 text-violet-300',
        slate: 'border-slate-700 bg-slate-800/50 text-slate-400',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
