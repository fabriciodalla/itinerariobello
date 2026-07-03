from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import (
    PerfilUsuario,
    StatusSolicitacaoCadastro,
    TipoDisponibilidadeVeiculo,
    TipoVeiculo,
)
from app.models.solicitacao_cadastro import SolicitacaoCadastro
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.signup_requests import (
    SignupRequestApproveRequest,
    SignupRequestCreateRequest,
    SignupRequestRejectRequest,
)
from app.services.veiculos import normalizar_marca_veiculo, normalizar_modelo_veiculo


def create_signup_request(db: Session, payload: SignupRequestCreateRequest) -> SolicitacaoCadastro:
    email = str(payload.email).strip().lower()
    placa = payload.veiculo_placa.strip().upper()

    if db.scalar(select(Usuario).where(Usuario.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado.")

    pending = db.scalar(
        select(SolicitacaoCadastro)
        .where(SolicitacaoCadastro.email == email)
        .where(SolicitacaoCadastro.status == StatusSolicitacaoCadastro.pendente)
    )
    if pending is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solicitacao ja registrada.")

    solicitacao = SolicitacaoCadastro(
        nome=payload.nome.strip(),
        email=email,
        cargo=payload.cargo.strip(),
        superior=payload.superior.strip(),
        veiculo_placa=placa,
        veiculo_modelo=normalizar_modelo_veiculo(payload.veiculo_modelo),
        veiculo_marca=normalizar_marca_veiculo(payload.veiculo_marca) or "",
        observacao=payload.observacao.strip() if payload.observacao else None,
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def approve_signup_request(
    db: Session,
    *,
    solicitacao: SolicitacaoCadastro,
    payload: SignupRequestApproveRequest,
    admin: Usuario,
) -> SolicitacaoCadastro:
    _ensure_pending(solicitacao)

    if db.scalar(select(Usuario).where(Usuario.email == solicitacao.email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado.")

    if payload.superior_id is not None and db.get(Usuario, payload.superior_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Superior nao encontrado.")

    usuario = Usuario(
        nome=solicitacao.nome,
        email=solicitacao.email,
        senha_hash=hash_password(payload.senha_temporaria),
        cargo=solicitacao.cargo,
        perfil=payload.perfil,
        superior_id=payload.superior_id,
        pode_aprovar=payload.pode_aprovar or payload.perfil == PerfilUsuario.supervisor,
        ativo=True,
    )
    db.add(usuario)
    db.flush()

    veiculo = _create_or_assign_vehicle(db, solicitacao, usuario, payload)

    now = datetime.now(timezone.utc)
    solicitacao.status = StatusSolicitacaoCadastro.aprovada
    solicitacao.usuario_id = usuario.id
    solicitacao.veiculo_id = veiculo.id
    solicitacao.processado_por_id = admin.id
    solicitacao.processado_em = now
    solicitacao.motivo_recusa = None
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def reject_signup_request(
    db: Session,
    *,
    solicitacao: SolicitacaoCadastro,
    payload: SignupRequestRejectRequest,
    admin: Usuario,
) -> SolicitacaoCadastro:
    _ensure_pending(solicitacao)
    solicitacao.status = StatusSolicitacaoCadastro.rejeitada
    solicitacao.processado_por_id = admin.id
    solicitacao.processado_em = datetime.now(timezone.utc)
    solicitacao.motivo_recusa = payload.motivo.strip()
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def _ensure_pending(solicitacao: SolicitacaoCadastro) -> None:
    if solicitacao.status != StatusSolicitacaoCadastro.pendente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Solicitacao ja processada.")


def _create_or_assign_vehicle(
    db: Session,
    solicitacao: SolicitacaoCadastro,
    usuario: Usuario,
    payload: SignupRequestApproveRequest,
) -> Veiculo:
    placa = solicitacao.veiculo_placa.strip().upper()
    modelo = normalizar_modelo_veiculo(solicitacao.veiculo_modelo)
    marca = normalizar_marca_veiculo(solicitacao.veiculo_marca) or ""
    solicitacao.veiculo_modelo = modelo
    solicitacao.veiculo_marca = marca

    disponibilidade = payload.tipo_disponibilidade
    if disponibilidade is None:
        disponibilidade = (
            TipoDisponibilidadeVeiculo.fixo
            if payload.tipo_veiculo in {TipoVeiculo.proprio, TipoVeiculo.alugado}
            else TipoDisponibilidadeVeiculo.alocado
        )

    usuario_responsavel_id = usuario.id if disponibilidade == TipoDisponibilidadeVeiculo.fixo else None
    veiculo = db.scalar(select(Veiculo).where(Veiculo.placa == placa))
    if veiculo is not None:
        if (
            veiculo.tipo_disponibilidade == TipoDisponibilidadeVeiculo.fixo
            and veiculo.usuario_responsavel_id is not None
            and veiculo.usuario_responsavel_id != usuario.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Veiculo ja vinculado a outro usuario.",
            )
        veiculo.modelo = modelo
        veiculo.marca = marca
        veiculo.tipo = payload.tipo_veiculo
        veiculo.tipo_disponibilidade = disponibilidade
        veiculo.usuario_responsavel_id = usuario_responsavel_id
        veiculo.ativo = True
        return veiculo

    veiculo = Veiculo(
        placa=placa,
        modelo=modelo,
        marca=marca,
        tipo=payload.tipo_veiculo,
        tipo_disponibilidade=disponibilidade,
        usuario_responsavel_id=usuario_responsavel_id,
        ativo=True,
    )
    db.add(veiculo)
    db.flush()
    return veiculo
