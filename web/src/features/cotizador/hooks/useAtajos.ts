import { useEffect } from 'react';

export type AtajoHandler = {
  combo: string;            // ej. "/", "ctrl+s", "ctrl+z", "n", "p", "f", "?"
  description: string;
  handler: (e: KeyboardEvent) => void;
};

function matches(combo: string, e: KeyboardEvent): boolean {
  const parts = combo.toLowerCase().split('+').map((s) => s.trim());
  const wantCtrl = parts.includes('ctrl');
  const wantShift = parts.includes('shift');
  const wantAlt = parts.includes('alt');
  const key = parts[parts.length - 1];
  if (wantCtrl !== (e.ctrlKey || e.metaKey)) return false;
  if (wantAlt !== e.altKey) return false;
  // Shift check: solo se enforza cuando el combo tiene modificadores explícitos,
  // o cuando la tecla final es alfanumérica. Atajos de un solo carácter de
  // puntuación (`/`, `?`, `!`, etc.) aceptan cualquier estado de shift porque
  // teclear esos símbolos requiere Shift en la mayoría de los layouts (US/ES/MX).
  // Sin esto, `?` (Shift+/) nunca dispararía porque wantShift=false pero
  // e.shiftKey=true.
  const isPunctuation = parts.length === 1 && !/^[a-z0-9]$/.test(key);
  if (!isPunctuation && wantShift !== e.shiftKey) return false;
  return e.key.toLowerCase() === key;
}

const TYPING_TAGS = new Set(['INPUT', 'TEXTAREA', 'SELECT']);

/**
 * Listener global de atajos. Respeta el contexto: atajos sin modificadores
 * NO se disparan mientras el usuario teclea en un input/textarea/select,
 * con la excepción de `/` que debe poder enfocar la búsqueda desde cualquier
 * lugar. Combos con Ctrl/Shift/Alt siempre se disparan.
 */
export function useAtajos(atajos: AtajoHandler[]) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const isTyping = !!target && (TYPING_TAGS.has(target.tagName) || target.isContentEditable);
      const a = atajos.find((x) => matches(x.combo, e));
      if (!a) return;
      // Atajos sin modificadores no disparan mientras tecleas (excepto `/`)
      if (!a.combo.includes('+') && isTyping && a.combo !== '/') return;
      if (document.querySelector('[data-overlay]')) return; // hay un modal/drawer abierto
      e.preventDefault();
      a.handler(e);
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [atajos]);
}
