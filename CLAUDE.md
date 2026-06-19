# CLAUDE.md — Controle Itinerário Comercial Bello

Referência técnica para o Claude Code trabalhar neste repositório.
Leia antes de qualquer implementação. Para regras de comportamento da IA, consulte `AGENTS.md`.

---

## O que estamos construindo

PWA mobile-first que substitui planilhas manuais de controle de quilometragem da Bello Alimentos. Motoristas registram viagens com foto do hodômetro e GPS. Superiores fecham consolidado mensal aberto/fechado. Analistas exportam relatórios.

Perfis: **motorista** · **supervisor** (pode_aprovar) · **analista** · **admin**

---

## Stack — decisões já tomadas, não alterar sem justificativa

| Camada | Escolha | Motivo |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Tipagem nativa, validação via Pydantic, async pronto |
| Banco | PostgreSQL 16 + SQLAlchemy + Alembic | Relacional com suporte a constraints de negócio |
| Frontend | React 18 + TypeScript + Vite | PWA com Workbox; câmera via `capture="environment"` nativo |
| Infra | Docker Compose | Ambiente reproduzível; serviços: `api`, `frontend` e `db` |
| Testes | pytest + marcador `@pytest.mark.risco` | Auditoria de risco integrada à suite |
| Fotos (protótipo) | Volume local Docker | Migrar para S3/Azure Blob em produção |

---

## Estrutura de pastas a seguir

```
backend/
  app/
    api/
      deps.py           # get_current_user(), require_admin()
      routes/           # um arquivo por domínio (auth, trips, vehicles, reports...)
    core/
      config.py         # Settings via BaseSettings — lê .env
      security.py       # JWT + hashing de senha
    db/
      base.py           # Base SQLAlchemy, UuidPkMixin, TimestampMixin
      session.py        # SessionLocal, get_db()
    models/             # Um arquivo por entidade
    schemas/            # Pydantic — separar request de response
    services/           # Lógica de negócio fora dos routes
  alembic/
    versions/           # Migrações versionadas — nunca editar as já aplicadas
  Dockerfile

frontend/
  src/
    screens/            # Uma tela por arquivo
    components/         # Componentes reutilizáveis
    services/api.ts     # Todo acesso HTTP centralizado aqui
    hooks/              # Hooks customizados (GPS, câmera, etc.)
    types/domain.ts     # Interfaces TypeScript do domínio
  vite.config.ts

docs/                   # Fonte de verdade do produto — ver seção abaixo
docker-compose.yml
docker-compose.prod.example.yml
.env.example
.env.production.example
```

Não criar pastas ou camadas fora desta estrutura sem discutir com o usuário.

---

## Comandos

```bash
# Subir ambiente
docker compose up -d

# Validar modelo de produção HTTPS
docker compose --env-file .env.production -f docker-compose.prod.example.yml config

# Validar e subir modelo de VM compartilhada
docker compose --env-file .env.production -f docker-compose.vm.yml config
docker compose --env-file .env.production -f docker-compose.vm.yml up -d --build

# Aplicar migrações
docker compose exec api alembic upgrade head
docker compose --env-file .env.production -f docker-compose.vm.yml exec api alembic upgrade head

# Criar migração após alterar model
docker compose exec api alembic revision --autogenerate -m "descricao"

# Testes
pytest
pytest -m "viagem" -v        # por área
pytest -m "critica" -v       # por criticidade

# Frontend
cd frontend && npm install --legacy-peer-deps
cd frontend && npm run dev    # http://localhost:5173
cd frontend && npm run build
cd frontend && npx tsc --noEmit
```

---

## Convenções de código

**Backend**
- Nomes de domínio em português (`viagem`, `fechamento_mensal`, `motorista_id`)
- Nomes técnicos em inglês (`models`, `schemas`, `services`, `get_db`)
- Validações críticas sempre no backend — frontend valida por UX, nunca como única barreira
- Dependências via `get_current_user()` e `require_admin()` em `deps.py`
- Schemas Pydantic separados: um para request, um para response
- Nenhuma lógica de negócio nos routes — vai em `services/`

**Banco**
- Toda entidade herda `UuidPkMixin` (id UUID) e `TimestampMixin` (criado_em, atualizado_em)
- Constraints de negócio vivem no banco, não só no código (CHECK, UNIQUE, NOT NULL)
- Migrações com nomes descritivos: `20260518_0001_cria_tabela_viagens.py`
- Nunca editar migration já aplicada — sempre criar nova revisão

**Frontend**
- Todo acesso HTTP passa por `services/api.ts` — nunca `fetch` direto nos componentes
- Câmera: `<input type="file" accept="image/*" capture="environment">` — sem biblioteca
- GPS: `react-use-geolocation` — já decidido, não trocar
- Tipos do domínio ficam em `types/domain.ts` — não duplicar inline nos componentes

---

## Regras de negócio inegociáveis

Estas regras nunca podem ser flexibilizadas sem aprovação explícita do usuário:

| # | Regra | Impacto se violada |
|---|---|---|
| 1 | Foto do hodômetro obrigatória na partida e na chegada | Viagem não pode ser criada/finalizada |
| 2 | GPS obrigatório na partida e na chegada | Idem |
| 3 | `km_final >= km_inicial` | Erro de validação — constraint no banco |
| 4 | Veículo em uso no dia não pode ser reutilizado | Bloqueio na partida (409) |
| 5 | Viagem não pode ser editada após fechamento mensal fechado | 409 |
| 6 | Fechamento mensal fechado registra responsável e data/hora | Auditoria incompleta |
| 7 | Responsável vê apenas fechamentos dos próprios subordinados | 403 para acesso cruzado |
| 8 | `endereco` GPS é nullable — geocodificação pode falhar | Nunca validar como truthy |
| 9 | Toda rota exige token JWT válido | 401 sem token, 403 sem permissão |

Detalhes completos em `docs/regras-negocio.md`.

---

## Política de testes

Todo teste precisa do marcador `@pytest.mark.risco(...)`:

```python
@pytest.mark.risco(
    peso=100,               # deve bater com criticidade: critica=100, alta=50, media=20, baixa=5
    criticidade="critica",
    area="viagem",          # ver áreas válidas abaixo
    referencias=("RF-004", "RN-002"),  # identificadores reais dos docs — não inventar
)
def test_descricao_do_comportamento(...):
    ...
```

**Áreas válidas:** `infra · modelo_dados · autenticacao · permissao · viagem · foto · gps · km · aprovacao · relatorio`

A entrega é bloqueada automaticamente se houver qualquer ponto de falha ou ponto não validado no relatório de risco gerado em `backend/app/tests/reports/risco-testes.json`.

Referências nos markers (`referencias=`) usam identificadores dos documentos em `docs/` (RF-XXX, RN-XXX, RNF-XXX). Nunca usar referências inventadas.

---

## Variáveis de ambiente

Definir em `.env` (copiar de `.env.example`):

| Variável | Descrição | Obrigatório em produção |
|---|---|---|
| `DATABASE_URL` | URL SQLAlchemy | sim |
| `SECRET_KEY` | Assinar JWT — sem isso, tokens invalidam ao reiniciar | sim |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Padrão: `10080` (7 dias) | não |
| `PHOTOS_DIR` | Diretório de fotos | sim |
| `CORS_ORIGINS` | Origins permitidas, separadas por vírgula | sim |
| `APP_ENV` | `local` / `production` | não |
| `REVERSE_GEOCODING_ENABLED` | `false` por padrão | não |

Para testes, definir também:
`TEST_MOTORISTA_EMAIL` · `TEST_MOTORISTA_PASSWORD` · `TEST_APROVADOR_EMAIL` · `TEST_APROVADOR_PASSWORD` · `TEST_ANALISTA_EMAIL` · `TEST_ANALISTA_PASSWORD` · `TEST_VEICULO_ID`

---

## Documentação — fonte de verdade

Antes de implementar qualquer coisa, consultar o documento correspondente em `docs/`:

| Documento | Consultar quando |
|---|---|
| `requisitos.md` | Definir funcionalidade, perfil ou critério de aceite |
| `regras-negocio.md` | Implementar validação, status ou fluxo de fechamento |
| `modelo-dados.md` | Criar ou alterar entidade, campo ou relacionamento |
| `api.md` | Definir endpoint, payload ou contrato de resposta |
| `telas-fluxos.md` | Implementar tela, navegação ou experiência mobile |
| `arquitetura.md` | Tomar decisão de infraestrutura ou organização técnica |
| `testes.md` | Definir escopo, marcadores ou critério de validação |

Quando a implementação alterar comportamento coberto por algum desses documentos, atualizar o documento na mesma entrega.
