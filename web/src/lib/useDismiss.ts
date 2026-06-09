import { useEffect, type RefObject } from 'react';

/**
 * Cierra un overlay al hacer click fuera de `ref` o al presionar Escape.
 * `onClose` DEBE ser estable (envolver en useCallback en el caller) o el
 * listener se re-registra en cada render. `enabled` debe ser el estado `open`.
 */
export function useDismiss(
  ref: RefObject<HTMLElement>,
  onClose: () => void,
  enabled = true,
) {
  useEffect(() => {
    if (!enabled) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [ref, onClose, enabled]);
}
