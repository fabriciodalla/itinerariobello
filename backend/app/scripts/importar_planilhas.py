from __future__ import annotations

import argparse
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.services.veiculos import normalizar_modelo_veiculo

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


@dataclass(frozen=True)
class ImportSummary:
    usuarios_lidos: int = 0
    usuarios_criados: int = 0
    usuarios_atualizados: int = 0
    superiores_nao_encontrados: int = 0
    veiculos_lidos: int = 0
    veiculos_criados: int = 0
    veiculos_atualizados: int = 0
    veiculos_sem_usuario: int = 0


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", (value or "").strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def normalize_header(value: str) -> str:
    return normalize_text(value).replace(" ", "_").replace("/", "_")


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def column_index(cell_reference: str) -> int:
    letters = "".join(ch for ch in cell_reference if ch.isalpha())
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter.upper()) - ord("A") + 1)
    return index - 1


def read_first_sheet(path: Path) -> list[dict[str, str]]:
    with ZipFile(path) as xlsx:
        workbook = ET.fromstring(xlsx.read("xl/workbook.xml"))
        rels = ET.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
        rel_by_id = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in xlsx.namelist():
            shared_root = ET.fromstring(xlsx.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("main:si", NS):
                shared_strings.append("".join(node.text or "" for node in item.findall(".//main:t", NS)))

        sheet = workbook.find("main:sheets/main:sheet", NS)
        if sheet is None:
            return []

        relationship_id = sheet.attrib[REL_NS + "id"]
        target = rel_by_id[relationship_id]
        if target.startswith("/xl/"):
            sheet_path = target.lstrip("/")
        elif target.startswith("xl/"):
            sheet_path = target
        else:
            sheet_path = "xl/" + target.lstrip("/")
        root = ET.fromstring(xlsx.read(sheet_path))

        matrix: list[list[str]] = []

        def cell_value(cell: ET.Element) -> str:
            value = cell.find("main:v", NS)
            if value is None:
                inline = cell.find("main:is/main:t", NS)
                return (inline.text or "").strip() if inline is not None else ""
            raw = value.text or ""
            if cell.attrib.get("t") == "s":
                return shared_strings[int(raw)].strip() if raw else ""
            return raw.strip()

        for row in root.findall("main:sheetData/main:row", NS):
            values: dict[int, str] = {}
            for cell in row.findall("main:c", NS):
                values[column_index(cell.attrib.get("r", "A1"))] = cell_value(cell)
            if values:
                matrix.append([values.get(index, "") for index in range(max(values) + 1)])

        if not matrix:
            return []

        headers = [normalize_header(header) for header in matrix[0]]
        rows = []
        for raw_row in matrix[1:]:
            if not any(value.strip() for value in raw_row):
                continue
            rows.append({headers[index]: value.strip() for index, value in enumerate(raw_row) if index < len(headers)})
        return rows


def require_columns(rows: list[dict[str, str]], required: set[str], source: str) -> None:
    columns = set(rows[0]) if rows else set()
    missing = required - columns
    if missing:
        raise ValueError(f"{source} nao possui colunas obrigatorias: {', '.join(sorted(missing))}")


def perfil_por_cargo(cargo: str) -> PerfilUsuario:
    return PerfilUsuario.motorista


def cargo_permite_aprovacao(cargo: str) -> bool:
    normalized = normalize_text(cargo)
    cargos_aprovadores = (
        "coordenador",
        "gerente",
        "diretor",
        "diretoria",
        "superintendente",
        "head",
    )
    return any(cargo_aprovador in normalized for cargo_aprovador in cargos_aprovadores)


def status_para_tipo_e_disponibilidade(status: str) -> tuple[TipoVeiculo, TipoDisponibilidadeVeiculo]:
    normalized = normalize_text(status)
    if normalized == "empresa":
        return TipoVeiculo.empresa, TipoDisponibilidadeVeiculo.alocado
    if normalized == "proprio":
        return TipoVeiculo.proprio, TipoDisponibilidadeVeiculo.fixo
    raise ValueError(f"status de veiculo invalido: {status}")


def find_usuario_by_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == normalize_email(email)))


def find_usuario_by_nome(db: Session, nome: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.nome == nome.strip()))


def upsert_usuarios(db: Session, rows: list[dict[str, str]], senha_padrao: str) -> tuple[int, int]:
    created = 0
    updated = 0
    for row in rows:
        email = normalize_email(row.get("usuario", ""))
        nome = row.get("nome_completo", "").strip()
        cargo = row.get("cargo", "").strip() or None
        if not email or not nome:
            continue

        usuario = find_usuario_by_email(db, email)
        if usuario is None:
            usuario = Usuario(
                email=email,
                nome=nome,
                cargo=cargo,
                senha_hash=hash_password(senha_padrao),
                perfil=perfil_por_cargo(cargo or ""),
                pode_aprovar=cargo_permite_aprovacao(cargo or ""),
                ativo=True,
            )
            db.add(usuario)
            created += 1
        else:
            usuario.nome = nome
            usuario.cargo = cargo
            usuario.perfil = perfil_por_cargo(cargo or "")
            usuario.pode_aprovar = cargo_permite_aprovacao(cargo or "")
            usuario.ativo = True
            updated += 1
    db.flush()
    return created, updated


def update_superiores(db: Session, rows: list[dict[str, str]]) -> int:
    not_found = 0
    for row in rows:
        usuario = find_usuario_by_email(db, row.get("usuario", ""))
        superior_text = row.get("superior", "").strip()
        if usuario is None or not superior_text:
            continue

        superior = find_usuario_by_email(db, superior_text)
        if superior is None:
            superior = find_usuario_by_nome(db, superior_text)

        if superior is None:
            not_found += 1
            continue

        usuario.superior_id = superior.id
    db.flush()
    return not_found


def upsert_veiculos(db: Session, rows: list[dict[str, str]]) -> tuple[int, int, int]:
    created = 0
    updated = 0
    without_user = 0
    for row in rows:
        placa = row.get("placa_veiculo", "").strip().upper()
        modelo = normalizar_modelo_veiculo(row.get("modelo___marca", ""))
        unidade = row.get("unidade", "").strip() or None
        categoria = row.get("categoria", "").strip() or None
        email = normalize_email(row.get("usuario", ""))
        tipo, disponibilidade = status_para_tipo_e_disponibilidade(row.get("status", ""))
        responsavel = find_usuario_by_email(db, email) if email else None

        if not placa or not modelo:
            continue
        if responsavel is None:
            without_user += 1
            if disponibilidade == TipoDisponibilidadeVeiculo.fixo:
                continue

        veiculo = db.scalar(select(Veiculo).where(Veiculo.placa == placa))
        if veiculo is None:
            veiculo = Veiculo(
                placa=placa,
                modelo=modelo,
                unidade=unidade,
                categoria=categoria,
                tipo=tipo,
                tipo_disponibilidade=disponibilidade,
                usuario_responsavel_id=responsavel.id if responsavel else None,
                ativo=True,
            )
            db.add(veiculo)
            created += 1
        else:
            veiculo.modelo = modelo
            veiculo.unidade = unidade
            veiculo.categoria = categoria
            veiculo.tipo = tipo
            veiculo.tipo_disponibilidade = disponibilidade
            veiculo.usuario_responsavel_id = responsavel.id if responsavel else None
            veiculo.ativo = True
            updated += 1
    db.flush()
    return created, updated, without_user


def import_planilhas(
    usuarios_path: Path,
    carros_path: Path,
    senha_padrao: str,
    dry_run: bool,
) -> ImportSummary:
    usuarios_rows = read_first_sheet(usuarios_path)
    carros_rows = read_first_sheet(carros_path)
    require_columns(usuarios_rows, {"usuario", "nome_completo", "cargo", "superior"}, "usuarios.xlsx")
    require_columns(carros_rows, {"placa_veiculo", "modelo___marca", "unidade", "categoria", "usuario", "status"}, "carros.xlsx")

    db = SessionLocal()
    try:
        usuarios_criados, usuarios_atualizados = upsert_usuarios(db, usuarios_rows, senha_padrao)
        superiores_nao_encontrados = update_superiores(db, usuarios_rows)
        veiculos_criados, veiculos_atualizados, veiculos_sem_usuario = upsert_veiculos(db, carros_rows)

        summary = ImportSummary(
            usuarios_lidos=len(usuarios_rows),
            usuarios_criados=usuarios_criados,
            usuarios_atualizados=usuarios_atualizados,
            superiores_nao_encontrados=superiores_nao_encontrados,
            veiculos_lidos=len(carros_rows),
            veiculos_criados=veiculos_criados,
            veiculos_atualizados=veiculos_atualizados,
            veiculos_sem_usuario=veiculos_sem_usuario,
        )

        if dry_run:
            db.rollback()
        else:
            db.commit()
        return summary
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importa usuarios e veiculos das planilhas iniciais.")
    parser.add_argument("--usuarios", required=True, type=Path)
    parser.add_argument("--carros", required=True, type=Path)
    parser.add_argument("--senha-padrao", required=True)
    parser.add_argument("--aplicar", action="store_true", help="Grava os dados no banco. Sem isso roda em dry-run.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = import_planilhas(
        usuarios_path=args.usuarios,
        carros_path=args.carros,
        senha_padrao=args.senha_padrao,
        dry_run=not args.aplicar,
    )
    modo = "aplicado" if args.aplicar else "dry-run"
    print(f"modo={modo}")
    for field, value in summary.__dict__.items():
        print(f"{field}={value}")


if __name__ == "__main__":
    main()
