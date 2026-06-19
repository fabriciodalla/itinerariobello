from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parents[1]
DEFAULT_RISK_REPORT_PATH = TESTS_DIR / "reports" / "risco-testes.json"
RISK_WEIGHTS = {
    "critica": 100,
    "alta": 50,
    "media": 20,
    "baixa": 5,
}
RISK_AREAS = {
    "infra",
    "modelo_dados",
    "autenticacao",
    "permissao",
    "viagem",
    "foto",
    "gps",
    "km",
    "aprovacao",
    "relatorio",
}
_RISK_OUTCOMES: dict[str, str] = {}

for path in (TESTS_DIR, BACKEND_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


def pytest_addoption(parser):
    parser.addoption(
        "--risk-report",
        action="store",
        default=os.getenv("TEST_RISK_REPORT_PATH", str(DEFAULT_RISK_REPORT_PATH)),
        help="Caminho do relatorio JSON de auditoria de risco dos testes.",
    )


def _risk_metadata(item) -> dict[str, Any]:
    marker = item.get_closest_marker("risco")
    if marker is None:
        raise pytest.UsageError(
            f"{item.nodeid} nao possui @pytest.mark.risco(...). "
            "Todo teste precisa de peso, criticidade, area e referencias."
        )

    if marker.args:
        raise pytest.UsageError(
            f"{item.nodeid} usa @pytest.mark.risco com argumentos posicionais. "
            "Use apenas argumentos nomeados."
        )

    metadata = dict(marker.kwargs)
    peso = metadata.get("peso")
    criticidade = metadata.get("criticidade")
    area = metadata.get("area")
    referencias = metadata.get("referencias")

    if criticidade not in RISK_WEIGHTS:
        raise pytest.UsageError(
            f"{item.nodeid} possui criticidade invalida: {criticidade}. "
            f"Use uma destas: {', '.join(RISK_WEIGHTS)}."
        )

    expected_weight = RISK_WEIGHTS[criticidade]
    if peso != expected_weight:
        raise pytest.UsageError(
            f"{item.nodeid} possui peso {peso}, mas criticidade {criticidade} "
            f"exige peso {expected_weight}."
        )

    if area not in RISK_AREAS:
        raise pytest.UsageError(
            f"{item.nodeid} possui area invalida: {area}. "
            f"Use uma destas: {', '.join(sorted(RISK_AREAS))}."
        )

    if not isinstance(referencias, (tuple, list)) or not referencias:
        raise pytest.UsageError(
            f"{item.nodeid} deve informar referencias como tupla/lista, "
            "por exemplo referencias=('RF-001', 'RN-001')."
        )

    return {
        "nodeid": item.nodeid,
        "peso": peso,
        "criticidade": criticidade,
        "area": area,
        "referencias": list(referencias),
    }


def pytest_collection_modifyitems(config, items):
    config._risk_audit_items = [_risk_metadata(item) for item in items]


def pytest_runtest_logreport(report):
    if report.when not in {"setup", "call", "teardown"}:
        return

    current_status = _RISK_OUTCOMES.get(report.nodeid)
    if report.failed:
        _RISK_OUTCOMES[report.nodeid] = "falhou"
    elif report.skipped and current_status != "falhou":
        _RISK_OUTCOMES[report.nodeid] = "nao_validado"
    elif report.when == "call" and report.passed and current_status is None:
        _RISK_OUTCOMES[report.nodeid] = "passou"


def _build_risk_summary(config) -> dict[str, Any]:
    items = getattr(config, "_risk_audit_items", [])

    by_nodeid = {}
    for item in items:
        status = _RISK_OUTCOMES.get(item["nodeid"], "nao_executado")
        by_nodeid[item["nodeid"]] = {**item, "status": status}

    total_points = sum(item["peso"] for item in by_nodeid.values())
    failed_points = sum(item["peso"] for item in by_nodeid.values() if item["status"] == "falhou")
    not_validated_points = sum(
        item["peso"] for item in by_nodeid.values() if item["status"] in {"nao_validado", "nao_executado"}
    )
    passed_points = sum(item["peso"] for item in by_nodeid.values() if item["status"] == "passou")

    by_criticality: dict[str, dict[str, int]] = {}
    for level in RISK_WEIGHTS:
        level_items = [item for item in by_nodeid.values() if item["criticidade"] == level]
        by_criticality[level] = {
            "testes": len(level_items),
            "pontos_total": sum(item["peso"] for item in level_items),
            "pontos_falha": sum(item["peso"] for item in level_items if item["status"] == "falhou"),
            "pontos_nao_validados": sum(
                item["peso"] for item in level_items if item["status"] in {"nao_validado", "nao_executado"}
            ),
        }

    compliance = 100.0
    if total_points:
        compliance = round((passed_points / total_points) * 100, 2)

    return {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "total_testes": len(by_nodeid),
        "pontos_risco_total": total_points,
        "pontos_falha": failed_points,
        "pontos_nao_validados": not_validated_points,
        "indice_conformidade_percentual": compliance,
        "bloqueia_entrega": failed_points > 0 or not_validated_points > 0 or compliance < 100.0,
        "por_criticidade": by_criticality,
        "testes": list(by_nodeid.values()),
    }


def pytest_sessionfinish(session, exitstatus):
    if session.config.option.collectonly:
        return

    summary = _build_risk_summary(session.config)
    session.config._risk_summary = summary
    if summary["total_testes"] and summary["bloqueia_entrega"] and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    summary = getattr(config, "_risk_summary", None) or _build_risk_summary(config)
    if not summary["total_testes"]:
        return

    terminalreporter.section("auditoria de risco dos testes")
    terminalreporter.write_line(f"Pontos totais de risco: {summary['pontos_risco_total']}")
    terminalreporter.write_line(f"Pontos com falha: {summary['pontos_falha']}")
    terminalreporter.write_line(f"Pontos nao validados: {summary['pontos_nao_validados']}")
    terminalreporter.write_line(
        f"Indice de conformidade: {summary['indice_conformidade_percentual']}%"
    )
    terminalreporter.write_line(
        f"Bloqueia entrega: {'sim' if summary['bloqueia_entrega'] else 'nao'}"
    )

    report_path = Path(config.getoption("--risk-report"))
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        terminalreporter.write_line(f"Relatorio JSON: {report_path}")
    except OSError as exc:
        terminalreporter.write_line(f"Nao foi possivel gravar relatorio JSON: {exc}")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.fail(
            f"Defina a variavel de ambiente {name} para executar estes testes. "
            "Use sempre uma base de teste descartavel.",
            pytrace=False,
        )
    return value


def _load_asgi_app() -> Any:
    import_path = os.getenv("APP_IMPORT_PATH", "app.main:app")
    if ":" not in import_path:
        pytest.fail(
            "APP_IMPORT_PATH deve seguir o formato modulo:atributo, "
            "por exemplo app.main:app.",
            pytrace=False,
        )

    module_name, attr_name = import_path.split(":", 1)

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        pytest.fail(
            f"Nao foi possivel importar {module_name}. "
            "Crie o backend FastAPI ou defina API_BASE_URL para testar uma API em execucao. "
            f"Erro original: {exc}",
            pytrace=False,
        )

    try:
        return getattr(module, attr_name)
    except AttributeError:
        pytest.fail(
            f"O modulo {module_name} nao possui o atributo {attr_name}.",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def api_client():
    base_url = os.getenv("API_BASE_URL")

    if base_url:
        try:
            import httpx
        except ModuleNotFoundError:
            pytest.fail(
                "Instale httpx ou execute os testes importando a app FastAPI via APP_IMPORT_PATH.",
                pytrace=False,
            )

        with httpx.Client(base_url=base_url.rstrip("/"), timeout=30.0) as client:
            yield client
        return

    try:
        from fastapi.testclient import TestClient
    except ModuleNotFoundError:
        pytest.fail(
            "FastAPI nao esta instalado. Instale as dependencias do backend "
            "ou defina API_BASE_URL para testar uma API em execucao.",
            pytrace=False,
        )

    app = _load_asgi_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def limpar_registros_transacionais_de_teste():
    if os.getenv("TEST_DB_CLEANUP_DISABLED") == "1":
        yield
        return

    from sqlalchemy import delete

    from app.db.session import SessionLocal
    from app.models.aprovacao import Aprovacao
    from app.models.fechamento_mensal import FechamentoMensal
    from app.models.foto_hodometro import FotoHodometro
    from app.models.localizacao_gps import LocalizacaoGPS
    from app.models.viagem import Viagem

    def cleanup() -> None:
        db = SessionLocal()
        try:
            db.execute(delete(FechamentoMensal))
            db.execute(delete(Aprovacao))
            db.execute(delete(LocalizacaoGPS))
            db.execute(delete(FotoHodometro))
            db.execute(delete(Viagem))
            db.commit()
        finally:
            db.close()

    cleanup()
    yield
    cleanup()


def _login(api_client, email: str, senha: str) -> dict[str, str]:
    response = api_client.post("/auth/login", json={"email": email, "senha": senha})
    if response.status_code != 200:
        pytest.fail(
            "Login de teste falhou. Verifique usuarios seedados e credenciais. "
            f"Status: {response.status_code}. Corpo: {response.text}",
            pytrace=False,
        )

    data = response.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        pytest.fail(
            "Resposta de /auth/login deve retornar access_token ou token.",
            pytrace=False,
        )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def motorista_auth_headers(api_client) -> dict[str, str]:
    return _login(
        api_client,
        _required_env("TEST_MOTORISTA_EMAIL"),
        _required_env("TEST_MOTORISTA_PASSWORD"),
    )


@pytest.fixture
def fresh_motorista_auth_headers(api_client) -> dict[str, str]:
    return _login(
        api_client,
        _required_env("TEST_MOTORISTA_EMAIL"),
        _required_env("TEST_MOTORISTA_PASSWORD"),
    )


@pytest.fixture(scope="session")
def aprovador_auth_headers(api_client) -> dict[str, str]:
    return _login(
        api_client,
        _required_env("TEST_APROVADOR_EMAIL"),
        _required_env("TEST_APROVADOR_PASSWORD"),
    )


@pytest.fixture(scope="session")
def analista_auth_headers(api_client) -> dict[str, str]:
    return _login(
        api_client,
        _required_env("TEST_ANALISTA_EMAIL"),
        _required_env("TEST_ANALISTA_PASSWORD"),
    )


@pytest.fixture(scope="session")
def test_vehicle_id() -> str:
    return _required_env("TEST_VEICULO_ID")
