from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


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
