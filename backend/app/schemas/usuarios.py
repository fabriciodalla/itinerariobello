from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import PerfilUsuario


class UsuarioCreateRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=100)
    perfil: PerfilUsuario
    cargo: str | None = Field(default=None, max_length=150)
    superior_id: UUID | None = None
    pode_aprovar: bool = False
    ativo: bool = True


class UsuarioPatchRequest(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    cargo: str | None = Field(default=None, max_length=150)
    perfil: PerfilUsuario | None = None
    superior_id: UUID | None = None
    pode_aprovar: bool | None = None
    ativo: bool | None = None


class ResetSenhaAdminRequest(BaseModel):
    nova_senha: str = Field(min_length=8, max_length=100)


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    email: str
    perfil: PerfilUsuario
    cargo: str | None = None
    superior_id: UUID | None = None
    pode_aprovar: bool
    ativo: bool
