from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.enums import (
    PerfilUsuario,
    StatusFechamentoMensal,
    StatusViagem,
    TipoFotoHodometro,
    TipoLocalizacaoGPS,
)
from app.models.fechamento_mensal import FechamentoMensal
from app.models.foto_hodometro import FotoHodometro
from app.models.localizacao_gps import LocalizacaoGPS
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem
from app.schemas.trips import (
    GPSPayload,
    GPSResponse,
    MonthlyClosureClosePayload,
    MonthlyClosureResponse,
    ReportPhotoEvidenceResponse,
    ReportItemResponse,
    TripFinishPayload,
    TripPatchPayload,
    TripResponse,
    TripStartPayload,
)
from app.services.geocoding import normalizar_endereco, reverse_geocode
from app.services.photos import save_trip_photo
from app.services.veiculos import listar_veiculos_disponiveis_para_partida

router = APIRouter(prefix="/trips", tags=["trips"])
photos_router = APIRouter(prefix="/photos", tags=["photos"])
reports_router = APIRouter(prefix="/reports", tags=["reports"])


def validation_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def parse_json_form(raw_payload: str, schema: type[BaseModel]):
    try:
        data = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise validation_error("Campo payload deve conter JSON valido.") from exc

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc


def ensure_can_register_trip(usuario: Usuario) -> None:
    if usuario.perfil != PerfilUsuario.motorista:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem permissao para registrar viagem.")


def ensure_trip_owner(viagem: Viagem, usuario: Usuario) -> None:
    if viagem.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem permissao para esta viagem.")


def can_view_trip(viagem: Viagem, usuario: Usuario) -> bool:
    if viagem.usuario_id == usuario.id:
        return True
    if usuario.perfil in {PerfilUsuario.admin, PerfilUsuario.analista}:
        return True
    return bool(usuario.e_aprovador and viagem.usuario and viagem.usuario.superior_id == usuario.id)


def ensure_can_view_trip(viagem: Viagem, usuario: Usuario) -> None:
    if not can_view_trip(viagem, usuario):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem permissao para esta viagem.")


def ensure_monthly_closer(motorista: Usuario, usuario: Usuario) -> None:
    if not usuario.e_aprovador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sem permissao para fechar relatorio mensal.",
        )
    if usuario.perfil != PerfilUsuario.admin and motorista.superior_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Responsavel pelo fechamento nao e superior imediato do motorista.",
        )


def get_trip_or_404(db: Session, viagem_id: UUID) -> Viagem:
    viagem = db.get(Viagem, viagem_id)
    if viagem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viagem nao encontrada.")
    return viagem


def get_user_or_404(db: Session, usuario_id: UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    return usuario


def get_vehicle_or_404(db: Session, veiculo_id: UUID) -> Veiculo:
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veiculo nao encontrado.")
    return veiculo


def create_gps(viagem_id: UUID, tipo: TipoLocalizacaoGPS, gps: GPSPayload) -> LocalizacaoGPS:
    settings = get_settings()
    endereco = normalizar_endereco(gps.endereco) or reverse_geocode(gps.latitude, gps.longitude, settings)
    return LocalizacaoGPS(
        viagem_id=viagem_id,
        tipo=tipo,
        latitude=gps.latitude,
        longitude=gps.longitude,
        precisao_metros=gps.precisao_metros,
        endereco=endereco,
        capturado_em=datetime.now(timezone.utc),
    )


def create_photo(
    viagem_id: UUID,
    tipo: TipoFotoHodometro,
    upload: UploadFile,
) -> FotoHodometro:
    settings = get_settings()
    arquivo_path, tamanho_bytes, mime_type = save_trip_photo(upload, settings.photos_dir, viagem_id, tipo.value)
    return FotoHodometro(
        viagem_id=viagem_id,
        tipo=tipo,
        arquivo_path=arquivo_path,
        mime_type=mime_type,
        tamanho_bytes=tamanho_bytes,
    )


def get_monthly_closure(db: Session, motorista_id: UUID, ano: int, mes: int) -> FechamentoMensal | None:
    return db.scalar(
        select(FechamentoMensal)
        .where(FechamentoMensal.motorista_id == motorista_id)
        .where(FechamentoMensal.ano == ano)
        .where(FechamentoMensal.mes == mes)
    )


def ensure_monthly_closure_open(db: Session, viagem: Viagem) -> None:
    fechamento = get_monthly_closure(db, viagem.usuario_id, viagem.partida_em.year, viagem.partida_em.month)
    if fechamento and fechamento.status == StatusFechamentoMensal.fechado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Viagem em fechamento mensal fechado nao pode ser editada.",
        )


def photo_download_url(foto_id: UUID) -> str:
    return f"/photos/{foto_id}"


def report_photo_evidence(foto: FotoHodometro | None) -> ReportPhotoEvidenceResponse | None:
    if foto is None:
        return None
    return ReportPhotoEvidenceResponse(
        id=foto.id,
        viagem_id=foto.viagem_id,
        tipo=foto.tipo,
        mime_type=foto.mime_type,
        tamanho_bytes=foto.tamanho_bytes,
        criado_em=foto.criado_em,
        download_url=photo_download_url(foto.id),
    )


def report_gps_evidence(location: LocalizacaoGPS | None) -> GPSResponse | None:
    if location is None:
        return None
    return GPSResponse(
        id=location.id,
        viagem_id=location.viagem_id,
        tipo=location.tipo,
        latitude=location.latitude,
        longitude=location.longitude,
        precisao_metros=location.precisao_metros,
        endereco=location.endereco,
        capturado_em=location.capturado_em,
    )


def latest_photos_by_type(db: Session, viagem_id: UUID) -> dict[TipoFotoHodometro, FotoHodometro]:
    photos_by_type: dict[TipoFotoHodometro, FotoHodometro] = {}
    photos = db.scalars(
        select(FotoHodometro).where(FotoHodometro.viagem_id == viagem_id).order_by(FotoHodometro.criado_em)
    ).all()
    for photo in photos:
        photos_by_type[photo.tipo] = photo
    return photos_by_type


def latest_gps_by_type(db: Session, viagem_id: UUID) -> dict[TipoLocalizacaoGPS, LocalizacaoGPS]:
    gps_by_type: dict[TipoLocalizacaoGPS, LocalizacaoGPS] = {}
    locations = db.scalars(
        select(LocalizacaoGPS).where(LocalizacaoGPS.viagem_id == viagem_id).order_by(LocalizacaoGPS.capturado_em)
    ).all()
    for location in locations:
        gps_by_type[location.tipo] = location
    return gps_by_type


def report_item(db: Session, viagem: Viagem) -> ReportItemResponse:
    fechamento = get_monthly_closure(db, viagem.usuario_id, viagem.partida_em.year, viagem.partida_em.month)
    photos_by_type = latest_photos_by_type(db, viagem.id)
    gps_by_type = latest_gps_by_type(db, viagem.id)
    return ReportItemResponse(
        id=viagem.id,
        usuario_id=viagem.usuario_id,
        usuario_nome=viagem.usuario.nome,
        veiculo_id=viagem.veiculo_id,
        veiculo_placa=viagem.veiculo.placa,
        veiculo_modelo=viagem.veiculo.modelo,
        partida_em=viagem.partida_em,
        chegada_em=viagem.chegada_em,
        km_inicial=viagem.km_inicial,
        km_final=viagem.km_final,
        km_rodado=viagem.km_rodado,
        rota_utilizada=viagem.rota_utilizada,
        foto_hodometro_inicial=report_photo_evidence(photos_by_type.get(TipoFotoHodometro.inicial)),
        foto_hodometro_final=report_photo_evidence(photos_by_type.get(TipoFotoHodometro.final)),
        gps_partida=report_gps_evidence(gps_by_type.get(TipoLocalizacaoGPS.partida)),
        gps_chegada=report_gps_evidence(gps_by_type.get(TipoLocalizacaoGPS.chegada)),
        status=viagem.status,
        fechamento_mensal_id=fechamento.id if fechamento else None,
        status_fechamento=fechamento.status if fechamento else StatusFechamentoMensal.aberto,
        superior_id=fechamento.superior_id if fechamento else None,
        avaliado_em=fechamento.avaliado_em if fechamento else None,
        observacao_fechamento=fechamento.observacao if fechamento else None,
    )


def trip_response(db: Session, viagem: Viagem) -> TripResponse:
    photos_by_type = latest_photos_by_type(db, viagem.id)
    return TripResponse(
        id=viagem.id,
        usuario_id=viagem.usuario_id,
        usuario_nome=viagem.usuario.nome,
        veiculo_id=viagem.veiculo_id,
        veiculo_placa=viagem.veiculo.placa,
        veiculo_modelo=viagem.veiculo.modelo,
        status=viagem.status,
        km_inicial=viagem.km_inicial,
        km_final=viagem.km_final,
        km_rodado=viagem.km_rodado,
        rota_utilizada=viagem.rota_utilizada,
        partida_em=viagem.partida_em,
        chegada_em=viagem.chegada_em,
        foto_hodometro_inicial=report_photo_evidence(photos_by_type.get(TipoFotoHodometro.inicial)),
        foto_hodometro_final=report_photo_evidence(photos_by_type.get(TipoFotoHodometro.final)),
    )


@router.get("", response_model=list[TripResponse])
def list_trips(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TripResponse]:
    query = select(Viagem).order_by(Viagem.partida_em.desc())
    if usuario.perfil in {PerfilUsuario.admin, PerfilUsuario.analista}:
        pass
    elif usuario.e_aprovador:
        query = query.join(Usuario, Viagem.usuario_id == Usuario.id).where(
            or_(Viagem.usuario_id == usuario.id, Usuario.superior_id == usuario.id)
        )
    else:
        query = query.where(Viagem.usuario_id == usuario.id)
    return [trip_response(db, viagem) for viagem in db.scalars(query).all()]


@router.post("/start", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def start_trip(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[str, Form(...)],
    foto_hodometro: Annotated[UploadFile | None, File()] = None,
) -> TripResponse:
    ensure_can_register_trip(usuario)
    if foto_hodometro is None:
        raise validation_error("Foto do hodometro inicial e obrigatoria.")

    data = parse_json_form(payload, TripStartPayload)
    hoje = datetime.now(timezone.utc).date()
    veiculos_permitidos = listar_veiculos_disponiveis_para_partida(db, usuario.id, hoje)
    veiculo = next((item for item in veiculos_permitidos if item.id == data.veiculo_id), None)
    if veiculo is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Veiculo indisponivel para partida.")

    viagem = Viagem(
        usuario_id=usuario.id,
        veiculo_id=veiculo.id,
        status=StatusViagem.em_andamento,
        km_inicial=data.km_inicial,
        partida_em=datetime.now(timezone.utc),
    )
    db.add(viagem)
    db.flush()

    db.add(create_gps(viagem.id, TipoLocalizacaoGPS.partida, data.gps))
    db.add(create_photo(viagem.id, TipoFotoHodometro.inicial, foto_hodometro))
    db.commit()
    db.refresh(viagem)
    return trip_response(db, viagem)


@router.get("/{viagem_id}", response_model=TripResponse)
def get_trip(
    viagem_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TripResponse:
    viagem = get_trip_or_404(db, viagem_id)
    ensure_can_view_trip(viagem, usuario)
    return trip_response(db, viagem)


@router.post("/{viagem_id}/finish", response_model=TripResponse)
def finish_trip(
    viagem_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[str, Form(...)],
    foto_hodometro: Annotated[UploadFile | None, File()] = None,
) -> TripResponse:
    ensure_can_register_trip(usuario)
    if foto_hodometro is None:
        raise validation_error("Foto do hodometro final e obrigatoria.")
    viagem = get_trip_or_404(db, viagem_id)
    ensure_trip_owner(viagem, usuario)
    if viagem.status != StatusViagem.em_andamento:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Viagem nao esta em andamento.")

    data = parse_json_form(payload, TripFinishPayload)
    rota = data.rota_utilizada.strip()
    if not rota:
        raise validation_error("Rota utilizada e obrigatoria.")
    if data.km_final < viagem.km_inicial:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Km final nao pode ser menor que km inicial.")

    viagem.km_final = data.km_final
    viagem.km_rodado = data.km_final - viagem.km_inicial
    viagem.rota_utilizada = rota
    viagem.chegada_em = datetime.now(timezone.utc)
    viagem.status = StatusViagem.concluida
    db.add(create_gps(viagem.id, TipoLocalizacaoGPS.chegada, data.gps))
    db.add(create_photo(viagem.id, TipoFotoHodometro.final, foto_hodometro))
    db.commit()
    db.refresh(viagem)
    return trip_response(db, viagem)


def ensure_can_edit_concluded_trip(viagem: Viagem, usuario: Usuario) -> None:
    if usuario.perfil == PerfilUsuario.admin:
        return
    if usuario.pode_aprovar and viagem.usuario and viagem.usuario.superior_id == usuario.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Somente o superior pode editar esta viagem.")


@router.patch("/{viagem_id}", response_model=TripResponse)
def patch_trip(
    viagem_id: UUID,
    payload: TripPatchPayload,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TripResponse:
    viagem = get_trip_or_404(db, viagem_id)
    if viagem.status != StatusViagem.concluida:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apenas viagens concluidas podem ser editadas pelo superior.",
        )
    ensure_monthly_closure_open(db, viagem)
    ensure_can_edit_concluded_trip(viagem, usuario)

    if payload.rota_utilizada is not None:
        rota = payload.rota_utilizada.strip()
        if not rota:
            raise validation_error("Rota utilizada nao pode ficar em branco.")
        viagem.rota_utilizada = rota
    if payload.km_inicial is not None:
        viagem.km_inicial = payload.km_inicial
    if payload.km_final is not None:
        km_inicial_referencia = payload.km_inicial if payload.km_inicial is not None else viagem.km_inicial
        if payload.km_final < km_inicial_referencia:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Km final nao pode ser menor que km inicial.")
        viagem.km_final = payload.km_final
        viagem.km_rodado = payload.km_final - viagem.km_inicial

    db.commit()
    db.refresh(viagem)
    return trip_response(db, viagem)


@router.post("/{viagem_id}/submit", response_model=TripResponse)
def submit_trip(
    viagem_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TripResponse:
    ensure_can_register_trip(usuario)
    viagem = get_trip_or_404(db, viagem_id)
    ensure_trip_owner(viagem, usuario)
    if viagem.km_final is None or viagem.chegada_em is None or not (viagem.rota_utilizada or "").strip():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Viagem incompleta nao pode ser enviada.")
    viagem.status = StatusViagem.concluida
    db.commit()
    db.refresh(viagem)
    return trip_response(db, viagem)


def individual_approval_gone() -> None:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Aprovacao individual por viagem foi substituida pelo fechamento mensal por motorista.",
    )


@router.post("/{viagem_id}/approve")
def approve_trip_gone(
    viagem_id: UUID,
    _: Annotated[Usuario, Depends(get_current_user)],
    payload: MonthlyClosureClosePayload | None = None,
) -> None:
    individual_approval_gone()


@router.post("/{viagem_id}/reject")
def reject_trip_gone(
    viagem_id: UUID,
    _: Annotated[Usuario, Depends(get_current_user)],
    payload: MonthlyClosureClosePayload | None = None,
) -> None:
    individual_approval_gone()


@router.post("/{viagem_id}/request-adjustment")
def request_adjustment_gone(
    viagem_id: UUID,
    _: Annotated[Usuario, Depends(get_current_user)],
    payload: MonthlyClosureClosePayload | None = None,
) -> None:
    individual_approval_gone()


@router.get("/{viagem_id}/approvals")
def list_approvals_gone(
    viagem_id: UUID,
    _: Annotated[Usuario, Depends(get_current_user)],
) -> None:
    individual_approval_gone()


@router.get("/{viagem_id}/photos", response_model=list[ReportPhotoEvidenceResponse])
def list_trip_photos(
    viagem_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ReportPhotoEvidenceResponse]:
    viagem = get_trip_or_404(db, viagem_id)
    ensure_can_view_trip(viagem, usuario)
    photos = list(
        db.scalars(
            select(FotoHodometro).where(FotoHodometro.viagem_id == viagem.id).order_by(FotoHodometro.criado_em)
        ).all()
    )
    return [evidence for photo in photos if (evidence := report_photo_evidence(photo)) is not None]


@router.get("/{viagem_id}/gps", response_model=list[GPSResponse])
def list_trip_gps(
    viagem_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LocalizacaoGPS]:
    viagem = get_trip_or_404(db, viagem_id)
    ensure_can_view_trip(viagem, usuario)
    return list(
        db.scalars(
            select(LocalizacaoGPS).where(LocalizacaoGPS.viagem_id == viagem.id).order_by(LocalizacaoGPS.capturado_em)
        ).all()
    )


@photos_router.get("/{foto_id}")
def download_photo(
    foto_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    foto = db.get(FotoHodometro, foto_id)
    if foto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto nao encontrada.")
    ensure_can_view_trip(foto.viagem, usuario)
    path = Path(foto.arquivo_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo da foto nao encontrado.")
    return FileResponse(path, media_type=foto.mime_type)


def monthly_query(
    ano: int,
    mes: int,
    motorista_id: UUID | None = None,
    veiculo_id: UUID | None = None,
):
    inicio = datetime(ano, mes, 1, tzinfo=timezone.utc)
    if mes == 12:
        fim = datetime(ano + 1, 1, 1, tzinfo=timezone.utc)
    else:
        fim = datetime(ano, mes + 1, 1, tzinfo=timezone.utc)
    query = select(Viagem).where(Viagem.partida_em >= inicio).where(Viagem.partida_em < fim)
    if motorista_id is not None:
        query = query.where(Viagem.usuario_id == motorista_id)
    if veiculo_id is not None:
        query = query.where(Viagem.veiculo_id == veiculo_id)
    return query.order_by(Viagem.partida_em)


def ensure_report_access(usuario: Usuario) -> None:
    if usuario.perfil not in {PerfilUsuario.analista, PerfilUsuario.admin} and not usuario.pode_aprovar:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem permissao para relatorios.")


def ensure_can_view_monthly_report(motorista: Usuario, usuario: Usuario) -> None:
    if usuario.perfil in {PerfilUsuario.admin, PerfilUsuario.analista}:
        return
    if usuario.pode_aprovar and motorista.superior_id == usuario.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sem permissao para este relatorio mensal.")


def ensure_can_view_vehicle_monthly_report(veiculo: Veiculo, usuario: Usuario) -> None:
    if usuario.perfil == PerfilUsuario.admin:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Somente administrador pode consultar relatorio mensal por veiculo.",
    )


def monthly_query_for_user(
    db: Session,
    ano: int,
    mes: int,
    usuario: Usuario,
    motorista_id: UUID | None = None,
    veiculo_id: UUID | None = None,
):
    ensure_report_access(usuario)
    query = monthly_query(ano, mes, motorista_id, veiculo_id)

    if veiculo_id is not None:
        veiculo = get_vehicle_or_404(db, veiculo_id)
        ensure_can_view_vehicle_monthly_report(veiculo, usuario)

    if motorista_id is not None:
        motorista = get_user_or_404(db, motorista_id)
        ensure_can_view_monthly_report(motorista, usuario)
        return query

    if usuario.perfil in {PerfilUsuario.admin, PerfilUsuario.analista}:
        return query

    return query.join(Usuario, Viagem.usuario_id == Usuario.id).where(Usuario.superior_id == usuario.id)


def closure_response(
    db: Session,
    motorista: Usuario,
    ano: int,
    mes: int,
    fechamento: FechamentoMensal | None = None,
) -> MonthlyClosureResponse:
    viagens = list(db.scalars(monthly_query(ano, mes, motorista.id)).all())
    km_total = sum((viagem.km_rodado or Decimal("0") for viagem in viagens), Decimal("0"))
    if fechamento is None:
        fechamento = get_monthly_closure(db, motorista.id, ano, mes)

    return MonthlyClosureResponse(
        id=fechamento.id if fechamento else None,
        motorista_id=motorista.id,
        motorista_nome=motorista.nome,
        ano=ano,
        mes=mes,
        status=fechamento.status if fechamento else StatusFechamentoMensal.aberto,
        superior_id=fechamento.superior_id if fechamento else None,
        avaliado_em=fechamento.avaliado_em if fechamento else None,
        observacao=fechamento.observacao if fechamento else None,
        total_viagens=len(viagens),
        km_total=km_total,
    )


def validate_closable_trips(viagens: list[Viagem]) -> None:
    if not viagens:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Relatorio mensal sem viagens nao pode ser fechado.",
        )
    for viagem in viagens:
        if viagem.km_final is None or viagem.chegada_em is None or not (viagem.rota_utilizada or "").strip():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Relatorio mensal possui viagem incompleta.",
            )


@reports_router.get("/monthly", response_model=list[ReportItemResponse])
def monthly_report(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    mes: Annotated[int, Query(ge=1, le=12)],
    motorista_id: Annotated[UUID | None, Query()] = None,
    veiculo_id: Annotated[UUID | None, Query()] = None,
) -> list[ReportItemResponse]:
    viagens = list(db.scalars(monthly_query_for_user(db, ano, mes, usuario, motorista_id, veiculo_id)).all())
    return [report_item(db, viagem) for viagem in viagens]


REPORT_EXPORT_FIELDNAMES = [
    "id",
    "usuario_nome",
    "veiculo_placa",
    "partida_em",
    "chegada_em",
    "km_inicial",
    "km_final",
    "km_rodado",
    "rota_utilizada",
    "foto_hodometro_inicial_id",
    "foto_hodometro_inicial_url",
    "foto_hodometro_final_id",
    "foto_hodometro_final_url",
    "gps_partida_latitude",
    "gps_partida_longitude",
    "gps_partida_precisao_metros",
    "gps_partida_endereco",
    "gps_partida_endereco_resolvido",
    "gps_partida_capturado_em",
    "gps_chegada_latitude",
    "gps_chegada_longitude",
    "gps_chegada_precisao_metros",
    "gps_chegada_endereco",
    "gps_chegada_endereco_resolvido",
    "gps_chegada_capturado_em",
    "status",
    "fechamento_mensal_id",
    "status_fechamento",
    "superior_id",
    "avaliado_em",
    "observacao_fechamento",
]


def report_export_row(item: ReportItemResponse) -> dict[str, object]:
    data = item.model_dump(mode="json")

    foto_inicial = data.pop("foto_hodometro_inicial", None) or {}
    foto_final = data.pop("foto_hodometro_final", None) or {}
    gps_partida = data.pop("gps_partida", None) or {}
    gps_chegada = data.pop("gps_chegada", None) or {}

    data.update(
        {
            "foto_hodometro_inicial_id": foto_inicial.get("id"),
            "foto_hodometro_inicial_url": foto_inicial.get("download_url"),
            "foto_hodometro_final_id": foto_final.get("id"),
            "foto_hodometro_final_url": foto_final.get("download_url"),
            "gps_partida_latitude": gps_partida.get("latitude"),
            "gps_partida_longitude": gps_partida.get("longitude"),
            "gps_partida_precisao_metros": gps_partida.get("precisao_metros"),
            "gps_partida_endereco": gps_partida.get("endereco") or gps_partida.get("endereco_exibicao"),
            "gps_partida_endereco_resolvido": gps_partida.get("endereco_resolvido"),
            "gps_partida_capturado_em": gps_partida.get("capturado_em"),
            "gps_chegada_latitude": gps_chegada.get("latitude"),
            "gps_chegada_longitude": gps_chegada.get("longitude"),
            "gps_chegada_precisao_metros": gps_chegada.get("precisao_metros"),
            "gps_chegada_endereco": gps_chegada.get("endereco") or gps_chegada.get("endereco_exibicao"),
            "gps_chegada_endereco_resolvido": gps_chegada.get("endereco_resolvido"),
            "gps_chegada_capturado_em": gps_chegada.get("capturado_em"),
        }
    )
    return data


@reports_router.get("/monthly/export")
def monthly_report_export(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    mes: Annotated[int, Query(ge=1, le=12)],
    motorista_id: Annotated[UUID | None, Query()] = None,
    veiculo_id: Annotated[UUID | None, Query()] = None,
) -> Response:
    from app.services.pdf_report import generate_itinerary_pdf

    viagens = list(db.scalars(monthly_query_for_user(db, ano, mes, usuario, motorista_id, veiculo_id)).all())

    photos_map: dict[str, dict[str, FotoHodometro]] = {}
    gps_map: dict[str, dict[str, LocalizacaoGPS]] = {}
    for viagem in viagens:
        p_by_type = latest_photos_by_type(db, viagem.id)
        photos_map[str(viagem.id)] = {t.value: f for t, f in p_by_type.items()}
        g_by_type = latest_gps_by_type(db, viagem.id)
        gps_map[str(viagem.id)] = {t.value: g for t, g in g_by_type.items()}

    focus = "motorista"
    entidade_nome = "Todos"
    filename_prefix = "relatorio"
    if veiculo_id is not None:
        veiculo = get_vehicle_or_404(db, veiculo_id)
        entidade_nome = f"{veiculo.placa} / {veiculo.modelo}" if veiculo.modelo else veiculo.placa
        focus = "veiculo"
        filename_prefix = f"relatorio-veiculo-{veiculo.placa}"
    else:
        nomes = {v.usuario.nome for v in viagens if v.usuario}
        entidade_nome = next(iter(nomes)) if len(nomes) == 1 else "Todos"

    pdf_bytes = generate_itinerary_pdf(entidade_nome, ano, mes, viagens, photos_map, gps_map, focus=focus)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename_prefix}-{ano}-{mes:02d}.pdf"'},
    )


@reports_router.get("/monthly/closures", response_model=list[MonthlyClosureResponse])
def list_monthly_closures(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    mes: Annotated[int, Query(ge=1, le=12)],
    motorista_id: Annotated[UUID | None, Query()] = None,
) -> list[MonthlyClosureResponse]:
    viagens = list(db.scalars(monthly_query_for_user(db, ano, mes, usuario, motorista_id)).all())
    motoristas = {viagem.usuario_id: viagem.usuario for viagem in viagens}
    return [closure_response(db, motorista, ano, mes) for motorista in motoristas.values()]


@reports_router.get("/monthly/closures/{motorista_id}", response_model=MonthlyClosureResponse)
def get_monthly_closure_detail(
    motorista_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    mes: Annotated[int, Query(ge=1, le=12)],
) -> MonthlyClosureResponse:
    motorista = get_user_or_404(db, motorista_id)
    ensure_can_view_monthly_report(motorista, usuario)
    return closure_response(db, motorista, ano, mes)


def close_monthly_closure(
    db: Session,
    motorista: Usuario,
    superior: Usuario,
    ano: int,
    mes: int,
    observacao: str | None,
) -> MonthlyClosureResponse:
    ensure_monthly_closer(motorista, superior)
    observacao_limpa = observacao.strip() if observacao is not None else None

    viagens = list(db.scalars(monthly_query(ano, mes, motorista.id)).all())
    validate_closable_trips(viagens)

    fechamento = get_monthly_closure(db, motorista.id, ano, mes)
    if fechamento is None:
        fechamento = FechamentoMensal(motorista_id=motorista.id, ano=ano, mes=mes)
        db.add(fechamento)

    fechamento.superior_id = superior.id
    fechamento.status = StatusFechamentoMensal.fechado
    fechamento.observacao = observacao_limpa
    fechamento.avaliado_em = datetime.now(timezone.utc)

    db.commit()
    db.refresh(fechamento)
    return closure_response(db, motorista, ano, mes, fechamento)


@reports_router.post("/monthly/closures/{motorista_id}/close", response_model=MonthlyClosureResponse)
def close_monthly_closure_endpoint(
    motorista_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    mes: Annotated[int, Query(ge=1, le=12)],
    payload: MonthlyClosureClosePayload | None = None,
) -> MonthlyClosureResponse:
    motorista = get_user_or_404(db, motorista_id)
    return close_monthly_closure(
        db,
        motorista,
        usuario,
        ano,
        mes,
        payload.observacao if payload else None,
    )


def monthly_closure_decision_gone() -> None:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Aprovacao/reprovacao do fechamento mensal foi substituida por fechamento aberto/fechado.",
    )


@reports_router.post("/monthly/closures/{motorista_id}/approve")
def approve_monthly_closure_gone(
    motorista_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    mes: Annotated[int, Query(ge=1, le=12)],
    payload: MonthlyClosureClosePayload | None = None,
) -> None:
    monthly_closure_decision_gone()


@reports_router.post("/monthly/closures/{motorista_id}/reject")
def reject_monthly_closure_gone(
    motorista_id: UUID,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ano: Annotated[int, Query(ge=2000, le=2100)],
    mes: Annotated[int, Query(ge=1, le=12)],
    payload: MonthlyClosureClosePayload | None = None,
) -> None:
    monthly_closure_decision_gone()
