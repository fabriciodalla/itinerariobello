from __future__ import annotations

import io
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
PILLOW_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
MAX_PHOTO_BYTES = 5 * 1024 * 1024


def validate_image_upload(upload: UploadFile) -> str:
    content_type = (upload.content_type or "").lower()
    extension = ALLOWED_IMAGE_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Foto do hodometro deve ser imagem JPEG, PNG ou WEBP.",
        )
    return extension


def _verify_image_bytes(content: bytes, claimed_content_type: str) -> None:
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo enviado nao e uma imagem valida.",
        )

    detected_mime = PILLOW_FORMAT_TO_MIME.get(img.format or "")
    if detected_mime is None or detected_mime != claimed_content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tipo real do arquivo nao corresponde ao tipo declarado.",
        )


def save_trip_photo(upload: UploadFile, photos_dir: str, viagem_id: UUID, tipo: str) -> tuple[str, int, str]:
    extension = validate_image_upload(upload)
    content = upload.file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Foto do hodometro esta vazia.",
        )
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Foto do hodometro excede o tamanho maximo permitido.",
        )

    _verify_image_bytes(content, upload.content_type or "")

    destination_dir = Path(photos_dir) / str(viagem_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    path = destination_dir / f"{tipo}-{uuid4().hex}{extension}"
    path.write_bytes(content)
    return str(path), len(content), upload.content_type or "application/octet-stream"
