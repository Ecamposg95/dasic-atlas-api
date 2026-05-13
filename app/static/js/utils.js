/**
 * Helpers globales front (sin dependencias).
 */

/**
 * Parsea response.json() de FastAPI/Pydantic en mensaje legible.
 * Cubre:
 *   - string plano → tal cual
 *   - array de ValidationError pydantic → "loc.field: msg" joined
 *   - object con .mensaje → mensaje
 *   - cualquier otro → JSON.stringify como fallback
 */
window.parseApiError = async function (res, fallback) {
  try {
    const data = await res.clone().json();
    const d = data?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) {
      return d.map((e) => {
        const loc = Array.isArray(e?.loc) ? e.loc.slice(1).join('.') : '';
        return loc ? `${loc}: ${e.msg || ''}` : (e.msg || JSON.stringify(e));
      }).join(' · ');
    }
    if (d && typeof d === 'object') {
      if (d.mensaje) return d.mensaje;
      return JSON.stringify(d);
    }
  } catch (_) {
    // El body no es JSON
  }
  return fallback || 'Error del servidor.';
};

/**
 * Formatea un Number como moneda con prefijo simple.
 *   fmtMoney(1500.5)        → "$1,500.50"
 *   fmtMoney(1500.5, 'USD') → "US$1,500.50"
 */
window.fmtMoney = function (v, moneda = 'MXN') {
  const sym = (moneda || 'MXN').toUpperCase() === 'USD' ? 'US$' : '$';
  const n = Number(v || 0);
  return sym + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

/**
 * Formatea fecha ISO a "dd MMM yyyy" en español MX.
 */
window.fmtFecha = function (iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch (_) {
    return iso;
  }
};
