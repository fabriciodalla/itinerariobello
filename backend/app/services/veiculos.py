from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Select, and_, case, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
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


def _local_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().app_timezone)


def data_referencia_atual() -> date:
    """'Hoje' no fuso horario do negocio (America/Cuiaba por padrao).

    Usar a data em UTC aqui deslocaria a janela em ~4h: uma viagem feita
    apos as 20h no horario local ja cairia no 'dia seguinte' em UTC, fazendo
    o veiculo aparecer bloqueado (ou liberado) no dia errado."""
    return datetime.now(_local_tz()).date()


def intervalo_do_dia(data_referencia: date) -> tuple[datetime, datetime]:
    """Janela [inicio, fim) do dia local (America/Cuiaba) convertida para UTC,
    ja que Viagem.partida_em e armazenado em UTC."""
    inicio_local = datetime.combine(data_referencia, time.min, tzinfo=_local_tz())
    fim_local = inicio_local + timedelta(days=1)
    return inicio_local.astimezone(timezone.utc), fim_local.astimezone(timezone.utc)


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

    # 0: veiculo principal do usuario | 1: outro veiculo proprio do usuario
    # (segundo carro, etc.) | 2: veiculos de terceiros/alocados da empresa
    prioridade_responsavel = case(
        (and_(Veiculo.usuario_responsavel_id == usuario_id, Veiculo.principal.is_(True)), 0),
        (Veiculo.usuario_responsavel_id == usuario_id, 1),
        else_=2,
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


def usuario_tem_veiculo_ativo(db: Session, usuario_responsavel_id: UUID) -> bool:
    return (
        db.scalar(
            select(Veiculo.id)
            .where(Veiculo.usuario_responsavel_id == usuario_responsavel_id)
            .where(Veiculo.ativo.is_(True))
            .limit(1)
        )
        is not None
    )


def marcar_como_principal(db: Session, veiculo: Veiculo) -> None:
    """Marca o veiculo como principal do seu usuario responsavel, desmarcando
    qualquer outro veiculo que hoje seja o principal desse mesmo usuario (no
    maximo um principal por usuario, reforcado tambem por indice unico no banco)."""
    if veiculo.usuario_responsavel_id is None:
        return
    db.execute(
        update(Veiculo)
        .where(Veiculo.usuario_responsavel_id == veiculo.usuario_responsavel_id)
        .where(Veiculo.id != veiculo.id)
        .where(Veiculo.principal.is_(True))
        .values(principal=False)
    )
    veiculo.principal = True


def listar_veiculos_em_rota(db: Session) -> list[Viagem]:
    query = (
        select(Viagem)
        .options(joinedload(Viagem.veiculo), joinedload(Viagem.usuario))
        .where(Viagem.status == StatusViagem.em_andamento)
        .order_by(Viagem.partida_em.desc())
    )
    return list(db.scalars(query).all())
