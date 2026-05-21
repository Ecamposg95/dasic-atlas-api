import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useAuth, type User } from '@/stores/auth';

export function HelloPage() {
  const navigate = useNavigate();
  const setUser = useAuth((s) => s.setUser);
  const { data, isLoading, error } = useQuery<User>({
    queryKey: ['me'],
    queryFn: () => api.get<User>('/api/auth/me'),
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data, setUser]);

  useEffect(() => {
    const status = (error as { status?: number })?.status;
    if (status === 401) navigate('/spa/login', { replace: true });
  }, [error, navigate]);

  if (isLoading) return <div className="p-6 text-slate-400">Cargando…</div>;
  if (error) {
    const status = (error as { status?: number })?.status;
    if (status === 401) return null;
    return <div className="p-6 text-rose-400">Error: {String((error as { detail?: string })?.detail ?? error)}</div>;
  }

  return (
    <div className="p-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>¡Hola, {data?.nombre}!</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-slate-400">
            Esta es la página de prueba del nuevo stack SPA. Tu rol es{' '}
            <code className="text-accent-glow">{data?.rol_label}</code>.
          </p>
          <p className="text-slate-500 text-sm">
            Resto de la app sigue en Jinja+Alpine. Próximo paso: migrar el cotizador (Phase 1).
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
