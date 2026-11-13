"""Regras de consistencia de quilometragem (RN-041 a RN-043 em
docs/regras-negocio.md): km inicial nao pode ficar abaixo do ultimo km de
chegada do veiculo e saltos/distancias atipicos exigem confirmacao explicita."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import StatusViagem
from app.models.viagem import Viagem


def limite_km_atipico() -> Decimal:
    return Decimal(str(get_settings().km_limite_atipico))


def formatar_km(valor: Decimal) -> str:
    """Formata no padrao do app (pt-BR, 1 casa decimal): 12410.80 -> '12.410,8 km'."""
    texto = f"{Decimal(valor).quantize(Decimal('0.1')):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} km"


def ultimo_km_chegada(db: Session, veiculo_id: UUID) -> Decimal | None:
    """Km final da viagem concluida mais recente do veiculo (pela chegada).

    Usa a viagem mais recente e nao o maior km ja registrado: assim um valor
    absurdo antigo, depois corrigido pelo superior/admin, nao trava o carro."""
    return db.scalar(
        select(Viagem.km_final)
        .where(Viagem.veiculo_id == veiculo_id)
        .where(Viagem.status == StatusViagem.concluida)
        .where(Viagem.km_final.is_not(None))
        .order_by(Viagem.chegada_em.desc().nulls_last(), Viagem.partida_em.desc())
        .limit(1)
    )


def _km_atipico_error(mensagem: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=mensagem)


def validar_km_inicial_partida(
    db: Session,
    veiculo_id: UUID,
    placa: str,
    km_inicial: Decimal,
    confirmar_km_atipico: bool,
) -> None:
    ultimo_km = ultimo_km_chegada(db, veiculo_id)
    if ultimo_km is None:
        return

    if km_inicial < ultimo_km:
        raise _km_atipico_error(
            f"Km inicial deve ser maior ou igual a {formatar_km(ultimo_km)}, "
            f"ultimo km de chegada registrado para o veiculo {placa}."
        )

    limite = limite_km_atipico()
    salto = km_inicial - ultimo_km
    if salto > limite and not confirmar_km_atipico:
        raise _km_atipico_error(
            f"Km inicial {formatar_km(km_inicial)} esta {formatar_km(salto)} acima do ultimo km de chegada "
            f"do veiculo {placa} ({formatar_km(ultimo_km)}). Revise o valor informado e, se estiver correto, "
            "confirme o km atipico."
        )


def validar_km_rodado_chegada(km_inicial: Decimal, km_final: Decimal, confirmar_km_atipico: bool) -> None:
    limite = limite_km_atipico()
    rodado = km_final - km_inicial
    if rodado > limite and not confirmar_km_atipico:
        raise _km_atipico_error(
            f"Km final {formatar_km(km_final)} resulta em {formatar_km(rodado)} rodados nesta viagem "
            f"(km inicial {formatar_km(km_inicial)}). Revise o valor informado e, se estiver correto, "
            "confirme o km atipico."
        )
