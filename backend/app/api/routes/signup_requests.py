from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.enums import StatusSolicitacaoCadastro
from app.models.solicitacao_cadastro import SolicitacaoCadastro
from app.models.usuario import Usuario
from app.schemas.signup_requests import (
    SignupRequestApproveRequest,
    SignupRequestCreateRequest,
    SignupRequestRejectRequest,
    SignupRequestResponse,
)
from app.services.signup_requests import approve_signup_request, create_signup_request, reject_signup_request

router = APIRouter(prefix="/signup-requests", tags=["signup-requests"])


def _get_or_404(db: Session, solicitacao_id: UUID) -> SolicitacaoCadastro:
    solicitacao = db.get(SolicitacaoCadastro, solicitacao_id)
    if solicitacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada.")
    return solicitacao


@router.post("", response_model=SignupRequestResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
def create_public_signup_request(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[str, Form(...)],
    cnh_arquivo: Annotated[UploadFile | None, File()] = None,
    apolice_arquivo: Annotated[UploadFile | None, File()] = None,
) -> SolicitacaoCadastro:
    try:
        data = SignupRequestCreateRequest.model_validate(json.loads(payload))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Campo payload deve conter JSON valido."
        ) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc

    return create_signup_request(db, data, cnh_upload=cnh_arquivo, apolice_upload=apolice_arquivo)


@router.get("/{solicitacao_id}/cnh")
def download_signup_request_cnh(
    solicitacao_id: UUID,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    solicitacao = _get_or_404(db, solicitacao_id)
    if not solicitacao.cnh_arquivo_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNH nao anexada a solicitacao.")
    path = Path(solicitacao.cnh_arquivo_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo da CNH nao encontrado.")
    return FileResponse(path, media_type=solicitacao.cnh_arquivo_mime_type)


@router.get("/{solicitacao_id}/apolice")
def download_signup_request_apolice(
    solicitacao_id: UUID,
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    solicitacao = _get_or_404(db, solicitacao_id)
    if not solicitacao.apolice_arquivo_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apolice nao anexada a solicitacao.")
    path = Path(solicitacao.apolice_arquivo_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo da apolice nao encontrado.")
    return FileResponse(path, media_type=solicitacao.apolice_arquivo_mime_type)


@router.get("", response_model=list[SignupRequestResponse])
def list_signup_requests(
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[StatusSolicitacaoCadastro | None, Query(alias="status")] = None,
) -> list[SolicitacaoCadastro]:
    query = select(SolicitacaoCadastro).order_by(SolicitacaoCadastro.criado_em.desc())
    if status_filter is not None:
        query = query.where(SolicitacaoCadastro.status == status_filter)
    return list(db.scalars(query).all())


@router.get("/pending-count")
def pending_signup_count(
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int]:
    count = db.scalar(
        select(func.count())
        .select_from(SolicitacaoCadastro)
        .where(SolicitacaoCadastro.status == StatusSolicitacaoCadastro.pendente)
    ) or 0
    return {"count": count}


@router.post("/{solicitacao_id}/approve", response_model=SignupRequestResponse)
def approve_public_signup_request(
    solicitacao_id: UUID,
    payload: SignupRequestApproveRequest,
    admin: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SolicitacaoCadastro:
    solicitacao = _get_or_404(db, solicitacao_id)
    return approve_signup_request(db, solicitacao=solicitacao, payload=payload, admin=admin)


@router.post("/{solicitacao_id}/reject", response_model=SignupRequestResponse)
def reject_public_signup_request(
    solicitacao_id: UUID,
    payload: SignupRequestRejectRequest,
    admin: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SolicitacaoCadastro:
    solicitacao = _get_or_404(db, solicitacao_id)
    return reject_signup_request(db, solicitacao=solicitacao, payload=payload, admin=admin)
