import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useAuth, type User } from '@/stores/auth';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const setUser = useAuth((s) => s.setUser);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      // /api/auth/login usa OAuth2PasswordRequestForm (form-urlencoded), no JSON.
      const r = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password }).toString(),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({ detail: 'Credenciales inválidas' }));
        throw new Error((d as { detail?: string }).detail ?? 'Login fallido');
      }
      // Cookie quedó set por el backend. Pedir info del usuario.
      const me = await api.get<User>('/api/auth/me');
      setUser(me);
      navigate('/spa/hello');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-20 p-6">
      <Card>
        <CardHeader>
          <CardTitle>DASIC ERP — Acceso</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-3">
            <Input
              type="email"
              placeholder="correo@dasic.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
            <Input
              type="password"
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && <div className="text-rose-400 text-sm">{error}</div>}
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? 'Entrando…' : 'Entrar'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
