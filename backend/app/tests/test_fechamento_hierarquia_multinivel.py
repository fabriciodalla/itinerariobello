from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from assertions import assert_forbidden, response_items
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, StatusViagem, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.fechamento_mensal import FechamentoMensal
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem


def current_report_params() -> dict[str, int]:
    today = date.today()
    return {"ano": today.year, "mes": today.month}


def _auth_headers(usuario_id) -> dict[str, str]:
    settings = get_settings()
    token = create_access_token(str(usuario_id), settings.secret_key, settings.access_token_expire_minutes)
    return {"Authorization": f"Bearer {token}"}


class _Cadeia:
    """Monta gerente -> coordenador regional -> coordenador local -> motorista, cada um
    apontando para o anterior via superior_id, com uma viagem concluida do motorista no mes atual."""

    def __init__(self, db):
        self.db = db
        self.created: list = []
        suffix = uuid4().hex[:6]

        self.gerente = Usuario(
            nome="Gerente Teste",
            email=f"gerente.hierarquia.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="GERENTE",
            pode_aprovar=True,
        )
        db.add(self.gerente)
        db.flush()

        self.coordenador_regional = Usuario(
            nome="Coordenador Regional Teste",
            email=f"coord.regional.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="COORDENADOR REGIONAL",
            pode_aprovar=True,
            superior_id=self.gerente.id,
        )
        db.add(self.coordenador_regional)
        db.flush()

        self.coordenador_local = Usuario(
            nome="Coordenador Local Teste",
            email=f"coord.local.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.supervisor,
            cargo="COORDENADOR LOCAL",
            pode_aprovar=True,
            superior_id=self.coordenador_regional.id,
        )
        db.add(self.coordenador_local)
        db.flush()

        self.motorista = Usuario(
            nome="Motorista Neto Hierarquia Teste",
            email=f"motorista.neto.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
            superior_id=self.coordenador_local.id,
        )
        db.add(self.motorista)
        db.flush()

        self.veiculo = Veiculo(
            placa=f"NT{suffix}".upper(),
            modelo="Veiculo Neto Hierarquia",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=self.motorista.id,
        )
        db.add(self.veiculo)
        db.flush()

        partida_em = datetime.now(timezone.utc)
        chegada_em = partida_em.replace(hour=min(partida_em.hour + 1, 23))
        self.viagem = Viagem(
            usuario_id=self.motorista.id,
            veiculo_id=self.veiculo.id,
            status=StatusViagem.concluida,
            km_inicial=Decimal("500.00"),
            km_final=Decimal("540.00"),
            km_rodado=Decimal("40.00"),
            rota_utilizada="Rota neto hierarquia",
            partida_em=partida_em,
            chegada_em=chegada_em,
        )
        db.add(self.viagem)
        db.commit()

        self.created = [
            self.viagem,
            self.veiculo,
            self.motorista,
            self.coordenador_local,
            self.coordenador_regional,
            self.gerente,
        ]

    def cleanup(self) -> None:
        self.db.rollback()
        for fechamento in self.db.scalars(
            select(FechamentoMensal).where(FechamentoMensal.motorista_id == self.motorista.id)
        ).all():
            self.db.delete(fechamento)
        for item in self.created:
            persisted = self.db.get(type(item), item.id)
            if persisted is not None:
                self.db.delete(persisted)
        self.db.commit()
        self.db.close()


@pytest.mark.relatorio
@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RN-031",))
def test_gerente_visualiza_relatorio_e_fechamento_de_subordinado_indireto(api_client):
    db = SessionLocal()
    cadeia = _Cadeia(db)
    try:
        headers = _auth_headers(cadeia.gerente.id)

        report_response = api_client.get("/reports/monthly", params=current_report_params(), headers=headers)
        assert report_response.status_code == 200, report_response.text
        report_motoristas = {str(item["usuario_id"]) for item in response_items(report_response)}
        assert str(cadeia.motorista.id) in report_motoristas

        closures_response = api_client.get(
            "/reports/monthly/closures", params=current_report_params(), headers=headers
        )
        assert closures_response.status_code == 200, closures_response.text
        closure_motoristas = {str(item["motorista_id"]) for item in response_items(closures_response)}
        assert str(cadeia.motorista.id) in closure_motoristas

        detail_response = api_client.get(
            f"/reports/monthly/closures/{cadeia.motorista.id}",
            params=current_report_params(),
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text

        filtered_response = api_client.get(
            "/reports/monthly",
            params={**current_report_params(), "motorista_id": str(cadeia.motorista.id)},
            headers=headers,
        )
        assert filtered_response.status_code == 200, filtered_response.text
    finally:
        cadeia.cleanup()


@pytest.mark.relatorio
@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RN-020", "RN-032"))
def test_gerente_nao_fecha_mes_de_subordinado_indireto(api_client):
    db = SessionLocal()
    cadeia = _Cadeia(db)
    try:
        headers = _auth_headers(cadeia.gerente.id)

        close_response = api_client.post(
            f"/reports/monthly/closures/{cadeia.motorista.id}/close",
            params=current_report_params(),
            json={},
            headers=headers,
        )
        assert_forbidden(close_response)

        headers_local = _auth_headers(cadeia.coordenador_local.id)
        close_response_local = api_client.post(
            f"/reports/monthly/closures/{cadeia.motorista.id}/close",
            params=current_report_params(),
            json={},
            headers=headers_local,
        )
        assert close_response_local.status_code == 200, close_response_local.text
    finally:
        cadeia.cleanup()
