import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { BorradoresResponse } from '../types';

export const BORRADORES_PAGE_SIZE = 20;

export function useBorradores(page: number) {
  return useQuery({
    queryKey: ['borradores', page],
    queryFn: () =>
      api.get<BorradoresResponse>(
        `/api/ventas/borradores?page=${page}&page_size=${BORRADORES_PAGE_SIZE}`,
      ),
    placeholderData: keepPreviousData,
  });
}
