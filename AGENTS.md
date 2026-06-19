# AGENTS.md

> Guia operacional para a IA trabalhar no projeto CONTROLE ITINERÁRIO COMERCIAL BELLO.
> Ler no início de cada conversa. Para referência técnica do código, consultar `CLAUDE.md`.

---

## 1. Papel Da IA

A IA atua como agente de programação e documentação do projeto.

Quando houver pedido claro do usuário, executar diretamente no código, documentação ou estrutura do projeto.

Quando identificar melhoria não solicitada, explicar a proposta e aguardar confirmação antes de executar.

---

## 2. Estado Atual Do Projeto

| Campo | Situação |
|---|---|
| Produto | CONTROLE ITINERÁRIO COMERCIAL BELLO |
| Plataforma | PWA mobile-first |
| Problema resolvido | Substitui planilhas manuais de controle de quilometragem |
| Estado | **Backend e frontend implementados e em funcionamento** |
| Prioridade atual | Estabilização, testes e ajustes para acesso externo |

**O que já existe:**
- Backend FastAPI com rotas: `/auth`, `/signup-requests`, `/users`, `/trips`, `/vehicles`, `/reports/monthly`, `/geocoding`, `/health`
- Frontend React + TypeScript (PWA) com telas de login, viagem, histórico e fechamento mensal
- Banco PostgreSQL com todas as tabelas, constraints e migrations aplicadas
- Suite de testes pytest com sistema de auditoria de risco (`@pytest.mark.risco`)
- Docker Compose configurado com serviços `api`, `frontend` e `db`

---

## 3. Documentação De Referência

Antes de implementar, consultar somente os documentos necessários para a tarefa:

| Tipo de tarefa | Ler antes de agir |
|---|---|
| Backend, serviço ou endpoint | `docs/regras-negocio.md`, `docs/modelo-dados.md`, `docs/api.md` |
| Model, migration ou banco | `docs/modelo-dados.md`, `docs/regras-negocio.md` |
| Tela ou fluxo mobile | `docs/telas-fluxos.md`, `docs/regras-negocio.md` |
| Autenticação ou permissões | `docs/requisitos.md`, `docs/api.md` |
| Fechamento mensal | `docs/regras-negocio.md`, `docs/modelo-dados.md`, `docs/api.md` |
| Relatório ou exportação | `docs/regras-negocio.md`, `docs/api.md` |
| Testes | `docs/testes.md` + documentos da funcionalidade testada |

Quando a implementação alterar comportamento, regra, endpoint, model ou tela, atualizar a documentação relacionada na mesma entrega.

### 3.1 Fonte Da Verdade Por Assunto

Quando houver divergência entre documentos:

| Assunto | Fonte principal | Atualizar junto |
|---|---|---|
| Requisitos, perfis e critérios | `docs/requisitos.md` | `docs/regras-negocio.md`, `docs/telas-fluxos.md` |
| Regras, status e validações | `docs/regras-negocio.md` | `docs/modelo-dados.md`, `docs/api.md` |
| Entidades e relacionamentos | `docs/modelo-dados.md` | `docs/api.md`, `docs/regras-negocio.md` |
| Endpoints e contratos | `docs/api.md` | `docs/modelo-dados.md`, `docs/telas-fluxos.md` |
| Telas e fluxos | `docs/telas-fluxos.md` | `docs/requisitos.md`, `docs/api.md` |
| Stack e infraestrutura | `docs/arquitetura.md` | `AGENTS.md`, `CLAUDE.md` |

---

## 4. Stack — Não Alterar Sem Justificativa

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Banco | PostgreSQL 16 + SQLAlchemy + Alembic |
| Validação | Pydantic |
| Frontend | React 18 + TypeScript + Vite (PWA + Workbox) |
| Câmera | `<input capture="environment">` nativo — sem biblioteca |
| GPS | `react-use-geolocation` |
| Infra | Docker Compose (`api` + `frontend` + `db`) |
| Fotos (protótipo) | Volume local — migrar para S3/Azure Blob em produção |

Novas dependências só com autorização explícita do usuário.

---

## 5. Estrutura Do Projeto

```
backend/app/
  api/
    deps.py              # get_current_user(), require_admin()
    routes/              # auth.py, signup_requests.py, users.py, trips.py, vehicles.py, geocoding.py
  core/config.py         # Settings via BaseSettings
  core/security.py       # JWT + hashing
  db/base.py             # Base SQLAlchemy, UuidPkMixin, TimestampMixin
  db/session.py          # SessionLocal, get_db()
  models/                # usuario, veiculo, viagem, foto_hodometro,
                         # localizacao_gps, fechamento_mensal, aprovacao
  schemas/               # Pydantic — request e response separados
  services/              # photos.py, veiculos.py, geocoding.py
  tests/
    conftest.py          # fixtures, sistema de auditoria de risco
    assertions.py        # helpers de asserção
    factories.py         # start_payload, finish_payload, multipart_payload
    helpers.py           # create_trip_in_progress, create_trip_ready_for_monthly_closure
    test_*.py

frontend/src/
  screens/               # LoginScreen, TripScreen, HistoryScreen, MonthlyClosureScreen
  components/            # CameraCapture, GpsBadge, StatusPill, ChangePasswordModal
  services/api.ts        # todo acesso HTTP centralizado aqui
  hooks/useGpsCapture.ts
  types/domain.ts        # interfaces TypeScript do domínio
```

---

## 6. Comandos

```bash
# Ambiente
docker compose up -d
docker compose down
docker compose logs api -f
docker compose --env-file .env.production -f docker-compose.prod.example.yml config
docker compose --env-file .env.production -f docker-compose.vm.yml config
docker compose --env-file .env.production -f docker-compose.vm.yml up -d --build

# Banco
docker compose exec api alembic upgrade head
docker compose --env-file .env.production -f docker-compose.vm.yml exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "descricao"

# Testes
pytest
pytest -m "viagem" -v
pytest -m "aprovacao" -v
pytest -m "critica" -v

# Frontend
cd frontend && npm install --legacy-peer-deps  # quando precisar reinstalar dependências
cd frontend && npm run dev       # http://localhost:5173
cd frontend && npm run build
cd frontend && npx tsc --noEmit
```

Antes de instalar dependências, baixar pacotes ou alterar infraestrutura, avisar o usuário e aguardar autorização.

---

## 7. Regras De Negócio Implementadas

Estas regras estão ativas no código. Não remover nem flexibilizar sem aprovação explícita:

| Ref | Regra | Retorno se violada |
|---|---|---|
| RN-001 | Token JWT obrigatório em toda rota | 401 |
| RN-004 | Foto do hodômetro obrigatória na partida e na chegada | 422 |
| RN-005 | GPS obrigatório na partida e na chegada | 422 |
| RN-013 | Viagem não editável após fechamento fechado | 409 |
| RN-014 | Observação do fechamento é opcional e registrada quando informada | comportamento válido |
| RN-017 | `km_final >= km_inicial` — constraint no banco | 409 |
| RN-018 | Veículo em uso no dia bloqueia nova partida | 409 |
| RN-020 | Responsável pelo fechamento vê só fechamentos dos próprios subordinados | 403 |
| RN-023 | `endereco` GPS é nullable — geocodificação pode falhar | comportamento válido |
| RNF-004 | Perfil sem permissão | 403 |

Aprovação individual por viagem e decisão aprovar/reprovar de fechamento foram desativadas — endpoints legados retornam **410**.

---

## 8. Perfis De Usuário

| Perfil | Flag no banco | Responsabilidade |
|---|---|---|
| Motorista | `perfil=motorista` | Registrar viagens próprias |
| Responsável pelo fechamento | `perfil=supervisor`, `pode_aprovar=True` | Fechar mensalmente consolidado de subordinados |
| Analista | `perfil=analista` | Consultar e exportar relatórios |
| Administrador | `perfil=admin` | Cadastrar usuários, veículos e permissões |

Hierarquia: `usuarios.superior_id` define de quem cada responsável pelo fechamento cuida.

---

## 9. Padrões De Desenvolvimento

- Código funcional, simples e fácil de manter — sem abstrações antecipadas.
- Nomes de domínio em português (`viagem`, `motorista_id`, `fechamento_mensal`).
- Nomes técnicos em inglês (`models`, `schemas`, `services`, `get_db`).
- Validações críticas sempre no backend — frontend valida por UX, nunca como única barreira.
- Nenhuma lógica de negócio nos routes — vai em `services/`.
- Sem refatorações fora do escopo da tarefa solicitada.
- Não reverter alterações existentes sem pedido explícito.
- Em PowerShell, ler arquivos Markdown com `-Encoding UTF8`.

---

## 10. Política De Testes

Todo teste requer `@pytest.mark.risco(...)` com argumentos nomeados:

```python
@pytest.mark.risco(
    peso=100,              # deve bater com criticidade
    criticidade="critica", # critica=100 | alta=50 | media=20 | baixa=5
    area="viagem",         # ver áreas válidas abaixo
    referencias=("RF-004", "RN-005"),  # identificadores reais dos docs
)
def test_nome_descritivo(...):
    ...
```

**Áreas válidas:** `infra · modelo_dados · autenticacao · permissao · viagem · foto · gps · km · aprovacao · relatorio`

**Referências** usam prefixos reais: `RF-XXX`, `RN-XXX`, `RNF-XXX`. Nunca inventar referências.

A entrega é bloqueada automaticamente se `pontos_falha > 0` ou `pontos_nao_validados > 0` no relatório `backend/app/tests/reports/risco-testes.json`.

Se não for possível executar testes, informar o comando pendente, o motivo e o risco da entrega sem validação.

### 10.1 Agentes Validadores Obrigatórios

Alterações relevantes devem ser revisadas pelos agentes em `docs/agentes/`. Veredito: `VALIDADO` ou `NÃO VALIDADO`.

| Tipo de mudança | Agente |
|---|---|
| Backend: Python, endpoint, schema, model, migration, regra, segurança, testes | `docs/agentes/agente-backend.md` |
| Frontend: tela, fluxo, câmera, GPS, experiência do usuário | `docs/agentes/agente-frontend.md` |
| Relatório, exportação ou documentação | `docs/agentes/agente-relatorios.md` |

Antes de declarar entrega pronta, informar: agentes acionados, veredito de cada um, evidências consideradas e pendências. Se qualquer agente emitir `NÃO VALIDADO`, a entrega não pode ser apresentada como pronta.

---

## 11. Política De Documentação

Atualizar na mesma entrega em que o código muda:

| Mudança | Documento |
|---|---|
| Regra ou requisito | `docs/requisitos.md` + `docs/regras-negocio.md` |
| Tela ou fluxo | `docs/telas-fluxos.md` |
| Entidade, campo ou constraint | `docs/modelo-dados.md` |
| Endpoint ou contrato | `docs/api.md` |
| Stack ou infraestrutura | `docs/arquitetura.md` |
| Estrutura, comandos ou estado do projeto | `AGENTS.md` + `CLAUDE.md` |

---

## 12. Critério De Pronto

Uma tarefa está concluída quando:

- código ou documento foi criado ou atualizado;
- regras obrigatórias foram respeitadas;
- testes foram criados ou atualizados quando aplicável;
- testes foram executados e aprovados;
- agentes validadores foram acionados quando aplicável;
- vereditos foram informados ao usuário com evidências;
- documentação afetada foi atualizada;
- limitações ou pendências foram informadas.

---

## 13. Estilo De Resposta

- Português brasileiro sempre.
- Curto, objetivo e técnico.
- Sem explicações genéricas.
- Títulos e listas quando ajudarem a leitura.
- Arquivos, comandos, variáveis e funções entre crases.
- Não criar arquivos ou código sem pedido prático do usuário.

---

## 14. Como Agir Em Caso De Dúvida

Dúvida que bloqueia decisão de produto, segurança, custo ou arquitetura → perguntar antes de implementar.

Dúvida pequena com opção conservadora alinhada à documentação → seguir a opção mais simples e registrar a decisão no arquivo afetado.
