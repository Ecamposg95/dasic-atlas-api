// Lógica pura de búsqueda enriquecida. Sin React, sin fetch.

export type ParsedQuery = {
  raw: string;             // string original
  cantidad: number | null; // cantidad si el usuario escribió "5 SKU"
  termino: string;         // término sin la cantidad
};

/**
 * Parser cantidad+SKU: "5 GV2ME14" → { cantidad: 5, termino: "GV2ME14" }.
 * Regla: si el primer token es un entero entre 1 y 999 y hay más texto, se interpreta
 * como cantidad. Si no, cantidad=null y termino=raw.
 */
export function parseQuantityPrefix(raw: string): ParsedQuery {
  const trimmed = raw.trim();
  if (!trimmed) return { raw, cantidad: null, termino: '' };
  const m = trimmed.match(/^(\d{1,3})\s+(.+)$/);
  if (m) {
    const n = parseInt(m[1], 10);
    if (n >= 1 && n <= 999) {
      return { raw, cantidad: n, termino: m[2].trim() };
    }
  }
  return { raw, cantidad: null, termino: trimmed };
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Expande términos con sinónimos. "rodamiento" → ["rodamiento", "balero", "cojinete"].
 * Solo expande tokens completos, case-insensitive.
 */
export function expandSinonimos(termino: string, dict: Record<string, string[]>): string[] {
  const lower = termino.toLowerCase();
  const tokens = lower.split(/\s+/).filter(Boolean);
  const variantes = new Set<string>([lower]);
  tokens.forEach((tok) => {
    const safe = escapeRegex(tok);
    if (dict[tok]) {
      dict[tok].forEach((syn) => {
        const variant = lower.replace(new RegExp(`\\b${safe}\\b`, 'g'), syn);
        variantes.add(variant);
      });
    }
    // También: si el token es ya un sinónimo, agregar la palabra canónica
    Object.entries(dict).forEach(([base, syns]) => {
      if (syns.includes(tok)) {
        const variant = lower.replace(new RegExp(`\\b${safe}\\b`, 'g'), base);
        variantes.add(variant);
      }
    });
  });
  return Array.from(variantes);
}

/**
 * Distancia Levenshtein truncada (early-exit a maxDist+1).
 * Útil para tolerar typos cortos: "tornilllo" → "tornillo" (dist=1).
 */
export function levenshteinTruncated(a: string, b: string, maxDist: number): number {
  if (Math.abs(a.length - b.length) > maxDist) return maxDist + 1;
  const m = a.length, n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  let prev = new Array(n + 1).fill(0).map((_, i) => i);
  for (let i = 1; i <= m; i++) {
    const curr: number[] = [i];
    let rowMin = i;
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      const v = Math.min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost);
      curr.push(v);
      if (v < rowMin) rowMin = v;
    }
    if (rowMin > maxDist) return maxDist + 1;
    prev = curr;
  }
  return prev[n];
}

/**
 * Construye el set de queries que se enviarán al backend.
 * Devuelve hasta 5 variantes ordenadas por relevancia (la original primero).
 */
export function buildSearchVariants(
  raw: string,
  dict: Record<string, string[]>,
): { cantidad: number | null; queries: string[] } {
  const parsed = parseQuantityPrefix(raw);
  if (!parsed.termino) return { cantidad: parsed.cantidad, queries: [] };
  const variantes = expandSinonimos(parsed.termino, dict);
  // Asegurar que la variante original (lowercase del termino) quede primero.
  const original = parsed.termino.toLowerCase();
  const ordenadas = [original, ...variantes.filter((v) => v !== original)];
  return { cantidad: parsed.cantidad, queries: ordenadas.slice(0, 5) };
}
