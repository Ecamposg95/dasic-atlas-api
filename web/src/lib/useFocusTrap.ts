import { useEffect, type RefObject } from 'react';

const FOCUSABLE = 'a[href],button:not([disabled]),textarea:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])';

/**
 * Atrapa el foco dentro de `ref` mientras `enabled`. Al activar enfoca el primer
 * focuseable; atrapa Tab/Shift+Tab; al desactivar restaura el foco al elemento
 * previamente activo. Complementa Escape/data-overlay (round 1).
 */
export function useFocusTrap(ref: RefObject<HTMLElement>, enabled: boolean) {
  useEffect(() => {
    if (!enabled || !ref.current) return;
    const container = ref.current;
    const prevActive = document.activeElement as HTMLElement | null;
    const focusables = () => Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE));
    focusables()[0]?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const els = focusables();
      if (els.length === 0) return;
      const first = els[0];
      const last = els[els.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    container.addEventListener('keydown', onKey);
    return () => {
      container.removeEventListener('keydown', onKey);
      prevActive?.focus?.();
    };
  }, [ref, enabled]);
}
