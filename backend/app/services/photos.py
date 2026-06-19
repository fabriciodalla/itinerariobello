from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
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

    destination_dir = Path(photos_dir) / str(viagem_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    path = destination_dir / f"{tipo}-{uuid4().hex}{extension}"
    path.write_bytes(content)
    return str(path), len(content), upload.content_type or "application/octet-stream"
