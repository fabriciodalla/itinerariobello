from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PerfilUsuario
from app.models.usuario import Usuario


def resolve_pode_aprovar(cargo: str | None, perfil: PerfilUsuario, current: bool) -> bool:
    """Cargo de coordenacao/gerencia (ex.: GERENTE, COORDENADOR REGIONAL) ou perfil
    supervisor sempre garantem pode_aprovar=True, independente do que foi marcado
    explicitamente no formulario. Sem isso, um usuario que tambem dirige (perfil
    motorista) e so recebe o cargo de gestor fica sem acesso aos relatorios da
    equipe (RN-007), pois nada mais deriva pode_aprovar a partir do cargo."""
    if perfil == PerfilUsuario.supervisor:
        return True
    if cargo:
        return True
    return current


def collect_subordinate_ids(db: Session, superior_id: UUID) -> set[UUID]:
    """Retorna os ids de todos os subordinados de superior_id, direta ou indiretamente
    (ex.: gerente -> coordenador regional -> coordenador local -> motorista)."""
    ids: set[UUID] = set()
    frontier = [superior_id]
    while frontier:
        direct = list(db.scalars(select(Usuario.id).where(Usuario.superior_id.in_(frontier))).all())
        new_ids = [i for i in direct if i not in ids]
        ids.update(new_ids)
        frontier = new_ids
    return ids
