# 📊 Estrutura de Agents — Referência Visual

> Diagrama visual da hierarquia de templates e como usá-los.

---

## Hierarquia de Arquivos

```
┌─────────────────────────────────────────────────────────────────┐
│  agents-base.md (Template Completo)                             │
│  ────────────────────────────────────────────────────────────── │
│  • 15 seções (1-15)                                             │
│  • ~600 linhas                                                  │
│  • Inclui: KB structure, SubAgents, Convenções                 │
│  • Público: Projetos complexos, long-term, multi-equipe        │
│  • Tempo preenchimento: 2-4 horas                              │
│                                                                 │
│  ✓ Use para: Plataforma SaaS, sistema enterprise               │
│  ✓ Copia para: AGENTS.md em projeto novo                      │
│                                                                 │
│         ↓ DUPLICAR & ADAPTAR ↓                                │
│                                                                 │
│  AGENTS.md (Instância do Projeto Novo)                         │
│  ────────────────────────────────────────────────────────────── │
│  • Preenchido com dados REAIS do seu projeto                   │
│  • Exemplo real neste workspace: ITINERÁRIO BELLO/AGENTS.md   │
│  • Lido pela IA no início de CADA conversa                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  agents-template.md (Template Minimalista)                      │
│  ────────────────────────────────────────────────────────────── │
│  • 11 seções (1-11)                                             │
│  • ~150 linhas                                                  │
│  • Essencial: contexto, arquitetura, regras, roadmap          │
│  • Público: Projetos simples, MVP, prototipagem                │
│  • Tempo preenchimento: 15-30 min                              │
│                                                                 │
│  ✓ Use para: Startup, CRUD simples, proof-of-concept           │
│  ✓ Copia para: AGENTS.md em projeto novo                      │
│                                                                 │
│         ↓ DUPLICAR & ADAPTAR ↓                                │
│                                                                 │
│  AGENTS.md (Instância do Projeto Novo)                         │
│  ────────────────────────────────────────────────────────────── │
│  • Preenchido com dados REAIS do seu projeto                   │
│  • Exemplo real neste workspace: ITINERÁRIO BELLO/AGENTS.md   │
│  • Lido pela IA no início de CADA conversa                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  COMO_USAR_AGENTS.md (Este Guia)                                │
│  ────────────────────────────────────────────────────────────── │
│  • Como escolher template                                       │
│  • Como preencher AGENTS.md                                    │
│  • Exemplos reais                                              │
│  • Checklist                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  AGENTS.md (Este Workspace)                                     │
│  ────────────────────────────────────────────────────────────── │
│  • Instância real baseada em agents-template.md                │
│  • Projeto: CONTROLE ITINERÁRIO COMERCIAL BELLO               │
│  • Público: Motoristas, coordenadores, supervisores           │
│  • Tecnologias: Python FastAPI + PostgreSQL + React Native    │
│                                                                 │
│  → Use como REFERÊNCIA para preencher seu AGENTS.md           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Mapa Mental: Qual Template Usar?

```
                         NOVO PROJETO?
                              │
                ┌─────────────┴─────────────┐
                │                           │
          [SIMPLES]                   [COMPLEXO]
                │                           │
        ├ MVP                      ├ SaaS/Enterprise
        ├ Prototipo                ├ Multi-equipe
        ├ Startup                  ├ Long-term
        ├ CRUD básico              ├ Múltiplas camadas
        ├ ~2-4 sprints             ├ AI/agents
        ├ 1-2 devs                 ├ 5+ devs
        │                           │
        ▼                           ▼
   Copiar do                   Copiar do
   agents-template.md          agents-base.md
        │                           │
   15-30 min                    2-4 horas
   preencher                    preencher
        │                           │
        └──────────────┬────────────┘
                       │
                       ▼
           Salvar como AGENTS.md
                       │
                       ▼
           Commitir no repositório
                       │
         Próxima conversa com IA:
    "Por favor, leia AGENTS.md e..."
```

---

## Comparação: Template vs Template

| Aspecto | agents-template.md | agents-base.md |
|---------|-------------------|-----------------|
| **Linhas** | ~150 | ~600 |
| **Seções** | 11 | 15 |
| **Setup** | 15-30 min | 2-4 horas |
| **KB Structure** | ❌ | ✅ |
| **SubAgents** | ❌ | ✅ |
| **Convenções** | Básicas | Detalhadas |
| **Exemplos** | Mínimos | Completos |
| **Roadmap** | 3-4 sprints | Estruturado por fase |
| **Bom para** | Simples | Complexo |
| **Prototipagem** | ✅ | ❌ |
| **Enterprise** | ❌ | ✅ |

---

## Fluxo de Trabalho Recomendado

```
SEMANA 1: Definição do Projeto
├─ [DIA 1] Conversa inicial com stakeholders
│  └─ Coletar: nome, objetivo, público, tecnologias
│
├─ [DIA 2] Decidir: Simples ou Complexo?
│  ├─ Simples → Copiar agents-template.md
│  └─ Complexo → Copiar agents-base.md
│
└─ [DIA 3-5] Preencher AGENTS.md
   ├─ Seção 2: Contexto + personas
   ├─ Seção 3: Stack + arquitetura
   ├─ Seção 5: Modelo de dados
   ├─ Seção 6: Regras obrigatórias
   ├─ Seção 9: Roadmap
   └─ Commit!

SEMANA 2+: Desenvolvimento
├─ TODA conversa com IA começa com:
│  "Leia AGENTS.md e me ajude com..."
│
└─ Resultado:
   ✓ Respostas alinhadas ao projeto
   ✓ Código contextualizado
   ✓ Sugestões smart (não genéricas)
```

---

## Checklist: Antes de Commitar AGENTS.md

### ✅ Contexto (Seção 2)
- [ ] Nome, plataforma, problema preenchidos
- [ ] 2-3 personas descritas com necessidades
- [ ] Objetivo claro ("O que o usuário consegue fazer agora que antes não conseguia?")

### ✅ Arquitetura (Seção 3)
- [ ] Stack reflete tecnologias REAIS (não wishlist)
- [ ] Componentes principais descritos (3-4 pilares)
- [ ] Estrutura de diretórios corresponde ao repo

### ✅ Dados (Seção 5)
- [ ] Entidades principais listadas
- [ ] Schemas Pydantic com validações
- [ ] Enums/constantes definidas

### ✅ Regras (Seção 6)
- [ ] Cada regra tem: descrição + impacto + onde validar
- [ ] Regras de acesso (RBAC) definidas
- [ ] Validações críticas documentadas

### ✅ APIs (Seção 7, se aplicável)
- [ ] Endpoints listados com métodos HTTP
- [ ] Request/response de exemplo
- [ ] Status codes documentados

### ✅ Sucesso (Seção 8)
- [ ] Critérios mensuráveis (não genéricos)
- [ ] Métricas de qualidade de dados
- [ ] Critério "pronto para produção"

### ✅ Roadmap (Seção 9)
- [ ] Sprint 0 (Setup) com checklist
- [ ] Sprint 1 (Core) com APIs mínimas
- [ ] Sprints seguintes por prioridade
- [ ] Realista (não otimista demais)

### ✅ Comportamento da IA (Seção 10-11)
- [ ] Idioma definido (ex: português do Brasil)
- [ ] Estilo de resposta claro
- [ ] Quando implementar vs. sugerir

### ✅ Limpeza Final
- [ ] Nenhum `[PLACEHOLDER]` deixado
- [ ] Nenhuma seção em branco (remova se não aplica)
- [ ] Sem "TODO" ou "FIXME" não resolvidos
- [ ] Formato consistente (markdown bem formatado)

---

## Exemplo Passo a Passo: Criando AGENTS.md para Novo Projeto

### Projeto: "App de Delivery Local"

**Passo 1:** Decidir entre templates
```
Características:
- 2 devs
- MVP em 2 meses
- Simples: restaurante → pedidos → entrega
- Sem IA/agents complexos

Decisão: Usar agents-template.md ✓
```

**Passo 2:** Copiar template
```bash
cp agents-template.md my-delivery-app/AGENTS.md
cd my-delivery-app
```

**Passo 3:** Preencher Seção 2
```markdown
## 2. Contexto do Projeto

| Campo | Valor |
|-------|-------|
| **Nome** | App de Delivery Local |
| **Plataforma** | Mobile (React Native) + Web (React) |
| **Problema** | Restaurantes locais precisam gerenciar pedidos e entregas |
| **Público-alvo** | Donos de restaurante, entregadores, clientes |
| **Linguagem** | Português do Brasil |
| **Estado** | MVP |
| **Prioridade** | Entrega em 2 meses com core features |

### 2.1 Visão geral

App que conecta restaurantes locais com entregadores e clientes.
Resolve: falta de sistema de pedidos digital para pequenos restaurantes.
Para: donos de restaurante e clientes que querem pedir online.

### 2.2 Personas

👤 Dona do Restaurante
- Responsabilidade: Gerenciar cardápio, pedidos, entregas
- Necessidade: Receber pedidos e acompanhar entrega
- Pain point: Usa WhatsApp/telefone, desorganizado
- Sucesso quando: Recebe pedido, aceita/rejeita, vê entregador saindo

👤 Entregador
- Responsabilidade: Buscar pedido, entregar para cliente
- Necessidade: Saber rota, localização cliente, contato
- Pain point: Sem sistema de rastreamento
- Sucesso quando: GPS ativo, cliente vê localização real-time

👤 Cliente
- Responsabilidade: Fazer pedido
- Necessidade: Ver cardápio, histórico, status
- Pain point: Ligações para confirmar
- Sucesso quando: Pede online, rastreia entrega, avalia
```

**Passo 4:** Preencher Seção 3 (Stack)
```markdown
## 3. Arquitetura

### 3.1 Stack
| Camada | Tecnologia | Justificativa |
|--------|-----------|--------------|
| Backend | FastAPI (Python) | Rápido, validação automática |
| Banco Dados | PostgreSQL | Relações entre restaurante→pedido→entrega |
| Frontend Mobile | React Native | iOS + Android da mesma base |
| Frontend Web | React | Dashboard para restaurante |
| Maps | Google Maps API | Rastreamento e rotas |
| Pagamento | Stripe | Processamento de cartão |
| DevOps | Docker + AWS | Escalável no futuro |

### 3.2 Componentes
1. **Backend API:** Endpoints para restaurante, pedido, entrega
2. **Cliente Mobile:** App do entregador (GPS ativo) + App cliente (pedido)
3. **Dashboard Web:** Restaurante gerencia cardápio/pedidos
4. **Payment Gateway:** Integração Stripe

### 3.3 Estrutura
```
my-delivery-app/
├── backend/
│   ├── models.py
│   ├── api.py
│   └── tests/
├── mobile/
│   ├── src/
│   └── app.json
├── web/
│   ├── src/
│   └── package.json
└── infra/docker-compose.yml
```
```

**Passo 5:** Preencher Seção 5 (Modelo)
```markdown
## 5. Modelo de Dados

### 5.1 Entidades

```
Restaurantes → Menu → Pedidos → Items ← Deliveries
```

Tabelas:
- `restaurants`: id, nome, endereco, telefone
- `menu_items`: id, restaurant_id, nome, preco, imagem
- `orders`: id, restaurant_id, customer_id, status, total
- `order_items`: id, order_id, menu_item_id, qtd
- `deliveries`: id, order_id, driver_id, status, gps_start, gps_end

### 5.2 Schemas Pydantic

```python
class OrderCreate(BaseModel):
    restaurant_id: int
    customer_id: int
    items: List[OrderItemCreate]
    
    @validator('items')
    def min_items(cls, v):
        if len(v) < 1:
            raise ValueError('Pedido precisa de pelo menos 1 item')
        return v

class DeliveryStart(BaseModel):
    order_id: int
    driver_id: int
    gps_start: dict  # {"lat": ..., "lng": ...}
```
```

**Passo 6:** Preencher Seção 6 (Regras)
```markdown
## 6. Regras e Requisitos

### 6.1 Regras Obrigatórias

✓ Pedido não pode ser vazio
  - Validação: Pydantic (min_items)
  - Impacto: Evita pedidos fantasma

✓ Entregador deve estar com GPS ativo durante entrega
  - Validação: Mobile + API (GPS refresh a cada 30s)
  - Impacto: Cliente vê localização real-time

✓ Cliente não pode pedir após restaurante fechar
  - Validação: API valida horário de funcionamento
  - Impacto: Pedidos para fora do horário rejeitados

✓ Pagamento deve ser processado antes de confirmar pedido
  - Validação: Stripe callback + DB transaction
  - Impacto: Garantir pagamento recebido
```

**Passo 7:** Preencher Roadmap
```markdown
## 9. Roadmap

### Sprint 0: Setup (1 week)
- [ ] Repo + Docker compose
- [ ] PostgreSQL schema
- [ ] FastAPI starter
- [ ] Tests setup

### Sprint 1: Core (2 weeks)
- [ ] Autenticação (JWT)
- [ ] CRUD Restaurante + Cardápio
- [ ] CRUD Pedidos (cliente → restaurante)
- [ ] Status de pedido (novo, aceito, pronto, saindo, entregue)
- [ ] Testes 80% coverage

### Sprint 2: Entrega (2 weeks)
- [ ] Entregador app (React Native + GPS)
- [ ] Rastreamento real-time
- [ ] Notificações push
- [ ] Avaliação

### Sprint 3: Web Dashboard (1 week)
- [ ] Dashboard restaurante (React)
- [ ] Relatórios básicos
- [ ] Deploy AWS

### Sprint 4: Polish (1 week)
- [ ] UX refinement
- [ ] Bug fixes
- [ ] Performance
```

**Passo 8:** Commitar
```bash
git add AGENTS.md
git commit -m "docs: criar AGENTS.md para App Delivery Local"
git push
```

---

## Resultado Final

Uma vez que `AGENTS.md` está preenchido e commitado:

```bash
# Próxima conversa com IA:
"@copilot: Leia AGENTS.md e me ajude a criar o endpoint POST /orders"

Copilot:
✓ Lê AGENTS.md
✓ Vê que: FastAPI + PostgreSQL + validação de itens
✓ Vê que: Restaurante precisa estar aberto
✓ Vê que: Pagamento via Stripe
✓ Gera endpoint com:
  - Validação Pydantic
  - Autenticação JWT
  - Stripe integration
  - DB transaction
  - Erro handling
✓ Explica cada parte

RESULTADO: Código pronto, contextualizado, sem genéricos!
```

---

## 🎯 Resumo Final

| Ação | Template | Tempo | Benefício |
|------|----------|-------|-----------|
| Projeto SIMPLES | agents-template.md | 15-30 min | Rápido, essencial |
| Projeto COMPLEXO | agents-base.md | 2-4 horas | Completo, escalável |
| Toda conversa | AGENTS.md | ∞ | IA entende contexto |

**Mantra:** "Sem `AGENTS.md` = respostas genéricas. Com `AGENTS.md` = respostas smart."

---

Voltar para: [COMO_USAR_AGENTS.md](../COMO_USAR_AGENTS.md)
