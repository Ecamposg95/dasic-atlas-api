import { useState } from 'react';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import type { Gasto, GastoCreate } from '../types';

const MONEDAS = ['MXN', 'USD'];

interface Props {
  mode: 'create' | 'edit';
  gasto?: Gasto;
  categorias: string[];
  onSave: (data: GastoCreate) => void;
  onClose: () => void;
  busy: boolean;
}

export function GastoFormModal({ mode, gasto, categorias, onSave, onClose, busy }: Props) {
  const [categoria, setCategoria] = useState(gasto?.categoria ?? '');
  const [categoriaCustom, setCategoriaCustom] = useState('');
  const [descripcion, setDescripcion] = useState(gasto?.descripcion ?? '');
  const [monto, setMonto] = useState(gasto ? String(gasto.monto) : '');
  const [moneda, setMoneda] = useState(gasto?.moneda ?? 'MXN');
  const [err, setErr] = useState<string | null>(null);

  // Allow selecting existing category or typing a new one
  const isNewCategoria = categoria === '__nueva__';
  const efectivaCategoria = isNewCategoria ? categoriaCustom.trim() : categoria;

  function onSubmit() {
    setErr(null);
    if (!efectivaCategoria) {
      setErr('La categoría es requerida.');
      return;
    }
    const montoNum = parseFloat(monto);
    if (!Number.isFinite(montoNum) || montoNum <= 0) {
      setErr('El monto debe ser mayor a 0.');
      return;
    }
    onSave({
      categoria: efectivaCategoria,
      descripcion: descripcion.trim() || null,
      monto: montoNum,
      moneda,
    });
  }

  return (
    <Modal
      title={mode === 'create' ? 'Nuevo gasto' : `Editar gasto #${gasto?.id}`}
      onClose={onClose}
      size="md"
    >
      <div className="space-y-3">
        {/* Categoría */}
        <div>
          <label className="block text-xs text-muted-foreground mb-1">
            Categoría <span className="text-rose-600 dark:text-rose-400">*</span>
          </label>
          <Select
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
          >
            <option value="">— Selecciona —</option>
            {categorias.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
            <option value="__nueva__">+ Nueva categoría…</option>
          </Select>
        </div>

        {isNewCategoria && (
          <div>
            <label className="block text-xs text-muted-foreground mb-1">
              Nueva categoría <span className="text-rose-600 dark:text-rose-400">*</span>
            </label>
            <Input
              value={categoriaCustom}
              onChange={(e) => setCategoriaCustom(e.target.value)}
              placeholder="Ej. Viáticos, Papelería…"
              autoFocus
            />
          </div>
        )}

        {/* Descripción */}
        <div>
          <label className="block text-xs text-muted-foreground mb-1">Descripción</label>
          <Input
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="Detalle del gasto (opcional)"
          />
        </div>

        {/* Monto + Moneda */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-muted-foreground mb-1">
              Monto <span className="text-rose-600 dark:text-rose-400">*</span>
            </label>
            <Input
              type="number"
              step="0.01"
              min="0.01"
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              placeholder="0.00"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Moneda</label>
            <Select value={moneda} onChange={(e) => setMoneda(e.target.value)}>
              {MONEDAS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </Select>
          </div>
        </div>

        {err && (
          <div className="text-xs bg-rose-100 border border-rose-300 rounded p-2 text-rose-700 dark:bg-rose-900/30 dark:border-rose-700/50 dark:text-rose-300">
            {err}
          </div>
        )}
      </div>

      <ModalFooter>
        <Button variant="ghost" size="sm" onClick={onClose} disabled={busy}>
          Cancelar
        </Button>
        <Button size="sm" onClick={onSubmit} disabled={busy}>
          {busy ? 'Guardando…' : mode === 'create' ? 'Registrar gasto' : 'Guardar cambios'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
