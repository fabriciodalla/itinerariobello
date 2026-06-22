from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from fpdf import FPDF
from PIL import Image

if TYPE_CHECKING:
    from app.models.foto_hodometro import FotoHodometro
    from app.models.localizacao_gps import LocalizacaoGPS
    from app.models.viagem import Viagem

log = logging.getLogger(__name__)

BRAND_COLOR = (30, 82, 107)
TABLE_HEADER_BG = (86, 130, 153)
WHITE = (255, 255, 255)
ROW_ALT_BG = (240, 245, 248)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

COL_WIDTHS = [25, 19, 10, 30, 30, 42, 18, 18, 18, 33, 33]
COL_HEADERS = [
    "Veiculo", "Data", "Nr", "Local Saida",
    "Local Chegada", "Atividade Realizada", "KM Saida", "KM Chegada", "KM Total",
    "GPS Saida", "GPS Chegada",
]
COL_ALIGNS = ["L", "C", "C", "L", "L", "L", "R", "R", "R", "C", "C"]

ROW_H = 5
FONT_SIZE = 6

PHOTO_MAX_W = 90
PHOTO_MAX_H = 70

NOISE_PARTS = {
    "brasil", "brazil", "regiao sul", "regiao sudeste", "regiao norte",
    "regiao nordeste", "regiao centro-oeste",
}
CEP_RE = re.compile(r"\d{5}-?\d{3}")


def _fmt_km(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{int(value):,}".replace(",", ".")


def _fmt_date(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.strftime("%d/%m/%Y")


def _fmt_datetime(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def _safe(text: str | None) -> str:
    if not text:
        return ""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _address_no_country(endereco: str | None) -> str:
    if not endereco:
        return ""
    parts = [p.strip() for p in endereco.split(",")]
    filtered = [p for p in parts if p.strip().lower() not in NOISE_PARTS]
    return ", ".join(filtered)


def _fmt_latlon(gps: LocalizacaoGPS | None) -> str:
    if gps is None:
        return ""
    return f"{float(gps.latitude):.6f}, {float(gps.longitude):.6f}"


def _veiculo_label(viagem: Viagem) -> str:
    placa = viagem.veiculo.placa if viagem.veiculo else None
    modelo = viagem.veiculo.modelo if viagem.veiculo else None
    if placa and modelo:
        return f"{placa} / {modelo}"
    if placa:
        return placa
    return "Nao informado"


def _resize_photo(photo_path: str) -> BytesIO | None:
    path = Path(photo_path)
    if not path.exists():
        return None
    try:
        img = Image.open(path)
        img.thumbnail((800, 800), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=75)
        buf.seek(0)
        return buf
    except Exception:
        log.warning("Falha ao processar foto %s", photo_path, exc_info=True)
        return None


def generate_itinerary_pdf(
    colaborador_nome: str,
    ano: int,
    mes: int,
    viagens: list[Viagem],
    photos_map: dict[str, dict[str, FotoHodometro]],
    gps_map: dict[str, dict[str, LocalizacaoGPS]],
) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    _draw_header(pdf, colaborador_nome, ano, mes)
    _draw_table(pdf, viagens, gps_map)

    km_total = sum((v.km_rodado or Decimal("0") for v in viagens), Decimal("0"))
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BRAND_COLOR)
    pdf.cell(0, 8, _safe(f"KM rodado total no periodo: {_fmt_km(km_total)}"))

    _draw_photos_section(pdf, viagens, photos_map)

    return bytes(pdf.output())


def _draw_header(pdf: FPDF, colaborador_nome: str, ano: int, mes: int) -> None:
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*BRAND_COLOR)
    pdf.cell(50, 18, _safe("Bello"), new_x="RIGHT", new_y="TOP")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, _safe("ALIMENTOS"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    x_start = 60

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*BRAND_COLOR)
    pdf.set_x(x_start)
    pdf.cell(0, 12, _safe("CONTROLE DE ITINERARIO"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*BLACK)
    pdf.set_x(x_start)
    pdf.cell(0, 6, _safe(f"Colaborador: {colaborador_nome}"), new_x="LMARGIN", new_y="NEXT")

    now = datetime.now(timezone.utc)
    pdf.set_x(x_start)
    pdf.cell(
        0, 6,
        _safe(f"Periodo: {mes:02d}/{ano} | Emitido em: {_fmt_datetime(now)}"),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)


def _draw_table_header(pdf: FPDF) -> None:
    pdf.set_font("Helvetica", "B", FONT_SIZE)
    pdf.set_fill_color(*TABLE_HEADER_BG)
    pdf.set_text_color(*WHITE)
    for i, header in enumerate(COL_HEADERS):
        pdf.cell(COL_WIDTHS[i], ROW_H + 1, _safe(header), border=1, fill=True, align="C")
    pdf.ln(ROW_H + 1)


def _draw_table(
    pdf: FPDF,
    viagens: list[Viagem],
    gps_map: dict[str, dict[str, LocalizacaoGPS]],
) -> None:
    _draw_table_header(pdf)

    pdf.set_font("Helvetica", "", FONT_SIZE)
    pdf.set_text_color(*BLACK)

    for idx, viagem in enumerate(viagens):
        gps = gps_map.get(str(viagem.id), {})
        gps_partida = gps.get("partida")
        gps_chegada = gps.get("chegada")

        endereco_saida = gps_partida.endereco if gps_partida else None
        endereco_chegada = gps_chegada.endereco if gps_chegada else None

        values = [
            _veiculo_label(viagem),
            _fmt_date(viagem.partida_em),
            str(idx + 1),
            _address_no_country(endereco_saida),
            _address_no_country(endereco_chegada),
            viagem.rota_utilizada or "",
            _fmt_km(viagem.km_inicial),
            _fmt_km(viagem.km_final),
            _fmt_km(viagem.km_rodado),
            _fmt_latlon(gps_partida),
            _fmt_latlon(gps_chegada),
        ]

        fill = idx % 2 == 1

        max_lines = 1
        for i, val in enumerate(values):
            lines = pdf.multi_cell(COL_WIDTHS[i], ROW_H, _safe(val), split_only=True)
            max_lines = max(max_lines, len(lines))
        cell_h = ROW_H * max_lines

        if pdf.get_y() + cell_h > pdf.h - 15:
            pdf.add_page()
            _draw_table_header(pdf)
            pdf.set_font("Helvetica", "", FONT_SIZE)
            pdf.set_text_color(*BLACK)

        x0 = pdf.get_x()
        y0 = pdf.get_y()

        for i, val in enumerate(values):
            x_cell = x0 + sum(COL_WIDTHS[:i])
            pdf.set_xy(x_cell, y0)
            if fill:
                pdf.set_fill_color(*ROW_ALT_BG)
            pdf.cell(COL_WIDTHS[i], cell_h, "", border=1, fill=fill)
            pdf.set_xy(x_cell + 0.5, y0 + 0.5)
            pdf.multi_cell(COL_WIDTHS[i] - 1, ROW_H, _safe(val), align=COL_ALIGNS[i])

        pdf.set_xy(x0, y0 + cell_h)


def _draw_photos_section(
    pdf: FPDF,
    viagens: list[Viagem],
    photos_map: dict[str, dict[str, FotoHodometro]],
) -> None:
    has_any_photo = any(photos_map.get(str(v.id)) for v in viagens)
    if not has_any_photo:
        return

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*BRAND_COLOR)
    pdf.cell(0, 12, _safe("Fotos do Hodometro"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for idx, viagem in enumerate(viagens):
        photos = photos_map.get(str(viagem.id), {})
        foto_inicial: FotoHodometro | None = photos.get("inicial")
        foto_final: FotoHodometro | None = photos.get("final")

        if not foto_inicial and not foto_final:
            continue

        needed_h = 100
        if pdf.get_y() + needed_h > pdf.h - 15:
            pdf.add_page()

        veiculo = _veiculo_label(viagem)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*BLACK)
        pdf.cell(
            0, 7,
            _safe(f"{_fmt_date(viagem.partida_em)} | Itinerario {idx + 1} | {veiculo}"),
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GRAY)
        pdf.cell(
            0, 5,
            _safe(f"KM saida: {_fmt_km(viagem.km_inicial)} | KM chegada: {_fmt_km(viagem.km_final)}"),
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(2)

        y_photos = pdf.get_y()
        col_w = 130

        _embed_photo(pdf, foto_inicial, "Foto saida", pdf.l_margin, y_photos, col_w)
        _embed_photo(pdf, foto_final, "Foto chegada", pdf.l_margin + col_w, y_photos, col_w)

        pdf.set_y(y_photos + PHOTO_MAX_H + 12)
        pdf.ln(4)


def _embed_photo(
    pdf: FPDF,
    foto: FotoHodometro | None,
    label: str,
    x: float,
    y: float,
    col_w: float,
) -> None:
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GRAY)

    if foto is None:
        pdf.cell(col_w, 6, _safe(f"{label} | Sem foto"), align="C")
        return

    pdf.cell(col_w, 6, _safe(f"{label} | {_fmt_datetime(foto.criado_em)}"), align="C")

    buf = _resize_photo(foto.arquivo_path)
    if buf is None:
        pdf.set_xy(x, y + 8)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(col_w, 6, _safe("Foto nao disponivel"), align="C")
        return

    img = Image.open(buf)
    w, h = img.size
    ratio = min(PHOTO_MAX_W / w, PHOTO_MAX_H / h, 1.0)
    img_w = w * ratio
    img_h = h * ratio
    img_x = x + (col_w - img_w) / 2

    buf.seek(0)
    pdf.image(buf, x=img_x, y=y + 8, w=img_w, h=img_h)
