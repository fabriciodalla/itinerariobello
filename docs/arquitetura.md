# Arquitetura Técnica

## 1. Visão Geral

O protótipo deve ser uma aplicação mobile conectada a uma API REST em Python. A API salva dados no PostgreSQL, armazena fotos localmente no servidor, registra GPS com endereço aproximado quando disponível e expõe informações para fechamento mensal e relatórios mensais.

## 2. Stack

| Camada | Tecnologia | Motivo |
|---|---|---|
| API | FastAPI | Framework Python rápido, simples e com documentação automática |
| Banco | PostgreSQL | Banco relacional robusto para viagens, usuários, veículos e fechamentos mensais |
| ORM | SQLAlchemy | Mapeamento entre tabelas e objetos Python |
| Migrations | Alembic | Controle versionado de alterações no banco |
| Validação | Pydantic | Validação de entrada e saída da API |
| Testes | Pytest | Testes automatizados simples e maduros no ecossistema Python |
| Containers | Docker Compose | Execução padronizada de API, banco e serviços auxiliares |
| Cliente mobile | Progressive Web App (PWA) | Interface responsiva acessível via navegador com suporte offline, câmera e GPS |
| Framework PWA | React 18 com TypeScript | Biblioteca JavaScript com tipos estáticos para componentes reutilizáveis; React 18 mantém compatibilidade com as bibliotecas mobile escolhidas |
| Build tool | Vite | Bundler ultra-rápido com Hot Module Replacement instantâneo |
| PWA Features | Workbox + react-pwa-install | Google Workbox para Service Workers, offline-first; library para prompts de instalação |
| Câmera | Input nativo HTML com `capture="environment"` | Abre diretamente a câmera traseira do celular e evita prévia preta no PWA |
| GPS | react-use-geolocation | Hook React para captura de localização GPS |
| E-mail transacional | SMTP via biblioteca padrão Python | Envio de link de recuperação de senha sem adicionar dependência |

## 3. Serviços Docker Esperados

| Serviço | Função |
|---|---|
| `api` | Backend FastAPI |
| `frontend` | Nginx que serve o PWA e faz proxy para a API |
| `db` | PostgreSQL |
| `storage` | Pasta ou volume local para fotos do protótipo |

### 3.1 Configuração Inicial Implementada

A configuração local inicial fica em:

| Arquivo | Responsabilidade |
|---|---|
| `docker-compose.yml` | Orquestra `api`, `frontend`, `db`, portas locais e volumes persistentes |
| `docker-compose.prod.example.yml` | Modelo de Compose para servidor HTTPS, expondo apenas Nginx nas portas `80` e `443` |
| `docker-compose.vm.yml` | Compose para VM compartilhada, usando proxy externo e frontend interno em `127.0.0.1:8082` |
| `backend/Dockerfile` | Cria a imagem Python da API FastAPI |
| `frontend/Dockerfile` | Compila o PWA e publica os arquivos estáticos via Nginx |
| `frontend/.dockerignore` | Reduz o contexto do build Docker, excluindo `node_modules`, `dist` e logs locais |
| `backend/requirements.txt` | Lista bibliotecas base do backend |
| `backend/pytest.ini` | Configura execução de testes dentro do container da API |
| `.env.example` | Documenta variáveis de ambiente locais |
| `.env.production.example` | Documenta variáveis esperadas para servidor publicado |
| `frontend/nginx.conf` | Configuração HTTP local do Nginx do frontend |
| `frontend/nginx.https.example.conf` | Modelo de configuração HTTPS do Nginx para publicação |
| `frontend/nginx.vm.conf` | Configuração HTTP interna para VM compartilhada atrás do proxy principal |
| `docs/deploy-https.md` | Roteiro operacional para publicação HTTPS, certificado, validação e backup |
| `docs/deploy-vm-compartilhada.md` | Roteiro operacional com etapas Local, WinSCP e PuTTY para a VM da empresa |
| `storage/photos/` | Diretório local usado pelo protótipo para fotos do hodômetro |

O serviço `api` usa `uvicorn` para expor `app.main:app` na porta `8000`. O serviço `frontend` usa Nginx para servir o PWA e encaminhar rotas da API. O serviço `db` usa PostgreSQL com volume persistente `postgres_data` e `healthcheck` via `pg_isready`.

As variáveis principais são:

| Variável | Uso |
|---|---|
| `API_PORT` | Porta local publicada para a API |
| `FRONTEND_HTTP_PORT` | Porta HTTP publicada para o Nginx do frontend |
| `FRONTEND_HTTPS_PORT` | Porta HTTPS publicada para o Nginx em ambiente publicado |
| `APP_DOMAIN` | Domínio usado no ambiente publicado |
| `APP_ENV` | Identifica o ambiente da API |
| `APP_DEBUG` | Ativa modo de depuração no ambiente local |
| `DATABASE_URL` | String de conexão SQLAlchemy com PostgreSQL |
| `POSTGRES_DB` | Nome do banco local |
| `POSTGRES_USER` | Usuário do PostgreSQL local |
| `POSTGRES_PASSWORD` | Senha do PostgreSQL local |
| `POSTGRES_PORT` | Porta local publicada para o PostgreSQL |
| `PHOTOS_DIR` | Caminho interno usado pela API para salvar fotos |
| `CORS_ORIGINS` | Origens permitidas para o futuro cliente mobile |
| `SECRET_KEY` | Chave usada para assinar tokens JWT; deve ser definida fora do ambiente local |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tempo de expiração do token de acesso |
| `REVERSE_GEOCODING_ENABLED` | Habilita consulta externa para resolver endereço a partir de latitude e longitude |
| `REVERSE_GEOCODING_PROVIDER` | Provedor de geocodificação reversa; no protótipo inicial, `nominatim` |
| `REVERSE_GEOCODING_TIMEOUT_SECONDS` | Tempo máximo da consulta de endereço |
| `REVERSE_GEOCODING_USER_AGENT` | Identificação enviada ao provedor de geocodificação |
| `NOMINATIM_REVERSE_URL` | URL do endpoint reverso do Nominatim quando esse provedor for usado |
| `FRONTEND_BASE_URL` | URL pública do PWA usada para montar links de recuperação de senha |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | Tempo de expiração do token de recuperação de senha |
| `SMTP_HOST` | Servidor SMTP usado para recuperação de senha |
| `SMTP_PORT` | Porta SMTP |
| `SMTP_USERNAME` | Usuário SMTP, quando exigido pelo provedor |
| `SMTP_PASSWORD` | Senha SMTP, quando exigida pelo provedor |
| `SMTP_FROM_EMAIL` | Remetente usado nos e-mails |
| `SMTP_FROM_NAME` | Nome de exibição do remetente |
| `SMTP_USE_TLS` | Habilita STARTTLS |
| `SMTP_USE_SSL` | Habilita conexão SMTP SSL direta |
| `SMTP_TIMEOUT_SECONDS` | Tempo máximo para conexão SMTP |

Se `SECRET_KEY` não for definida no ambiente local, a API gera uma chave efêmera ao iniciar. Isso permite desenvolvimento rápido, mas invalida tokens após reinício; em servidor de testes ou produção a variável deve ser configurada explicitamente.

## 4. Ambientes Previstos

O projeto deve ser preparado para funcionar em dois momentos:

| Ambiente | Quando usar | Objetivo |
|---|---|---|
| Local | Início do desenvolvimento | Criar backend, banco, regras, testes e fluxo principal com rapidez |
| Servidor de testes | Quando o MVP estiver avançado | Permitir acesso de usuários externos para validar o protótipo |

No início, os testes serão feitos localmente com `Docker Compose`, API, PostgreSQL e volume local para fotos.

Quando o projeto avançar, a aplicação deverá ser instalada em um servidor externo ainda não definido. Esse servidor será usado para testes reais com usuários autorizados e validação do MVP.

## 5. Hospedagem Do Protótipo

A escolha do servidor ainda está pendente. Pode ser uma VPS, ambiente em nuvem, servidor corporativo publicado ou outro provedor definido posteriormente.

Mesmo sem definir o provedor agora, o projeto deve ser desenvolvido considerando:

- execução via `Docker Compose`;
- API FastAPI publicada para acesso externo;
- PostgreSQL com volume persistente;
- volume ou diretório persistente para fotos;
- configuração por variáveis de ambiente;
- suporte a HTTPS no ambiente publicado;
- Nginx como porta de entrada HTTPS do PWA e proxy interno para a API;
- configuração de CORS para o cliente mobile;
- backup básico de banco e fotos antes de testes com usuários reais;
- logs suficientes para diagnosticar falhas de API, upload e banco.

## 6. Estrutura De Pastas Sugerida

```txt
backend/
  app/
    api/
      routes/
        auth.py
        signup_requests.py
        users.py
        vehicles.py
        trips.py
        reports.py
    core/
      config.py
      security.py
    db/
      base.py
      session.py
    models/
    schemas/
    services/
    repositories/
    tests/
  alembic/
  Dockerfile
frontend/
  src/
    screens/
      Login/
      Cadastros/
      SelecionarVeiculo/
      Partida/
      Chegada/
      Historico/
      FechamentoMensal/
    components/
    services/
    hooks/
    styles/
    types/
  assets/
  tests/
docker-compose.yml
docs/
  agentes/
```

## 7. Frontend Mobile: Progressive Web App (PWA)

Foi definido que o cliente mobile será desenvolvido como **Progressive Web App (PWA)**. Essa escolha permite:

- **Acesso via navegador**: funciona em qualquer dispositivo com navegador moderno (iOS, Android, desktop).
- **Suporte offline**: utiliza Service Workers para sincronizar dados quando conexão retorna.
- **Acesso a câmera e GPS**: APIs modernas do navegador permitem capturar fotos e localização.
- **Instalação como app**: pode ser instalado na tela inicial sem passar por app stores.
- **Desenvolvimento rápido**: tecnologia web (JavaScript/TypeScript) com estrutura simples.
- **Facilidade de deploy**: serve via servidor HTTP/HTTPS, sem necessidade de compilação ou distribuição em app stores.

O PWA foi iniciado em `frontend/` com **React 18 + TypeScript** e **Vite**, conforme stack oficial do projeto. A versão principal do React deve permanecer em `18.x` enquanto `react-use-geolocation` e `react-pwa-install` forem usados, para evitar incompatibilidades de runtime.

### 7.1 Organização Esperada

| Pasta | Responsabilidade |
|---|---|
| `frontend/src/screens/` | Telas principais do fluxo mobile |
| `frontend/src/components/` | Componentes reutilizáveis, como botões, campos, cards e indicadores |
| `frontend/src/services/` | Comunicação com a API, autenticação e upload |
| `frontend/src/hooks/` | Lógicas reutilizáveis, como sessão, câmera, GPS e permissões |
| `frontend/src/styles/` | Tema visual, espaçamentos, cores e padrões de interface |
| `frontend/src/types/` | Tipos e contratos usados pelo frontend |
| `frontend/public/` | Ícones, manifest gerado e arquivos públicos do PWA |
| `frontend/tests/` | Testes do cliente mobile |

### 7.2 Padrões Do Frontend

- Priorizar experiência mobile simples, rápida e objetiva.
- Seguir os fluxos definidos em `docs/telas-fluxos.md`.
- Consumir os contratos definidos em `docs/api.md`.
- Revalidar no frontend apenas para melhorar a experiência do usuário; regras críticas sempre devem ser validadas no backend.
- Isolar acesso a câmera, GPS e permissões em serviços ou hooks reutilizáveis.
- Resolver endereço aproximado no cliente chamando o endpoint autenticado `GET /geocoding/reverse`, mantendo a chave e o provedor de geocodificação no backend.
- Usar `endereco` apenas para endereço real resolvido; quando indisponível, usar `endereco_exibicao` e `endereco_resolvido` para tela e exportação sem gravar texto de fallback como endereço.
- Evitar acoplamento direto entre telas e detalhes internos da API.
- Manter nomes de telas alinhados ao domínio: `Login`, `SelecionarVeiculo`, `Partida`, `Chegada`, `Historico` e `FechamentoMensal`.
- O prompt de instalação usa `react-pwa-install`; por compatibilidade desse pacote legado, `@material-ui/core` fica instalado como dependência de runtime do diálogo de instalação.
- No fluxo principal de foto do hodômetro, o botão de câmera usa o input nativo do navegador com `capture="environment"` para abrir diretamente a câmera traseira do celular. Isso evita prévia preta em dispositivos móveis; bibliotecas de câmera ao vivo podem ser usadas apenas como evolução controlada.

### 7.3 Implantação E Hospedagem Do PWA

**Desenvolvimento local:**
- PWA roda em `http://localhost:3000` ou `http://localhost:5173` via dev server do framework escolhido.
- API FastAPI roda em `http://localhost:8000`.
- CORS é configurado para aceitar as origens locais `http://localhost:3000` e `http://localhost:5173`.
- Para teste em celular na mesma rede, o Compose local pode servir o PWA pelo Nginx em `http://IP_DA_MAQUINA/`, com proxy interno para a API.
- O build Docker do frontend usa `npm ci --legacy-peer-deps` por compatibilidade do `@material-ui/core` legado usado pelo prompt de instalação do PWA.

**Build para produção:**
- PWA é compilado para pasta `frontend/dist/` pelo Vite.
- Arquivos estáticos são servidos por servidor web (nginx, Apache ou similar).
- `public/manifest.json` define metadados do app para instalação em tela inicial.
- `public/service-worker.js` habilita sincronização offline.

**Hospedagem:**
- PWA será servido no mesmo servidor da API ou via CDN.
- Deve suportar HTTPS obrigatoriamente para acesso a câmera e GPS.
- Configurar headers HTTP para cachear assets estáticos e prevenir cache de HTML/manifest.

**Configuração de CORS:**
- Variável `CORS_ORIGINS` na API deve incluir a origem do PWA em produção.
- Exemplo: `CORS_ORIGINS=["https://app.bello.com.br"]`

### 7.4 Preparação Para HTTPS

Enquanto o servidor externo não estiver definido, o projeto mantém arquivos modelo para reduzir risco no momento da publicação:

| Arquivo | Finalidade |
|---|---|
| `.env.production.example` | Base para criar `.env.production` no servidor, sem versionar segredos |
| `docker-compose.prod.example.yml` | Modelo de execução com `api` e `db` privados e apenas o Nginx exposto |
| `frontend/nginx.https.example.conf` | Modelo de HTTPS com redirecionamento `80 -> 443`, proxy para API e cache do PWA |
| `docs/deploy-https.md` | Checklist de domínio, certificado, deploy, migrations, validação e backup |

No modelo recomendado para o protótipo publicado, o fluxo é:

```txt
Celular ou navegador
        |
        v
Nginx HTTPS na porta 443
        |
        +--> arquivos estáticos do PWA
        |
        +--> proxy interno para FastAPI em api:8000
        |
        +--> FastAPI acessa PostgreSQL em db:5432
```

Nesse desenho, as portas `8000` da API e `5432` do PostgreSQL não devem ser publicadas para a internet.

### 7.5 Deploy Em VM Compartilhada

Para a VM Ubuntu Server da empresa, onde `80`, `443` e `8080` ja estao ocupadas por outros projetos, o modelo recomendado e:

```txt
Usuario
        |
        v
Proxy HTTPS principal da VM em 443
        |
        v
http://127.0.0.1:8082
        |
        +--> frontend Nginx interno
        +--> API privada em api:8000
        +--> PostgreSQL privado em db:5432
```

Esse modo usa:

- `docker-compose.vm.yml`;
- `frontend/nginx.vm.conf`;
- `.env.production` com `FRONTEND_HTTP_PORT=8082`;
- proxy principal da VM apontando o dominio publico para `http://127.0.0.1:8082`.

As etapas operacionais ficam em `docs/deploy-vm-compartilhada.md`. Se o proxy principal tambem estiver em container Docker, pode ser necessario trocar o encaminhamento por uma rede Docker compartilhada.

## 8. Responsabilidades Por Camada

| Camada | Responsabilidade |
|---|---|
| `routes` | Receber requisições HTTP e chamar serviços |
| `schemas` | Validar entrada e saída com Pydantic |
| `models` | Representar tabelas do banco |
| `repositories` | Concentrar consultas e gravações no banco |
| `services` | Aplicar regras de negócio |
| `core` | Configurações, segurança e utilitários centrais |
| `tests` | Testes automatizados |
| `frontend/screens` | Telas do cliente mobile |
| `frontend/components` | Componentes visuais reutilizáveis |
| `frontend/services` | Integração com API, autenticação, câmera, GPS e uploads |
| `docs/agentes` | Pareceres operacionais para validação técnica por especialidade |

## 9. Segurança

- Senhas devem ser armazenadas com hash seguro.
- Tokens ou sessões devem ter expiração.
- Tokens de recuperação de senha devem ser armazenados somente como hash e usados uma única vez.
- Cadastro público deve criar apenas solicitação pendente; usuário ativo depende de aprovação admin.
- Dados de localização devem ser acessíveis apenas por usuários autorizados.
- Fotos devem ter controle de acesso.
- Logs não devem expor senha, token ou dados sensíveis desnecessários.
- Ao habilitar geocodificação reversa externa, latitude e longitude são enviadas ao provedor configurado; isso deve ser considerado dado sensível para LGPD.
- O projeto deve considerar LGPD desde o protótipo.

## 10. Armazenamento De Fotos

No protótipo:

- salvar fotos em volume local no servidor;
- guardar no banco apenas metadados e caminho do arquivo;
- validar formato e tamanho máximo;
- separar fotos por viagem ou data para facilitar manutenção.

Em produção:

- migrar para S3, Azure Blob ou serviço equivalente;
- usar URLs assinadas ou controle de acesso seguro.

## 11. Qualidade E Testes

Todos os processos críticos do projeto devem passar por testes antes de serem considerados prontos.

Além dos testes, mudanças relevantes devem acionar os agentes validadores definidos em `docs/agentes/` e `AGENTS.md`. O parecer desses agentes deve ser informado ao usuário com evidências objetivas antes de considerar a entrega pronta.

Isso inclui:

- regras de negócio;
- código Python, uso de bibliotecas do backend e dependências;
- endpoints da API;
- autenticação e permissões;
- criação, encerramento e fechamento mensal de viagens;
- validações de foto, GPS e quilometragem;
- geração e exportação de relatórios;
- integrações de armazenamento de fotos;
- validações e fluxos principais do frontend;
- configurações de ambiente local e servidor de testes.

Se uma implementação não passar nos testes aplicáveis, ela não deve ser entregue. A falha deve ser corrigida ou a implementação feita naquela entrega deve ser removida, sem apagar alterações anteriores do usuário sem autorização explícita.

### 11.1 Validação Obrigatória Em Toda Entrega

Toda alteração funcional deve executar os testes de validação aplicáveis antes de ser considerada concluída.

Comando mínimo:

```bash
pytest
```

Quando a alteração envolver banco de dados, migrations, endpoints, autenticação, permissões, viagens, fotos, GPS, fechamento mensal ou relatórios, os testes devem rodar contra uma base de teste descartável.

Se os testes não puderem ser executados, a entrega deve informar claramente:

- comando que deveria ter sido executado;
- motivo do bloqueio;
- risco da entrega sem validação;
- próxima ação necessária.

Detalhes ficam em `docs/testes.md`.

### 11.2 Auditoria De Risco Dos Testes

Todo teste automatizado deve ter marcador de risco com criticidade, peso, área e referências de regra ou requisito.

Escala oficial:

| Criticidade | Peso |
|---|---:|
| `critica` | 100 |
| `alta` | 50 |
| `media` | 20 |
| `baixa` | 5 |

A entrega só pode ser considerada pronta quando o relatório de risco indicar:

- `pontos_falha = 0`;
- `pontos_nao_validados = 0`;
- `indice_conformidade_percentual = 100`;
- `bloqueia_entrega = false`.

O relatório auditável padrão fica em `backend/app/tests/reports/risco-testes.json`.

## 12. Comandos Padrão

```bash
docker compose up -d
docker compose down
docker compose logs api
docker compose logs db
pytest
alembic upgrade head

# Validar modelo de produção
docker compose --env-file .env.production -f docker-compose.prod.example.yml config
```

## 13. Decisões Pendentes

| Decisão | Opções |
|---|---|
| Framework PWA | Definido: React com TypeScript e Vite |
| Estratégia de sessão | JWT Bearer inicial, com expiração configurável; refresh token segue pendente para fase posterior |
| Exportação de relatório | CSV, XLSX ou ambos |
| Hospedagem do protótipo | VPS, cloud corporativa, servidor interno publicado ou outro provedor; preparação HTTPS documentada em `docs/deploy-https.md` |
| Limite de foto | Definir tamanho máximo e compressão |
| Hospedagem do PWA | Recomendado inicialmente no mesmo servidor da API via Nginx; CDN separado segue como opção futura |
| Provedor definitivo de endereço | Protótipo suporta Nominatim configurável; produção deve confirmar provedor, limites, custo e LGPD |
