/**
 * Toast global reusable.
 *
 * API:
 *   window.toast(mensaje, tipo='success', ms=3500)
 *   tipos: 'success' | 'error' | 'warning' | 'info'
 *
 * Renderiza un store Alpine 'toasts' (array) con auto-dismiss. El layout
 * en base.html monta un contenedor fijo top-right que itera el store.
 *
 * Diseño: cero dependencias externas; tailwind ya disponible.
 */
(function () {
  const STORE = 'toasts';
  let _id = 0;

  function ensureStore() {
    if (!window.Alpine || !window.Alpine.store) return null;
    let s = window.Alpine.store(STORE);
    if (!s) {
      window.Alpine.store(STORE, { items: [] });
      s = window.Alpine.store(STORE);
    }
    return s;
  }

  function push(msg, type, ms) {
    const store = ensureStore();
    if (!store) {
      // Alpine aún no listo — reintentar 1 vez
      setTimeout(() => {
        const s2 = ensureStore();
        if (s2) s2.items.push(_makeItem(msg, type, ms));
        else console.warn('[toast] Alpine.store no disponible:', msg);
      }, 50);
      return;
    }
    const item = _makeItem(msg, type, ms);
    store.items.push(item);
    if (ms > 0) {
      setTimeout(() => {
        const i = store.items.findIndex((x) => x.id === item.id);
        if (i >= 0) store.items.splice(i, 1);
      }, ms);
    }
  }

  function _makeItem(msg, type, ms) {
    _id += 1;
    return {
      id: _id,
      msg: String(msg || ''),
      type: ['success', 'error', 'warning', 'info'].includes(type) ? type : 'success',
      ms,
    };
  }

  window.toast = function (msg, type = 'success', ms = 3500) {
    push(msg, type, ms);
  };

  // Atajos
  window.toast.success = (m, ms = 3500) => push(m, 'success', ms);
  window.toast.error   = (m, ms = 5000) => push(m, 'error', ms);
  window.toast.warn    = (m, ms = 4000) => push(m, 'warning', ms);
  window.toast.info    = (m, ms = 3500) => push(m, 'info', ms);

  // Init después de Alpine
  document.addEventListener('alpine:init', () => {
    if (window.Alpine && !window.Alpine.store(STORE)) {
      window.Alpine.store(STORE, { items: [] });
    }
  });
})();
