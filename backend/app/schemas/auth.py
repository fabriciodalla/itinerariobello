from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PerfilUsuario


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    senha: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioAutenticadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    email: str
    perfil: PerfilUsuario
    cargo: str | None = None
    superior_id: UUID | None = None
    pode_aprovar: bool
    ativo: bool


class ChangePasswordRequest(BaseModel):
    senha_atual: str = Field(min_length=1)
    nova_senha: str = Field(min_length=8, max_length=100)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=1)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    nova_senha: str = Field(min_length=8, max_length=100)
