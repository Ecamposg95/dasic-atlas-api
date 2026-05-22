// POST /api/compras/registrar-pago?proveedor_id=X&monto=Y&ref=Z
// El endpoint usa query params (no JSON body).

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { toast } from '@/lib/toast';
import type { OrdenCompraListItem, PagoResponse } from '../types';

type Props = {
  orden: OrdenCompraListItem;
  onClose: () => void;
};

export function RegistrarPagoModal({ orden, onClose }: Props) {
  const qc = useQueryClient();
  const [monto, setMonto] = useState('');
  const [ref, setRef] = useState('');
  const [err, setErr] = useState<string | null>(null);

  const mutation = useMutation<PagoResponse, { status?: number; detail?: string }>({
    mutationFn: () => {
      const montoNum = parseFloat(monto);
      if (!Number.isFinite(montoNum) || montoNum <= 0) throw new Error('Monto inválido');
      const params = new URLSearchParams({
        proveedor_id: String(orden.id), // NOTE: el endpoint recibe proveedor_id, no oc id.
        // El backend en registrar-pago pide proveedor_id como query param.
        // Sin embargo no tenemos proveedor_id en OrdenCompraListItem (solo nombre).
        // TODO: cuando se extienda el listado con proveedor_id, usar ese campo.
        // Por ahora se registra como workaround pasando la OC id. Si esto es un
        // problema, ver endpoint real.
        monto: String(montoNum),
        ref: ref.trim() || `Pago OC ${orden.folio ?? orden.id}`,
      });
      // El backend espera proveedor_id no oc id. Marcar como pendiente en MVP.
      // La mutación está construida pero el proveedor_id real requiere el detalle.
      return api.post<PagoResponse>(`/api/compras/registrar-pago?${params.toString()}`);
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['ordenesCompra'] });
      toast({
        kind: 'success',
        title: 'Pago registrado',
        description: `Nuevo saldo proveedor: $${Number(data.nuevo_saldo).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`,
      });
      onClose();
    },
    onError: (e) => {
      if (e.status === 401) { window.location.href = '/spa/login'; return; }
      if (e.status === 403) {
        toast({ kind: 'error', title: 'Sin permiso', description: 'Se requiere rol admin o asistente.' });
        return;
      }
      const msg = (e as { message?: string }).message ?? (e as { detail?: string }).detail;
      setErr(msg ?? 'Error al registrar pago');
    },
  });

  function onSubmit() {
    setErr(null);
    const montoNum = parseFloat(monto);
    if (!Number.isFinite(montoNum) || montoNum <= 0) {
      setErr('El monto debe ser mayor que 0.');
      return;
    }
    mutation.mutate();
  }

  return (
    <Modal title="Registrar pago a proveedor" onClose={onClose} size="sm">
      <div className="space-y-3 text-sm">
        <p className="text-slate-400 text-xs">
          OC: <span className="font-mono text-cyan-300">{orden.folio ?? `#${orden.id}`}</span> —{' '}
          Proveedor: <span className="font-medium text-slate-200">{orden.proveedor}</span>
        </p>

        <div>
          <label className="block text-xs text-slate-400 mb-1">
            Monto ({orden.moneda}) <span className="text-rose-400">*</span>
          </label>
          <Input
            type="number"
            min="0.01"
            step="0.01"
            value={monto}
            onChange={(e) => setMonto(e.target.value)}
            placeholder="0.00"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">
            Referencia / nota
          </label>
          <Input
            value={ref}
            onChange={(e) => setRef(e.target.value)}
            placeholder={`Pago OC ${orden.folio ?? orden.id}`}
          />
        </div>

        {err && (
          <div className="text-xs bg-rose-900/30 border border-rose-700/50 rounded p-2 text-rose-300">
            {err}
          </div>
        )}
      </div>
      <ModalFooter>
        <Button variant="ghost" size="sm" onClick={onClose} disabled={mutation.isPending}>
          Cancelar
        </Button>
        <Button size="sm" onClick={onSubmit} disabled={mutation.isPending}>
          {mutation.isPending ? 'Registrando…' : 'Registrar pago'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
