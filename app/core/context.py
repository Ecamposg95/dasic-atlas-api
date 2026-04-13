"""
Contexto de request para Multi-tenancy.

Almacena el organization_id activo en un ContextVar
para que cualquier capa del sistema pueda leerlo sin
necesidad de pasarlo como parámetro explícito.
"""
from contextvars import ContextVar
from typing import Optional

_org_id_ctx: ContextVar[Optional[str]] = ContextVar("org_id", default=None)
_branch_id_ctx: ContextVar[Optional[str]] = ContextVar("branch_id", default=None)


def set_tenant_context(org_id: Optional[str], branch_id: Optional[str] = None) -> None:
    """Establece el contexto del tenant actual."""
    _org_id_ctx.set(org_id)
    _branch_id_ctx.set(branch_id)


def get_current_org_id() -> Optional[str]:
    """Retorna el organization_id del tenant activo."""
    return _org_id_ctx.get()


def get_current_branch_id() -> Optional[str]:
    """Retorna el branch_id del tenant activo."""
    return _branch_id_ctx.get()
