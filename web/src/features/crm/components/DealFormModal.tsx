import { useState, useEffect } from 'react';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { toast } from '@/lib/toast';
import { normalizeDetail } from '@/lib/api';
import { useClientes } from '@/features/clientes/hooks/useClientes';
import { useUsuarios } from '@/features/usuarios/hooks/useUsuarios';
import { useCreateDeal, useUpdateDeal } from '../hooks/useCrmDeals';
import type { Deal, DealCreate, DealUpdate, Stage } from '../types';

type Props = {
  pipelineId: number;
  stages: Stage[];
  deal?: Deal | null;          // null/undefined = create mode
  defaultStageId?: number;
  onClose: () => void;
};

export function DealFormModal({ pipelineId, stages, deal, defaultStageId, onClose }: Props) {
  const isEdit = deal != null;

  const [titulo, setTitulo] = useState(deal?.titulo ?? '');
  const [clienteId, setClienteId] = useState<string>(deal?.cliente_id != null ? String(deal.cliente_id) : '');
  const [monto, setMonto] = useState<string>(deal?.monto != null ? String(deal.monto) : '');
  const [moneda, setMoneda] = useState<string>(deal?.moneda ?? 'MXN');
  const [stageId, setStageId] = useState<string>(
    deal?.stage_id != null
      ? String(deal.stage_id)
      : defaultStageId != null
      ? String(defaultStageId)
      : stages[0]?.id != null
      ? String(stages[0].id)
      : '',
  );
  const [ownerId, setOwnerId] = useState<string>(deal?.owner_user_id != null ? String(deal.owner_user_id) : '');

  const { data: clientes = [] } = useClientes(1, '', 500);
  const { data: usuarios = [] } = useUsuarios();

  const createDeal = useCreateDeal();
  const updateDeal = useUpdateDeal();

  const isPending = createDeal.isPending || updateDeal.isPending;

  // Reset form when deal changes (e.g. switching between edit targets).
  useEffect(() => {
    setTitulo(deal?.titulo ?? '');
    setClienteId(deal?.cliente_id != null ? String(deal.cliente_id) : '');
    setMonto(deal?.monto != null ? String(deal.monto) : '');
    setMoneda(deal?.moneda ?? 'MXN');
    setStageId(
      deal?.stage_id != null
        ? String(deal.stage_id)
        : defaultStageId != null
        ? String(defaultStageId)
        : stages[0]?.id != null
        ? String(stages[0].id)
        : '',
    );
    setOwnerId(deal?.owner_user_id != null ? String(deal.owner_user_id) : '');
  }, [deal, defaultStageId, stages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!titulo.trim()) {
      toast({ kind: 'warning', title: 'El título es requerido' });
      return;
    }

    const montoNum = monto.trim() ? parseFloat(monto) : null;
    const parsedStageId = stageId ? parseInt(stageId, 10) : undefined;
    const parsedClienteId = clienteId ? parseInt(clienteId, 10) : null;
    const parsedOwnerId = ownerId ? parseInt(ownerId, 10) : null;

    try {
      if (isEdit) {
        const payload: DealUpdate = {
          titulo: titulo.trim(),
          cliente_id: parsedClienteId,
          monto: montoNum,
          moneda,
          stage_id: parsedStageId,
          owner_user_id: parsedOwnerId,
        };
        await updateDeal.mutateAsync({ id: deal.id, payload });
        toast({ kind: 'success', title: 'Deal actualizado' });
      } else {
        const payload: DealCreate = {
          pipeline_id: pipelineId,
          titulo: titulo.trim(),
          stage_id: parsedStageId,
          cliente_id: parsedClienteId,
          monto: montoNum,
          moneda,
          owner_user_id: parsedOwnerId,
        };
        await createDeal.mutateAsync(payload);
        toast({ kind: 'success', title: 'Deal creado' });
      }
      onClose();
    } catch (err: unknown) {
      const detail = (err as { detail?: unknown })?.detail;
      toast({
        kind: 'error',
        title: isEdit ? 'Error al actualizar' : 'Error al crear',
        description: normalizeDetail(detail, 'Verifica los datos e intenta de nuevo'),
      });
    }
  }

  return (
    <Modal title={isEdit ? 'Editar deal' : 'Nuevo deal'} onClose={onClose} size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Título */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground">
            Título <span className="text-rose-500">*</span>
          </label>
          <Input
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            placeholder="Ej. Propuesta equipo industrial"
            required
            disabled={isPending}
          />
        </div>

        {/* Stage */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground">Etapa</label>
          <Select value={stageId} onChange={(e) => setStageId(e.target.value)} disabled={isPending}>
            {stages.map((s) => (
              <option key={s.id} value={String(s.id)}>
                {s.nombre}
              </option>
            ))}
          </Select>
        </div>

        {/* Cliente */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground">Cliente</label>
          <Select value={clienteId} onChange={(e) => setClienteId(e.target.value)} disabled={isPending}>
            <option value="">— Sin cliente —</option>
            {clientes.map((c) => (
              <option key={c.id} value={String(c.id)}>
                {c.nombre_empresa}
              </option>
            ))}
          </Select>
        </div>

        {/* Monto + Moneda */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-sm font-medium text-foreground">Monto</label>
            <Input
              type="number"
              min="0"
              step="0.01"
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              placeholder="0"
              disabled={isPending}
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-foreground">Moneda</label>
            <Select value={moneda} onChange={(e) => setMoneda(e.target.value)} disabled={isPending}>
              <option value="MXN">MXN</option>
              <option value="USD">USD</option>
            </Select>
          </div>
        </div>

        {/* Owner */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground">Responsable</label>
          <Select value={ownerId} onChange={(e) => setOwnerId(e.target.value)} disabled={isPending}>
            <option value="">— Sin asignar —</option>
            {usuarios.map((u) => (
              <option key={u.id} value={String(u.id)}>
                {u.nombre}
              </option>
            ))}
          </Select>
        </div>

        <ModalFooter>
          <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isPending}>
            Cancelar
          </Button>
          <Button type="submit" size="sm" disabled={isPending}>
            {isPending ? 'Guardando…' : isEdit ? 'Guardar cambios' : 'Crear deal'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
}
