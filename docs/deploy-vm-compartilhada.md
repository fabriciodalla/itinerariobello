# Deploy Em VM Compartilhada

Este roteiro e para a VM Ubuntu Server da empresa, onde Docker Engine e Docker Compose ja existem e as portas `80`, `443` e `8080` ja estao ocupadas por outros projetos.

## Como Vamos Trabalhar

| Momento | Responsavel | Acao |
|---|---|---|
| Local | Codex | Ajustar arquivos, validar Compose e preparar checklist |
| WinSCP | Usuario | Transferir arquivos do projeto para a VM |
| PuTTY | Usuario com orientacao do Codex | Criar `.env.production`, subir containers, rodar migrations e configurar proxy |

## Desenho Recomendado

```txt
Usuario
  -> https://itinerario.dominio.com.br
  -> proxy principal da VM em 443
  -> http://127.0.0.1:8082
  -> container frontend
  -> container api:8000
  -> container db:5432
```

O stack do Itinerario nao publica `80`, `443`, `8080`, `8000` nem `5432` para a rede. O unico ponto publicado no host e `127.0.0.1:8082`, usado pelo proxy principal.

## Arquivos Criados Para Esse Cenario

| Arquivo | Uso |
|---|---|
| `docker-compose.vm.yml` | Compose para VM compartilhada, com frontend em `127.0.0.1:8082` |
| `frontend/nginx.vm.conf` | Nginx interno sem TLS, com proxy para a API |

## Quando Avisar WinSCP

Avisar WinSCP quando os arquivos locais estiverem revisados. Transferir para uma pasta do servidor, por exemplo:

```bash
/opt/itinerario-bello
```

Transferir:

- `backend/`
- `frontend/`
- `docs/`
- `docker-compose.vm.yml`
- `.env.production` somente se ja estiver preenchido com valores reais
- `AGENTS.md`
- `CLAUDE.md`
- `pytest.ini`

Nao transferir:

- `frontend/node_modules/`
- `frontend/dist/`
- `backend/app/__pycache__/`
- `.env`
- `.env.local`
- `certs/`
- arquivos `.xlsx`, exceto quando forem usados para importacao real
- `storage/photos/`, se a producao for com base limpa

## Quando Avisar PuTTY

Avisar PuTTY depois que os arquivos estiverem na VM.

Entrar na pasta:

```bash
cd /opt/itinerario-bello
```

Gerar `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Criar ou editar `.env.production` com:

```env
APP_ENV=production
APP_DEBUG=false
APP_DOMAIN=https://itinerario.dominio.com.br
FRONTEND_HTTP_PORT=8082
POSTGRES_DB=itinerario_bello
POSTGRES_USER=bello
POSTGRES_PASSWORD=SENHA_FORTE_DO_BANCO
DATABASE_URL=postgresql+psycopg://bello:SENHA_FORTE_DO_BANCO@db:5432/itinerario_bello
SECRET_KEY=SECRET_KEY_GERADA
ACCESS_TOKEN_EXPIRE_MINUTES=10080
CORS_ORIGINS=https://itinerario.dominio.com.br
PHOTOS_DIR=/app/storage/photos
REVERSE_GEOCODING_ENABLED=false
REVERSE_GEOCODING_PROVIDER=nominatim
REVERSE_GEOCODING_TIMEOUT_SECONDS=3
REVERSE_GEOCODING_USER_AGENT=itinerario-bello-vm/1.0
NOMINATIM_REVERSE_URL=https://nominatim.openstreetmap.org/reverse
FRONTEND_BASE_URL=https://itinerario.dominio.com.br
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=60
SMTP_HOST=smtp.dominio.com.br
SMTP_PORT=587
SMTP_USERNAME=usuario-smtp
SMTP_PASSWORD=SENHA_SMTP
SMTP_FROM_EMAIL=nao-responda@dominio.com.br
SMTP_FROM_NAME=Itinerario Bello
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT_SECONDS=10
```

Validar Compose:

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml config
```

Subir containers:

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml up -d --build
```

Aplicar migrations:

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml exec api alembic upgrade head
```

Validar localmente na VM:

```bash
curl -I http://127.0.0.1:8082/health
```

## Proxy Principal Da VM

Exemplo de bloco Nginx no proxy principal da VM:

```nginx
server {
    listen 80;
    server_name itinerario.dominio.com.br;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name itinerario.dominio.com.br;

    ssl_certificate     /caminho/fullchain.pem;
    ssl_certificate_key /caminho/privkey.pem;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
```

Se o proxy principal tambem estiver em container Docker, pode ser necessario usar uma rede Docker compartilhada em vez de `127.0.0.1:8082`.

## Alternativa: Acesso Direto Pela Rede Local, Sem Dominio

Quando ainda nao existe dominio nem proxy principal configurado para este projeto, e o objetivo e apenas abrir o app a partir de outros computadores/celulares da mesma rede local, use o IP da VM diretamente.

Camera, GPS e a instalacao do PWA exigem contexto seguro (HTTPS) em qualquer origem que nao seja `localhost`. Como so ha uma porta externa liberada (`8082`), o `docker-compose.vm.yml` mapeia essa porta direto para o bloco HTTPS (443) do Nginx interno, com certificado autoassinado gerado no build da imagem do frontend com o IP da VM no `subjectAltName` (`CERT_SAN_IP`, ver `frontend/Dockerfile` e `docker-compose.vm.yml`). Nao ha mais acesso HTTP puro nessa porta.

Descobrir o IP da VM na rede local:

```bash
hostname -I
```

Adicionar ao `.env.production`, alem das variaveis da secao anterior:

```env
VM_LAN_IP=192.168.0.50
FRONTEND_HTTP_PORT=8082
CORS_ORIGINS=https://192.168.0.50:8082
FRONTEND_BASE_URL=https://192.168.0.50:8082
COOKIE_SECURE=true
```

Como `APP_DOMAIN` nao existe nesse cenario, basta remover essa linha do `.env.production` (ela so e usada como referencia documental, nao e lida pelo Compose).

Subir (o `--build` e obrigatorio para gravar `VM_LAN_IP` no certificado):

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml up -d --build
docker compose --env-file .env.production -f docker-compose.vm.yml exec api alembic upgrade head
```

A porta `8082` ja deve estar liberada no firewall (era usada para HTTP). Se precisar confirmar:

```bash
sudo ufw allow 8082/tcp
```

Acessar de outro computador da mesma rede: `https://192.168.0.50:8082` (nao mais `http://`). O certificado e autoassinado, entao o navegador mostra aviso de seguranca — em Chrome/Edge, clicar em "Avancado" e depois "Continuar para o site" (uma vez por navegador/dispositivo).

Para trocar o IP depois (ex: a VM recebeu outro IP), atualizar `VM_LAN_IP` no `.env.production` e refazer o build:

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml up -d --build frontend
```

## Base Limpa

Para comecar producao sem banco e sem fotos locais, nao transferir `storage/photos/` e nao restaurar dump local.

Se for necessario apagar uma subida de teste deste stack:

```bash
docker compose --env-file .env.production -f docker-compose.vm.yml down
docker volume rm itinerario_bello_vm_postgres itinerario_bello_vm_fotos
```

Esse comando apaga permanentemente banco e fotos do stack da VM.

## Checklist De Aceite

- `curl -I http://127.0.0.1:8082/health` responde `200` na VM.
- `https://itinerario.dominio.com.br/health` responde `200` fora da VM.
- Login funciona via HTTPS.
- Camera abre no celular.
- GPS captura latitude e longitude.
- Foto do hodometro e enviada.
- API `8000` e banco `5432` nao ficam publicados externamente.
