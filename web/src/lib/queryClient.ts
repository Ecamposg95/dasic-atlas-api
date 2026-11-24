import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (failureCount, error: unknown) => {
        const status = (error as { status?: number })?.status;
        // 423 = plataforma suspendida: reintentar no cambia nada.
        if (status === 401 || status === 403 || status === 423) return false;
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
  },
});
