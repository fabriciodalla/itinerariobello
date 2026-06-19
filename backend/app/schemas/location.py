from __future__ import annotations


ENDERECO_NAO_RESOLVIDO = "Endereco nao resolvido"


def endereco_foi_resolvido(endereco: str | None) -> bool:
    return bool(endereco)


def endereco_para_exibicao(endereco: str | None) -> str:
    return endereco or ENDERECO_NAO_RESOLVIDO
