import { branding } from '@/lib/branding';
import { AtlasLockup, ATLAS_URL } from '@/components/brand/Atlas';

export function Footer() {
  return (
    <footer className="h-9 shrink-0 border-t border-border px-6 flex items-center justify-between text-[10px] text-muted-foreground bg-card/50 backdrop-blur-sm">
      <a
        href={ATLAS_URL}
        target="_blank"
        rel="noreferrer"
        className="group inline-flex items-center gap-2 rounded-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-atlas-amber"
      >
        <span>Una plataforma de</span>
        <AtlasLockup
          className="text-[11px] text-foreground transition-colors group-hover:text-atlas-ember-text dark:group-hover:text-atlas-ember"
          markClassName="h-3.5"
        />
      </a>
      <span className="font-mono hidden sm:flex items-center gap-2">
        <span>{branding.organizationName}</span>
        <span className="h-1 w-1 rounded-full bg-accent-glow/70" aria-hidden="true" />
        <span>
          {branding.productName} {branding.productVersion}
        </span>
      </span>
    </footer>
  );
}
