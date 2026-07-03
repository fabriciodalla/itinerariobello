# Deploy no Ubuntu — Itinerario Bello (porta 8082)

## Pre-requisitos no servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Instalar Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verificar instalacao
docker --version
docker compose version

# Abrir porta 8082 no firewall (se necessario)
sudo ufw allow 8082/tcp
```

## 1. Clonar o repositorio

```bash
cd /opt
sudo git clone <URL_DO_REPOSITORIO> itinerario-bello
sudo chown -R $USER:$USER itinerario-bello
cd itinerario-bello
```

## 2. Configurar variaveis de ambiente

```bash
# Copiar template e editar
cp .env.production.example .env.production
nano .env.production
```

**Campos obrigatorios para preencher:**

| Campo | O que colocar |
|---|---|
| `POSTGRES_PASSWORD` | Senha forte para o banco (gere com `openssl rand -base64 32`) |
| `DATABASE_URL` | Atualizar com a mesma senha do POSTGRES_PASSWORD |
| `SECRET_KEY` | Gerar com `python3 -c "from secrets import token_urlsafe; print(token_urlsafe(64))"` |
| `CORS_ORIGINS` | `http://IP_DO_SERVIDOR:8082` |
| `FRONTEND_BASE_URL` | `http://IP_DO_SERVIDOR:8082` |
| `SMTP_HOST` | Servidor SMTP (ex: `smtp.gmail.com`) |
| `SMTP_USERNAME` | Email para envio |
| `SMTP_PASSWORD` | Senha de app do email |
| `SMTP_FROM_EMAIL` | Email remetente |
| `COOKIE_SECURE` | `false` se HTTP, `true` se HTTPS |

**Se usar Gmail:**
1. Ativar verificacao em 2 etapas na conta Google
2. Gerar uma "Senha de app" em Seguranca > Senhas de app
3. Usar essa senha em `SMTP_PASSWORD`

## 3. Subir os containers

```bash
# Validar a configuracao
docker compose --env-file .env.production -f docker-compose.vm.yml config

# Build e start
docker compose --env-file .env.production -f docker-compose.vm.yml up -d --build
```

## 4. Aplicar migracoes do banco

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml exec api alembic upgrade head
```

## 5. Criar usuario administrador inicial

Antes de rodar, edite o `backend/seed_producao.py` com o email e senha do admin real:

```bash
nano backend/seed_producao.py
```

Depois rode:

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml exec api python seed_producao.py
```

## 6. Verificar se esta funcionando

```bash
# Health check da API
curl http://localhost:8082/health

# Verificar containers
docker compose --env-file .env.production -f docker-compose.vm.yml ps

# Ver logs
docker compose --env-file .env.production -f docker-compose.vm.yml logs -f
```

Acesse `http://IP_DO_SERVIDOR:8082` no navegador.

## Comandos uteis

```bash
# Parar todos os containers
docker compose --env-file .env.production -f docker-compose.vm.yml down

# Reiniciar
docker compose --env-file .env.production -f docker-compose.vm.yml restart

# Ver logs da API
docker compose --env-file .env.production -f docker-compose.vm.yml logs -f api

# Ver logs do banco
docker compose --env-file .env.production -f docker-compose.vm.yml logs -f db

# Acessar o banco de dados
docker compose --env-file .env.production -f docker-compose.vm.yml exec db psql -U bello -d itinerario_bello

# Rebuild apos atualizar codigo
docker compose --env-file .env.production -f docker-compose.vm.yml up -d --build

# Aplicar novas migracoes apos atualizacao
docker compose --env-file .env.production -f docker-compose.vm.yml exec api alembic upgrade head
```

## Backup do banco

```bash
# Criar backup
docker compose --env-file .env.production -f docker-compose.vm.yml exec db \
  pg_dump -U bello itinerario_bello > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker compose --env-file .env.production -f docker-compose.vm.yml exec -T db \
  psql -U bello -d itinerario_bello < backup_arquivo.sql
```

## Seguranca em producao

- Swagger/OpenAPI esta **desabilitado** automaticamente (APP_ENV=production)
- Headers de seguranca (X-Frame-Options, HSTS, etc.) ja ativos
- Rate limiting no login (5/min) e cadastro (3/min)
- JWT com chave secreta forte
- Fotos validadas por tipo (JPEG, PNG, WEBP) e tamanho (5MB max)
- Banco PostgreSQL nao expoe porta externamente
- Containers rodam com usuario nao-root
