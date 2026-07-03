from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import Select, case, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import StatusViagem, TipoDisponibilidadeVeiculo
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem

STATUS_BLOQUEIA_VEICULO_NO_DIA = (
    StatusViagem.em_andamento,
    StatusViagem.concluida,
)

MARCAS_PREFIXO_MODELO = (
    "MERCEDES-BENZ",
    "MERCEDES BENZ",
    "VOLKSWAGEN",
    "CHEVROLET",
    "MITSUBISHI",
    "HYUNDAI",
    "RENAULT",
    "TOYOTA",
    "HONDA",
    "FIAT",
    "FORD",
    "JEEP",
    "KIA",
    "NISSAN",
    "PEUGEOT",
    "CITROEN",
    "CITROËN",
    "AUDI",
    "BMW",
    "VOLVO",
    "VW",
    "GM",
)


def _compactar_espacos(valor: str) -> str:
    return " ".join((valor or "").strip().split())


def normalizar_modelo_veiculo(valor: str) -> str:
    modelo = _compactar_espacos(valor)
    partes_barra = [parte.strip() for parte in modelo.split("/") if parte.strip()]
    if len(partes_barra) >= 2:
        modelo = partes_barra[-1]

    modelo = _compactar_espacos(modelo).upper()
    for marca in MARCAS_PREFIXO_MODELO:
        prefixo = f"{marca} "
        if modelo.startswith(prefixo):
            return _compactar_espacos(modelo[len(prefixo) :])
    return modelo


def normalizar_marca_veiculo(valor: str | None) -> str | None:
    marca = _compactar_espacos(valor or "")
    return marca.upper() if marca else None


def intervalo_do_dia(data_referencia: date) -> tuple[datetime, datetime]:
    inicio = datetime.combine(data_referencia, time.min, tzinfo=timezone.utc)
    return inicio, inicio + timedelta(days=1)


def consulta_veiculos_disponiveis_para_partida(
    usuario_id: UUID,
    data_referencia: date,
) -> Select[tuple[Veiculo]]:
    inicio, fim = intervalo_do_dia(data_referencia)

    veiculos_bloqueados = (
        select(Viagem.veiculo_id)
        .where(Viagem.partida_em >= inicio)
        .where(Viagem.partida_em < fim)
        .where(Viagem.status.in_(STATUS_BLOQUEIA_VEICULO_NO_DIA))
    )

    prioridade_responsavel = case(
        (Veiculo.usuario_responsavel_id == usuario_id, 0),
        else_=1,
    )

    return (
        select(Veiculo)
        .where(Veiculo.ativo.is_(True))
        .where(
            or_(
                Veiculo.tipo_disponibilidade == TipoDisponibilidadeVeiculo.alocado,
                Veiculo.usuario_responsavel_id == usuario_id,
            )
        )
        .where(Veiculo.id.not_in(veiculos_bloqueados))
        .order_by(prioridade_responsavel, Veiculo.placa)
    )


def listar_veiculos_disponiveis_para_partida(
    db: Session,
    usuario_id: UUID,
    data_referencia: date,
) -> list[Veiculo]:
    return list(db.scalars(consulta_veiculos_disponiveis_para_partida(usuario_id, data_referencia)).all())


def listar_veiculos_em_rota(db: Session) -> list[Viagem]:
    query = (
        select(Viagem)
        .options(joinedload(Viagem.veiculo), joinedload(Viagem.usuario))
        .where(Viagem.status == StatusViagem.em_andamento)
        .order_by(Viagem.partida_em.desc())
    )
    return list(db.scalars(query).all())
