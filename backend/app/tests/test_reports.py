from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from assertions import (
    assert_forbidden,
    assert_has_any_key,
    assert_validation_error,
    json_body,
    response_items,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, StatusViagem, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.models.viagem import Viagem
from factories import finish_payload, start_payload, without_nested_key
from helpers import create_trip_ready_for_monthly_closure, post_trip_finish, post_trip_start


def current_report_params() -> dict[str, int]:
    today = date.today()
    return {"ano": today.year, "mes": today.month}


def assert_pdf_response(response) -> None:
    assert response.status_code == 200, response.text
    assert response.content.startswith(b"%PDF"), response.content[:40]
    assert "application/pdf" in response.headers.get("content-type", "")
    assert "text/html" not in response.headers.get("content-type", "")


def assert_report_item_contains_required_fields(item: dict) -> None:
    assert_has_any_key(item, "id", "viagem_id")
    assert_has_any_key(item, "usuario", "usuario_nome", "motorista", "nome_usuario")
    assert_has_any_key(item, "veiculo", "placa", "veiculo_placa")
    assert_has_any_key(item, "partida_em", "data_partida")
    assert_has_any_key(item, "chegada_em", "data_chegada")
    assert_has_any_key(item, "km_inicial")
    assert_has_any_key(item, "km_final")
    assert_has_any_key(item, "km_rodado")
    assert_has_any_key(item, "rota_utilizada", "rota")
    assert_has_any_key(item, "status")
    assert_has_any_key(item, "status_fechamento")


def assert_report_item_contains_required_evidence(item: dict) -> None:
    foto_inicial = item.get("foto_hodometro_inicial")
    foto_final = item.get("foto_hodometro_final")
    gps_partida = item.get("gps_partida")
    gps_chegada = item.get("gps_chegada")

    assert isinstance(foto_inicial, dict), item
    assert isinstance(foto_final, dict), item
    assert foto_inicial.get("download_url", "").startswith("/photos/"), item
    assert foto_final.get("download_url", "").startswith("/photos/"), item
    assert foto_inicial.get("tipo") == "inicial", item
    assert foto_final.get("tipo") == "final", item

    assert isinstance(gps_partida, dict), item
    assert isinstance(gps_chegada, dict), item
    assert gps_partida.get("tipo") == "partida", item
    assert gps_chegada.get("tipo") == "chegada", item
    assert gps_partida.get("latitude") is not None, item
    assert gps_partida.get("longitude") is not None, item
    assert gps_partida.get("endereco_resolvido") in {True, False}, item
    assert gps_chegada.get("latitude") is not None, item
    assert gps_chegada.get("longitude") is not None, item
    assert gps_chegada.get("endereco_resolvido") in {True, False}, item


@pytest.mark.relatorio
@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-016", "RNF-004"))
def test_motorista_nao_acessa_relatorio_mensal(api_client, motorista_auth_headers):
    response = api_client.get(
        "/reports/monthly",
        params=current_report_params(),
        headers=motorista_auth_headers,
    )

    assert_forbidden(response)


@pytest.mark.relatorio
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-016", "RF-017"))
def test_analista_consulta_relatorio_mensal(
    api_client,
    motorista_auth_headers,
    aprovador_auth_headers,
    analista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)
    close_response = api_client.post(
        f"/reports/monthly/closures/{trip['usuario_id']}/close",
        params=current_report_params(),
        json={},
        headers=aprovador_auth_headers,
    )
    assert close_response.status_code == 200, close_response.text

    response = api_client.get(
        "/reports/monthly",
        params=current_report_params(),
        headers=analista_auth_headers,
    )

    assert response.status_code == 200, response.text
    data = json_body(response)
    assert isinstance(data, (dict, list))
    items = response_items(response)
    trip_item = next(
        (item for item in items if str(item.get("id") or item.get("viagem_id")) == trip["id"]),
        None,
    )
    assert trip_item is not None, f"Relatorio mensal deve conter a viagem concluida {trip['id']}: {items}"
    assert_report_item_contains_required_fields(trip_item)
    assert_report_item_contains_required_evidence(trip_item)
    assert trip_item["status"] == "concluida"
    assert trip_item["status_fechamento"] == "fechado"


@pytest.mark.relatorio
@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-014", "RF-016", "RN-020", "RNF-004"))
def test_aprovador_consulta_fechamento_mensal_somente_de_subordinados(api_client):
    db = SessionLocal()
    created = []
    try:
        aprovador = db.scalar(select(Usuario).where(Usuario.email == "aprovador.teste@bello.local"))
        if aprovador is None:
            aprovador = Usuario(
                nome="Aprovador Teste",
                email="aprovador.teste@bello.local",
                senha_hash="hash",
                perfil=PerfilUsuario.motorista,
                cargo="Coordenador",
                pode_aprovar=True,
            )
            db.add(aprovador)
            db.flush()
            created.append(aprovador)
        assert aprovador.pode_aprovar is True
        headers = {
            "Authorization": (
                "Bearer "
                + create_access_token(
                    str(aprovador.id),
                    get_settings().secret_key,
                    get_settings().access_token_expire_minutes,
                )
            )
        }

        suffix = uuid4().hex[:6]
        subordinado = Usuario(
            nome="Motorista Subordinado Fechamento Teste",
            email=f"subordinado.fechamento.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
            superior_id=aprovador.id,
        )
        fora_da_hierarquia = Usuario(
            nome="Motorista Fora Hierarquia Fechamento Teste",
            email=f"fora.hierarquia.fechamento.{suffix}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([subordinado, fora_da_hierarquia])
        db.flush()
        created.extend([subordinado, fora_da_hierarquia])

        veiculo_subordinado = Veiculo(
            placa=f"FS{suffix}".upper(),
            modelo="Veiculo Subordinado",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=subordinado.id,
        )
        veiculo_fora_da_hierarquia = Veiculo(
            placa=f"FH{suffix}".upper(),
            modelo="Veiculo Fora Hierarquia",
            tipo=TipoVeiculo.proprio,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
            usuario_responsavel_id=fora_da_hierarquia.id,
        )
        db.add_all([veiculo_subordinado, veiculo_fora_da_hierarquia])
        db.flush()
        created.extend([veiculo_subordinado, veiculo_fora_da_hierarquia])

        partida_em = datetime.now(timezone.utc)
        chegada_em = partida_em.replace(hour=min(partida_em.hour + 1, 23))
        viagem_subordinado = Viagem(
            usuario_id=subordinado.id,
            veiculo_id=veiculo_subordinado.id,
            status=StatusViagem.concluida,
            km_inicial=Decimal("1000.00"),
            km_final=Decimal("1050.00"),
            km_rodado=Decimal("50.00"),
            rota_utilizada="Rota subordinada",
            partida_em=partida_em,
            chegada_em=chegada_em,
        )
        viagem_fora_da_hierarquia = Viagem(
            usuario_id=fora_da_hierarquia.id,
            veiculo_id=veiculo_fora_da_hierarquia.id,
            status=StatusViagem.concluida,
            km_inicial=Decimal("2000.00"),
            km_final=Decimal("2075.00"),
            km_rodado=Decimal("75.00"),
            rota_utilizada="Rota fora da hierarquia",
            partida_em=partida_em,
            chegada_em=chegada_em,
        )
        db.add_all([viagem_subordinado, viagem_fora_da_hierarquia])
        db.commit()
        created.extend([viagem_subordinado, viagem_fora_da_hierarquia])

        closures_response = api_client.get(
            "/reports/monthly/closures",
            params=current_report_params(),
            headers=headers,
        )
        assert closures_response.status_code == 200, closures_response.text
        closure_motoristas = {str(item["motorista_id"]) for item in response_items(closures_response)}
        assert str(subordinado.id) in closure_motoristas
        assert str(fora_da_hierarquia.id) not in closure_motoristas

        report_response = api_client.get(
            "/reports/monthly",
            params=current_report_params(),
            headers=headers,
        )
        assert report_response.status_code == 200, report_response.text
        report_motoristas = {str(item["usuario_id"]) for item in response_items(report_response)}
        assert str(subordinado.id) in report_motoristas
        assert str(fora_da_hierarquia.id) not in report_motoristas

        detail_response = api_client.get(
            f"/reports/monthly/closures/{fora_da_hierarquia.id}",
            params=current_report_params(),
            headers=headers,
        )
        assert_forbidden(detail_response)
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.relatorio
@pytest.mark.foto
@pytest.mark.gps
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-016", "RF-017"))
def test_analista_exporta_relatorio_mensal(
    api_client,
    motorista_auth_headers,
    analista_auth_headers,
    test_vehicle_id,
):
    trip = create_trip_ready_for_monthly_closure(api_client, motorista_auth_headers, test_vehicle_id)

    response = api_client.get(
        "/reports/monthly/export",
        params=current_report_params(),
        headers=analista_auth_headers,
    )

    assert trip["id"]
    assert_pdf_response(response)


@pytest.mark.relatorio
@pytest.mark.gps
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-016", "RN-023"))
def test_relatorio_mensal_informa_endereco_nao_resolvido_quando_indisponivel(
    api_client,
    motorista_auth_headers,
    analista_auth_headers,
    test_vehicle_id,
    monkeypatch,
):
    import app.api.routes.trips as trips_route

    monkeypatch.setattr(trips_route, "reverse_geocode", lambda latitude, longitude, settings: None)
    start_data = without_nested_key(start_payload(test_vehicle_id), "gps", "endereco")
    start_response = post_trip_start(api_client, motorista_auth_headers, start_data)
    assert start_response.status_code == 201, start_response.text
    trip_id = start_response.json()["id"]

    finish_data = without_nested_key(finish_payload(), "gps", "endereco")
    finish_response = post_trip_finish(api_client, trip_id, motorista_auth_headers, finish_data)
    assert finish_response.status_code == 200, finish_response.text

    response = api_client.get(
        "/reports/monthly",
        params=current_report_params(),
        headers=analista_auth_headers,
    )

    assert response.status_code == 200, response.text
    items = response_items(response)
    trip_item = next((item for item in items if item.get("id") == trip_id), None)
    assert trip_item is not None, response.text
    assert trip_item["gps_partida"]["endereco"] is None
    assert trip_item["gps_partida"]["endereco_exibicao"] == "Endereco nao resolvido"
    assert trip_item["gps_partida"]["endereco_resolvido"] is False
    assert trip_item["gps_chegada"]["endereco"] is None
    assert trip_item["gps_chegada"]["endereco_exibicao"] == "Endereco nao resolvido"
    assert trip_item["gps_chegada"]["endereco_resolvido"] is False


@pytest.mark.relatorio
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-016", "RF-017"))
def test_admin_consulta_e_exporta_relatorio_mensal_por_veiculo_alocado(api_client):
    db = SessionLocal()
    created = []
    try:
        settings = get_settings()
        suffix = uuid4().hex[:6].upper()
        admin = Usuario(
            nome="Admin Relatorio Veiculo",
            email=f"admin.relatorio.veiculo.{suffix.lower()}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.admin,
        )
        vendedor = Usuario(
            nome="Vendedor Veiculo Alocado",
            email=f"vendedor.veiculo.{suffix.lower()}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        outro_vendedor = Usuario(
            nome="Outro Vendedor Veiculo",
            email=f"outro.vendedor.veiculo.{suffix.lower()}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.motorista,
        )
        db.add_all([admin, vendedor, outro_vendedor])
        db.flush()
        created.extend([admin, vendedor, outro_vendedor])

        veiculo_alocado = Veiculo(
            placa=f"AL{suffix[:5]}",
            modelo="Veiculo Alocado",
            tipo=TipoVeiculo.empresa,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
        )
        outro_veiculo = Veiculo(
            placa=f"AO{suffix[:5]}",
            modelo="Outro Alocado",
            tipo=TipoVeiculo.empresa,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
        )
        db.add_all([veiculo_alocado, outro_veiculo])
        db.flush()
        created.extend([veiculo_alocado, outro_veiculo])

        params_base = current_report_params()
        partida_em = datetime(params_base["ano"], params_base["mes"], 5, 8, tzinfo=timezone.utc)
        chegada_em = datetime(params_base["ano"], params_base["mes"], 5, 18, tzinfo=timezone.utc)
        viagem_do_veiculo = Viagem(
            usuario_id=vendedor.id,
            veiculo_id=veiculo_alocado.id,
            status=StatusViagem.concluida,
            km_inicial=Decimal("1000.00"),
            km_final=Decimal("1060.00"),
            km_rodado=Decimal("60.00"),
            rota_utilizada="Cliente A -> Cliente B",
            partida_em=partida_em,
            chegada_em=chegada_em,
        )
        viagem_de_outro_veiculo = Viagem(
            usuario_id=outro_vendedor.id,
            veiculo_id=outro_veiculo.id,
            status=StatusViagem.concluida,
            km_inicial=Decimal("2000.00"),
            km_final=Decimal("2030.00"),
            km_rodado=Decimal("30.00"),
            rota_utilizada="Cliente C",
            partida_em=partida_em,
            chegada_em=chegada_em,
        )
        db.add_all([viagem_do_veiculo, viagem_de_outro_veiculo])
        db.commit()
        created.extend([viagem_do_veiculo, viagem_de_outro_veiculo])

        headers = {
            "Authorization": (
                "Bearer "
                + create_access_token(
                    str(admin.id),
                    settings.secret_key,
                    settings.access_token_expire_minutes,
                )
            )
        }
        params = {**params_base, "veiculo_id": str(veiculo_alocado.id)}

        response = api_client.get("/reports/monthly", params=params, headers=headers)

        assert response.status_code == 200, response.text
        items = response_items(response)
        assert [item["id"] for item in items] == [str(viagem_do_veiculo.id)]
        assert items[0]["veiculo_id"] == str(veiculo_alocado.id)
        assert items[0]["usuario_nome"] == vendedor.nome

        export_response = api_client.get("/reports/monthly/export", params=params, headers=headers)
        assert_pdf_response(export_response)
        assert f"relatorio-veiculo-{veiculo_alocado.placa}" in export_response.headers.get("content-disposition", "")
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.relatorio
@pytest.mark.permissao
@pytest.mark.risco(peso=100, criticidade="critica", area="permissao", referencias=("RF-016", "RNF-004"))
def test_analista_nao_consulta_relatorio_mensal_por_veiculo(api_client):
    db = SessionLocal()
    created = []
    try:
        settings = get_settings()
        suffix = uuid4().hex[:6].upper()
        analista = Usuario(
            nome="Analista Sem Relatorio Veiculo",
            email=f"analista.relatorio.veiculo.{suffix.lower()}@bello.local",
            senha_hash="hash",
            perfil=PerfilUsuario.analista,
        )
        veiculo = Veiculo(
            placa=f"PV{suffix[:5]}",
            modelo="Veiculo Restrito",
            tipo=TipoVeiculo.empresa,
            tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
        )
        db.add_all([analista, veiculo])
        db.commit()
        created.extend([analista, veiculo])

        headers = {
            "Authorization": (
                "Bearer "
                + create_access_token(
                    str(analista.id),
                    settings.secret_key,
                    settings.access_token_expire_minutes,
                )
            )
        }
        params = {**current_report_params(), "veiculo_id": str(veiculo.id)}

        response = api_client.get("/reports/monthly", params=params, headers=headers)

        assert_forbidden(response)
    finally:
        db.rollback()
        for item in reversed(created):
            persisted = db.get(type(item), item.id)
            if persisted is not None:
                db.delete(persisted)
        db.commit()
        db.close()


@pytest.mark.relatorio
@pytest.mark.risco(peso=50, criticidade="alta", area="relatorio", referencias=("RF-016", "RF-017"))
def test_relatorio_mensal_rejeita_mes_invalido(api_client, analista_auth_headers):
    response = api_client.get(
        "/reports/monthly",
        params={"ano": current_report_params()["ano"], "mes": 13},
        headers=analista_auth_headers,
    )

    assert_validation_error(response)
