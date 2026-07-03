"""
Script de seed de producao — Itinerario Bello
==============================================
Cria o usuario administrador inicial no banco de producao.
Demais usuarios sao criados pela interface (solicitacao de cadastro)
ou adicionados aqui conforme necessidade.

Como usar:
  docker compose --env-file .env.production -f docker-compose.vm.yml exec api python seed_producao.py

O script e idempotente: pula registros que ja existem (por email ou placa).
"""

import sys
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import PerfilUsuario, TipoDisponibilidadeVeiculo, TipoVeiculo
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.services.veiculos import normalizar_modelo_veiculo


@dataclass
class UsuarioSeed:
    nome: str
    email: str
    senha: str
    perfil: PerfilUsuario
    cargo: str | None = None
    superior_email: str | None = None
    pode_aprovar: bool = False
    id: UUID = field(default_factory=uuid4)


@dataclass
class VeiculoSeed:
    placa: str
    modelo: str
    tipo: TipoVeiculo
    tipo_disponibilidade: TipoDisponibilidadeVeiculo
    unidade: str | None = None
    categoria: str | None = None
    responsavel_email: str | None = None


# ==============================================================================
# USUARIOS — preencha com os dados reais antes de rodar
# ==============================================================================

USUARIOS: list[UsuarioSeed] = [
    UsuarioSeed(
        nome="Administrador Bello",
        email="admin@belloalimentos.com.br",      # TROCAR pelo email real
        senha="Bello@2026admin",                   # TROCAR na primeira entrada
        perfil=PerfilUsuario.admin,
        cargo="Administrador do Sistema",
    ),
    # Adicione supervisores, motoristas e analistas abaixo conforme necessidade.
    # Exemplo:
    # UsuarioSeed(
    #     nome="Nome do Supervisor",
    #     email="supervisor@belloalimentos.com.br",
    #     senha="SenhaTempor@ria1",
    #     perfil=PerfilUsuario.supervisor,
    #     cargo="Supervisor Comercial",
    # ),
    # UsuarioSeed(
    #     nome="Nome do Motorista",
    #     email="motorista@belloalimentos.com.br",
    #     senha="SenhaTempor@ria2",
    #     perfil=PerfilUsuario.motorista,
    #     cargo="Motorista",
    #     superior_email="supervisor@belloalimentos.com.br",
    # ),
]


# ==============================================================================
# VEICULOS — preencha com os dados reais da frota
# ==============================================================================

VEICULOS: list[VeiculoSeed] = [
    # Exemplo:
    # VeiculoSeed(
    #     placa="ABC-1D23",
    #     modelo="STRADA 2023",
    #     tipo=TipoVeiculo.proprio,
    #     tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
    #     unidade="Matriz",
    #     categoria="Pickup",
    # ),
]


# ==============================================================================
# EXECUCAO — nao alterar abaixo desta linha
# ==============================================================================

def main() -> None:
    db = SessionLocal()
    erros: list[str] = []

    print("\n=== SEED DE PRODUCAO — ITINERARIO BELLO ===\n")

    usuarios_criados: dict[str, Usuario] = {}

    print("--- Usuarios ---")
    for u in USUARIOS:
        existente = db.scalar(select(Usuario).where(Usuario.email == u.email))
        if existente:
            print(f"  [JA EXISTE] {u.nome} <{u.email}>")
            usuarios_criados[u.email] = existente
            continue

        pode_aprovar = u.pode_aprovar or u.perfil == PerfilUsuario.supervisor
        novo = Usuario(
            id=u.id,
            nome=u.nome,
            email=u.email,
            senha_hash=hash_password(u.senha),
            perfil=u.perfil,
            cargo=u.cargo,
            pode_aprovar=pode_aprovar,
            ativo=True,
        )
        db.add(novo)
        try:
            db.flush()
            usuarios_criados[u.email] = novo
            print(f"  [CRIADO]    {u.nome} <{u.email}> perfil={u.perfil.value}")
        except IntegrityError as exc:
            db.rollback()
            msg = f"Erro ao criar {u.email}: {exc}"
            erros.append(msg)
            print(f"  [ERRO]      {msg}")

    for u in USUARIOS:
        if u.superior_email is None:
            continue
        motorista = usuarios_criados.get(u.email)
        superior = usuarios_criados.get(u.superior_email)
        if motorista is None or superior is None:
            continue
        if motorista.superior_id != superior.id:
            motorista.superior_id = superior.id

    db.flush()

    print("\n--- Veiculos ---")
    for v in VEICULOS:
        modelo_normalizado = normalizar_modelo_veiculo(v.modelo)
        existente = db.scalar(select(Veiculo).where(Veiculo.placa == v.placa))
        if existente:
            print(f"  [JA EXISTE] {v.placa} — {existente.modelo}")
            continue

        responsavel_id: UUID | None = None
        if v.responsavel_email:
            resp = usuarios_criados.get(v.responsavel_email)
            if resp is None:
                msg = f"Responsavel '{v.responsavel_email}' nao encontrado para veiculo {v.placa}."
                erros.append(msg)
                print(f"  [ERRO]      {msg}")
                continue
            responsavel_id = resp.id

        if v.tipo_disponibilidade == TipoDisponibilidadeVeiculo.fixo and responsavel_id is None:
            msg = f"Veiculo fixo {v.placa} exige responsavel_email."
            erros.append(msg)
            print(f"  [ERRO]      {msg}")
            continue

        novo_veiculo = Veiculo(
            placa=v.placa,
            modelo=modelo_normalizado,
            tipo=v.tipo,
            tipo_disponibilidade=v.tipo_disponibilidade,
            unidade=v.unidade,
            categoria=v.categoria,
            usuario_responsavel_id=responsavel_id,
            ativo=True,
        )
        db.add(novo_veiculo)
        try:
            db.flush()
            print(f"  [CRIADO]    {v.placa} — {modelo_normalizado} ({v.tipo_disponibilidade.value})")
        except IntegrityError as exc:
            db.rollback()
            msg = f"Erro ao criar veiculo {v.placa}: {exc}"
            erros.append(msg)
            print(f"  [ERRO]      {msg}")

    if erros:
        db.rollback()
        print("\n=== SEED CONCLUIDO COM ERROS — nenhuma alteracao salva ===")
        for e in erros:
            print(f"  !! {e}")
        db.close()
        sys.exit(1)
    else:
        db.commit()
        print("\n=== SEED CONCLUIDO COM SUCESSO ===")
        print("Lembre-se: todos os usuarios devem trocar a senha no primeiro acesso.")

    db.close()


if __name__ == "__main__":
    main()
