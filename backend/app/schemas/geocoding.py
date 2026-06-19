from __future__ import annotations

from pydantic import BaseModel, Field, computed_field, field_validator

from app.schemas.location import endereco_foi_resolvido, endereco_para_exibicao


class ReverseGeocodeResponse(BaseModel):
    endereco: str | None = Field(default=None, max_length=500)

    @field_validator("endereco")
    @classmethod
    def limpar_endereco(cls, value: str | None) -> str | None:
        if value is None:
            return None
        endereco = value.strip()
        return endereco or None

    @computed_field
    @property
    def endereco_resolvido(self) -> bool:
        return endereco_foi_resolvido(self.endereco)

    @computed_field
    @property
    def endereco_exibicao(self) -> str:
        return endereco_para_exibicao(self.endereco)
