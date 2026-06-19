"""
Script de seed de producao — Itinerario Bello
==============================================
Cria os usuarios iniciais e a frota de veiculos no banco de producao.

Como usar:
  docker compose -f docker-compose.prod.yml exec api python seed_producao.py

ANTES DE RODAR:
  1. Preencha as secoes USUARIOS e VEICULOS abaixo com os dados reais.
  2. Verifique os superiores — cada motorista deve ter o ID do seu supervisor em superior_id.
  3. O script e idempotente: pula registros que ja existem (por email ou placa).

Perfis disponiveis:
  admin      — acesso total, gerencia usuarios e veiculos
  supervisor — fecha relatorio mensal, ve viagens dos subordinados
  motorista  — registra viagens proprias
  analista   — acesso read-only a relatorios
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


# ==============================================================================
# CONFIGURACAO — USUARIOS
# Preencha com os dados reais antes de rodar.
# ==============================================================================

@dataclass
class UsuarioSeed:
    nome: str
    email: str
    senha: str
    perfil: PerfilUsuario
    cargo: str | None = None
    superior_email: str | None = None  # email do supervisor direto (para motoristas)
    pode_aprovar: bool = False
    id: UUID = field(default_factory=uuid4)


USUARIOS: list[UsuarioSeed] = [
    # ------------------------------------------------------------------
    # ADMIN — acesso total ao sistema
    # ------------------------------------------------------------------
    UsuarioSeed(
        nome="Administrador Bello",
        email="admin@belloalimentos.com.br",
        senha="Bello@2026admin",          # TROCAR na primeira entrada
        perfil=PerfilUsuario.admin,
        cargo="Administrador do Sistema",
    ),

    # ------------------------------------------------------------------
    # SUPERVISORES — fecham relatorio mensal e veem viagens dos subordinados
    # Adicione quantos supervisores a empresa tiver.
    # ------------------------------------------------------------------
    UsuarioSeed(
        nome="Supervisor Exemplo Um",           # TROCAR pelo nome real
        email="supervisor1@belloalimentos.com.br",  # TROCAR
        senha="Bello@2026sup1",                # TROCAR na primeira entrada
        perfil=PerfilUsuario.supervisor,
        cargo="Supervisor Comercial",
    ),
    UsuarioSeed(
        nome="Supervisor Exemplo Dois",         # TROCAR pelo nome real
        email="supervisor2@belloalimentos.com.br",  # TROCAR
        senha="Bello@2026sup2",                # TROCAR na primeira entrada
        perfil=PerfilUsuario.supervisor,
        cargo="Supervisor Comercial",
    ),

    # ------------------------------------------------------------------
    # MOTORISTAS — registram viagens
    # superior_email deve ser o email do supervisor acima.
    # ------------------------------------------------------------------
    UsuarioSeed(
        nome="Motorista Exemplo Um",            # TROCAR pelo nome real
        email="motorista1@belloalimentos.com.br",  # TROCAR
        senha="Bello@2026mot1",                # TROCAR na primeira entrada
        perfil=PerfilUsuario.motorista,
        cargo="Motorista",
        superior_email="supervisor1@belloalimentos.com.br",
    ),
    UsuarioSeed(
        nome="Motorista Exemplo Dois",          # TROCAR pelo nome real
        email="motorista2@belloalimentos.com.br",  # TROCAR
        senha="Bello@2026mot2",
        perfil=PerfilUsuario.motorista,
        cargo="Motorista",
        superior_email="supervisor1@belloalimentos.com.br",
    ),
    UsuarioSeed(
        nome="Motorista Exemplo Tres",          # TROCAR pelo nome real
        email="motorista3@belloalimentos.com.br",  # TROCAR
        senha="Bello@2026mot3",
        perfil=PerfilUsuario.motorista,
        cargo="Motorista",
        superior_email="supervisor2@belloalimentos.com.br",
    ),
    UsuarioSeed(
        nome="Motorista Exemplo Quatro",        # TROCAR pelo nome real
        email="motorista4@belloalimentos.com.br",  # TROCAR
        senha="Bello@2026mot4",
        perfil=PerfilUsuario.motorista,
        cargo="Motorista",
        superior_email="supervisor2@belloalimentos.com.br",
    ),

    # ------------------------------------------------------------------
    # ANALISTA — acesso read-only a relatorios (opcional)
    # ------------------------------------------------------------------
    # UsuarioSeed(
    #     nome="Analista Exemplo",
    #     email="analista@belloalimentos.com.br",
    #     senha="Bello@2026ana",
    #     perfil=PerfilUsuario.analista,
    #     cargo="Analista Comercial",
    # ),
]


# ==============================================================================
# CONFIGURACAO — VEICULOS
# Preencha com os dados reais da frota.
# ==============================================================================

@dataclass
class VeiculoSeed:
    placa: str
    modelo: str
    tipo: TipoVeiculo
    tipo_disponibilidade: TipoDisponibilidadeVeiculo
    unidade: str | None = None
    categoria: str | None = None
    responsavel_email: str | None = None  # email do motorista fixo (se tipo_disponibilidade='fixo')


VEICULOS: list[VeiculoSeed] = [
    # ------------------------------------------------------------------
    # Veiculos FIXOS — atribuidos a um motorista especifico
    # responsavel_email deve ser o email do motorista responsavel.
    # ------------------------------------------------------------------
    VeiculoSeed(
        placa="ABC-1234",                          # TROCAR pela placa real
        modelo="Fiat Strada 2023",                 # TROCAR pelo modelo real
        tipo=TipoVeiculo.proprio,
        tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
        unidade="Matriz",
        categoria="Pickup",
        responsavel_email="motorista1@belloalimentos.com.br",
    ),
    VeiculoSeed(
        placa="DEF-5678",                          # TROCAR
        modelo="VW Saveiro 2022",                  # TROCAR
        tipo=TipoVeiculo.proprio,
        tipo_disponibilidade=TipoDisponibilidadeVeiculo.fixo,
        unidade="Matriz",
        categoria="Pickup",
        responsavel_email="motorista2@belloalimentos.com.br",
    ),

    # ------------------------------------------------------------------
    # Veiculos ALOCADOS — qualquer motorista pode usar
    # ------------------------------------------------------------------
    VeiculoSeed(
        placa="GHI-9012",                          # TROCAR
        modelo="Chevrolet S10 2021",               # TROCAR
        tipo=TipoVeiculo.proprio,
        tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
        unidade="Filial",
        categoria="Pickup",
    ),
    VeiculoSeed(
        placa="JKL-3456",                          # TROCAR
        modelo="Fiat Toro 2023",                   # TROCAR
        tipo=TipoVeiculo.alugado,
        tipo_disponibilidade=TipoDisponibilidadeVeiculo.alocado,
        unidade="Filial",
        categoria="Pickup",
    ),
]


# ==============================================================================
# EXECUCAO — nao alterar abaixo desta linha
# ==============================================================================

def main() -> None:
    db = SessionLocal()
    erros: list[str] = []

    print("\n=== SEED DE PRODUCAO — ITINERARIO BELLO ===\n")

    # Indexar usuarios por email para resolver superior_id depois
    usuarios_criados: dict[str, Usuario] = {}

    # Primeira passagem: criar todos os usuarios sem superior_id
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

    # Segunda passagem: vincular superior_id
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

    # Criar veiculos
    print("\n--- Veiculos ---")
    for v in VEICULOS:
        existente = db.scalar(select(Veiculo).where(Veiculo.placa == v.placa))
        if existente:
            print(f"  [JA EXISTE] {v.placa} — {v.modelo}")
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
            modelo=v.modelo,
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
            print(f"  [CRIADO]    {v.placa} — {v.modelo} ({v.tipo_disponibilidade.value})")
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
