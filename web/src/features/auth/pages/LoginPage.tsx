import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuth, type User } from '@/stores/auth';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const setUser = useAuth((s) => s.setUser);

  // Si ya hay cookie válida, redirigir directo al dashboard (matching el
  // comportamiento previo de Jinja `view_login` que hacía RedirectResponse).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await api.get<User>('/api/auth/me');
        if (cancelled) return;
        setUser(me);
        navigate('/spa/dashboard', { replace: true });
      } catch {
        // 401 esperado si no hay sesión — mantener login visible.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate, setUser]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const r = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password }).toString(),
      });
      if (!r.ok) {
        const d = (await r.json().catch(() => ({}))) as { detail?: string };
        setError(d.detail ?? 'Credenciales incorrectas');
        setBusy(false);
        return;
      }
      const me = await api.get<User>('/api/auth/me');
      setUser(me);
      navigate('/spa/dashboard', { replace: true });
    } catch {
      setError('Error de conexión. Intenta de nuevo.');
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="relative z-10 w-full max-w-md">
        <div className="rounded-2xl border border-slate-700/50 bg-slate-800/80 backdrop-blur-xl shadow-2xl shadow-black/40 p-8">
          {/* Marca */}
          <div className="mb-8 text-center">
            <img
              src="/static/img/Logo_main.png"
              alt="DASIC"
              className="mx-auto mb-4 h-20 w-auto object-contain drop-shadow-2xl"
              onError={(e) => {
                // Si la imagen no existe, oculta el elemento (no rompe layout)
                (e.currentTarget as HTMLImageElement).style.display = 'none';
              }}
            />
            <h1 className="text-2xl font-bold text-white tracking-tight">Atlas ONE</h1>
            <p className="mt-1 text-sm text-slate-400">DASIC <span className="text-accent-glow">·</span> Sistema Industrial</p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-rose-500/10 border border-rose-500/20 px-4 py-3 text-sm text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Correo electrónico
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                autoFocus
                placeholder="admin@dasic.mx"
                className="w-full bg-slate-700/50 border border-slate-600 text-slate-100 placeholder-slate-500 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-accent-glow focus:ring-1 focus:ring-accent-glow/40 transition"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Contraseña
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full bg-slate-700/50 border border-slate-600 text-slate-100 placeholder-slate-500 rounded-lg px-3 pr-10 py-2.5 text-sm focus:outline-none focus:border-accent-glow focus:ring-1 focus:ring-accent-glow/40 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                  aria-label={showPass ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  {showPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={busy}
              className="mt-2 w-full flex items-center justify-center gap-2 bg-accent-glow hover:bg-accent-glow/90 disabled:bg-slate-700 disabled:cursor-not-allowed text-slate-900 font-semibold text-sm py-2.5 rounded-lg transition-all shadow-lg hover:shadow-accent-glow/30 active:scale-[0.98]"
            >
              {busy ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Verificando…</span>
                </>
              ) : (
                <>
                  <span>Ingresar al sistema</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-[10px] text-slate-600">
          Powered by Atlas Tech · Atlas ONE v2.0
        </p>
      </div>
    </div>
  );
}
