from __future__ import annotations

import io
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
PILLOW_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
PDF_MAGIC_BYTES = b"%PDF-"


def validate_document_upload(upload: UploadFile) -> str:
    content_type = (upload.content_type or "").lower()
    extension = ALLOWED_DOCUMENT_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo deve ser PDF, JPEG, PNG ou WEBP.",
        )
    return extension


def _verify_document_bytes(content: bytes, claimed_content_type: str) -> None:
    claimed = claimed_content_type.lower()

    if claimed == "application/pdf":
        if not content.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Arquivo enviado nao e um PDF valido.",
            )
        return

    try:
        img = Image.open(io.BytesIO(content))
        img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo enviado nao e uma imagem valida.",
        )

    detected_mime = PILLOW_FORMAT_TO_MIME.get(img.format or "")
    if detected_mime is None or detected_mime != claimed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tipo real do arquivo nao corresponde ao tipo declarado.",
        )


def save_document(upload: UploadFile, storage_root: str, subdir: str, prefix: str) -> tuple[str, int, str]:
    """Valida e salva um documento (CNH, apolice de seguro, etc.) em disco.

    Retorna (arquivo_path, tamanho_bytes, mime_type).
    """
    extension = validate_document_upload(upload)
    content = upload.file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo enviado esta vazio.",
        )
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo excede o tamanho maximo permitido (10 MB).",
        )

    _verify_document_bytes(content, upload.content_type or "")

    destination_dir = Path(storage_root) / "documentos" / subdir
    destination_dir.mkdir(parents=True, exist_ok=True)
    path = destination_dir / f"{prefix}-{uuid4().hex}{extension}"
    path.write_bytes(content)
    return str(path), len(content), upload.content_type or "application/octet-stream"


def delete_document_if_exists(arquivo_path: str | None) -> None:
    if not arquivo_path:
        return
    path = Path(arquivo_path)
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def cnh_subdir(usuario_id: UUID) -> str:
    return f"cnh/{usuario_id}"


def apolice_subdir(veiculo_id: UUID) -> str:
    return f"apolices/{veiculo_id}"


def crlv_subdir(veiculo_id: UUID) -> str:
    return f"crlv/{veiculo_id}"
