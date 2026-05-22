// Toast minimal — emite eventos que un <Toaster /> global escucha.
// Más simple que radix-toast para MVP, sin dependencias adicionales.

export type ToastKind = 'success' | 'error' | 'warning' | 'info';
export type ToastEvent = { kind: ToastKind; title: string; description?: string };

export function toast(t: ToastEvent) {
  window.dispatchEvent(new CustomEvent<ToastEvent>('app:toast', { detail: t }));
}
