// Recepción completa de OC. MVP: solo recepción total (no parcial).
// POST /api/compras/{id}/recibir — sin body requerido, solo auth cookie.

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { toast } from '@/lib/toast';
import type { RecepcionResponse } from '../types';

type Props = {
  id: number;
  folio: string | null;
  onClose: () => void;
};

export function RegistrarRecepcionModal({ id, folio, onClose }: Props) {
  const qc = useQueryClient();
  const [confirmado, setConfirmado] = useState(false);

  const mutation = useMutation<RecepcionResponse, { status?: number; detail?: string }>({
    mutationFn: () => api.post<RecepcionResponse>(`/api/compras/${id}/recibir`),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['ordenesCompra'] });
      qc.invalidateQueries({ queryKey: ['ordenCompraDetalle', id] });
      toast({
        kind: 'success',
        title: 'Recepción registrada',
        description: `${data.productos_ingresados} producto(s) ingresados al almacén.`,
      });
      onClose();
    },
    onError: (e) => {
      if (e.status === 401) { window.location.href = '/spa/login'; return; }
      if (e.status === 403) {
        toast({ kind: 'error', title: 'Sin permiso', description: 'Se requiere rol admin o asistente.' });
        return;
      }
      toast({ kind: 'error', title: 'Error al recibir OC', description: e.detail });
    },
  });

  return (
    <Modal title="Registrar recepción de OC" onClose={onClose} size="sm">
      <div className="space-y-3 text-sm">
        <p className="text-slate-300">
          Vas a marcar la OC{' '}
          <span className="font-mono font-bold text-cyan-300">{folio ?? `#${id}`}</span>{' '}
          como <span className="font-bold">recibida</span>.
        </p>
        <p className="text-slate-400 text-xs">
          Esto ingresará al almacén todos los productos de la OC como una ENTRADA de stock.
          Esta operación no se puede deshacer.
        </p>
        <label className="flex items-center gap-2 cursor-pointer select-none mt-2">
          <input
            type="checkbox"
            checked={confirmado}
            onChange={(e) => setConfirmado(e.target.checked)}
            className="h-4 w-4 accent-cyan-400"
          />
          <span className="text-xs text-slate-300">
            Confirmo que la mercancía fue recibida físicamente en almacén.
          </span>
        </label>
      </div>
      <ModalFooter>
        <Button variant="ghost" size="sm" onClick={onClose} disabled={mutation.isPending}>
          Cancelar
        </Button>
        <Button
          size="sm"
          onClick={() => mutation.mutate()}
          disabled={!confirmado || mutation.isPending}
        >
          {mutation.isPending ? 'Procesando…' : 'Confirmar recepción'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
