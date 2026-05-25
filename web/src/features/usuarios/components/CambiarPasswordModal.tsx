// web/src/features/usuarios/components/CambiarPasswordModal.tsx
import { useState } from 'react';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { Usuario } from '../types';

type Props = {
  usuario: Usuario;
  onSave: (password: string) => void;
  onClose: () => void;
  busy: boolean;
};

export function CambiarPasswordModal({ usuario, onSave, onClose, busy }: Props) {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [err, setErr] = useState<string | null>(null);

  function onSubmit() {
    setErr(null);
    if (password.length < 6) {
      setErr('La contraseña debe tener al menos 6 caracteres.');
      return;
    }
    if (password !== confirm) {
      setErr('Las contraseñas no coinciden.');
      return;
    }
    onSave(password);
  }

  return (
    <Modal
      title={`Cambiar contraseña: ${usuario.nombre}`}
      onClose={onClose}
      size="sm"
    >
      <div className="space-y-3">
        <div>
          <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">
            Nueva contraseña <span className="text-rose-400">*</span>
          </label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mínimo 6 caracteres"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">
            Confirmar contraseña <span className="text-rose-400">*</span>
          </label>
          <Input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Repetir contraseña"
          />
        </div>

        {err && (
          <div className="text-xs bg-rose-50 dark:bg-rose-900/30 border border-rose-300 dark:border-rose-700/50 rounded p-2 text-rose-700 dark:text-rose-300">
            {err}
          </div>
        )}
      </div>

      <ModalFooter>
        <Button variant="ghost" size="sm" onClick={onClose} disabled={busy}>
          Cancelar
        </Button>
        <Button size="sm" onClick={onSubmit} disabled={busy}>
          {busy ? 'Guardando…' : 'Cambiar contraseña'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
