# Deploy HTTPS

Este roteiro prepara o projeto para publicacao em servidor externo, mantendo API e banco privados dentro do Docker Compose e expondo apenas o Nginx nas portas `80` e `443`.

## Arquivos Preparados

| Arquivo | Uso |
|---|---|
| `.env.production.example` | Modelo das variaveis de ambiente de producao |
| `docker-compose.prod.example.yml` | Compose completo para servidor publicado |
| `frontend/nginx.https.example.conf` | Modelo de Nginx com HTTPS e proxy para a API |

Arquivos reais com segredo nao devem ser versionados: `.env.production` e `certs/`.

## Antes De Ter Servidor

1. Definir o dominio publico ou interno, por exemplo `itinerario.bello.com.br`.
2. Reservar as portas `80` e `443` para o Nginx.
3. Definir quem vai emitir o certificado:
   - Let's Encrypt, se o dominio for publico;
   - certificado corporativo, se o acesso for interno/VPN;
   - certificado autoassinado apenas para teste tecnico.
4. Gerar uma `SECRET_KEY` forte e exclusiva para o ambiente.
5. Definir senha forte do PostgreSQL.

## Preparar O Servidor

No servidor, criar o arquivo real de ambiente a partir do modelo:

```bash
cp .env.production.example .env.production
```

Editar `.env.production` e trocar:

- `APP_DOMAIN`;
- `POSTGRES_PASSWORD`;
- senha dentro de `DATABASE_URL`;
- `CORS_ORIGINS`;
- `SECRET_KEY`;
- `FRONTEND_BASE_URL`;
- `SMTP_HOST`;
- `SMTP_FROM_EMAIL`;
- `SMTP_USERNAME` e `SMTP_PASSWORD`, quando o provedor exigir autenticação.

Criar a pasta de certificados:

```bash
mkdir -p certs
```

Colocar os arquivos abaixo, sem versionar:

```txt
certs/fullchain.pem
certs/privkey.pem
```

## Emitir Certificado

Com Let's Encrypt, uma opcao comum e emitir no host e depois copiar os arquivos para `certs/`:

```bash
sudo certbot certonly --standalone -d itinerario.bello.com.br
sudo cp /etc/letsencrypt/live/itinerario.bello.com.br/fullchain.pem certs/fullchain.pem
sudo cp /etc/letsencrypt/live/itinerario.bello.com.br/privkey.pem certs/privkey.pem
sudo chown "$USER":"$USER" certs/fullchain.pem certs/privkey.pem
```

Se for certificado corporativo, salvar o certificado completo como `certs/fullchain.pem` e a chave privada como `certs/privkey.pem`.

## Renovar Certificado

Quando o certificado for renovado no host, atualizar os arquivos montados no container e recarregar o Nginx:

```bash
sudo certbot renew
sudo cp /etc/letsencrypt/live/itinerario.bello.com.br/fullchain.pem certs/fullchain.pem
sudo cp /etc/letsencrypt/live/itinerario.bello.com.br/privkey.pem certs/privkey.pem
docker compose --env-file .env.production -f docker-compose.prod.example.yml exec frontend nginx -s reload
```

## Ajustar Nginx

Antes de subir, trocar `itinerario.exemplo.com.br` em `frontend/nginx.https.example.conf` pelo dominio real.

Para producao definitiva, recomenda-se copiar o exemplo para um arquivo real nao ambiguo:

```bash
cp frontend/nginx.https.example.conf frontend/nginx.https.conf
```

Depois, ajustar o volume do `frontend` em `docker-compose.prod.example.yml` para apontar para `frontend/nginx.https.conf`.

## Validar Configuracao

Validar o Compose:

```bash
docker compose --env-file .env.production -f docker-compose.prod.example.yml config
```

Subir os containers:

```bash
docker compose --env-file .env.production -f docker-compose.prod.example.yml up -d --build
```

Aplicar migrations:

```bash
docker compose --env-file .env.production -f docker-compose.prod.example.yml exec api alembic upgrade head
```

Verificar saude da API via HTTPS:

```bash
curl -I https://itinerario.bello.com.br/health
```

## Backup Basico

Backup do banco:

```bash
docker compose --env-file .env.production -f docker-compose.prod.example.yml exec db pg_dump -U bello -d itinerario_bello > backup-itinerario.sql
```

Backup das fotos:

```bash
tar -czf backup-fotos.tar.gz storage/photos
```

Restauracao do banco em ambiente controlado:

```bash
docker compose --env-file .env.production -f docker-compose.prod.example.yml exec -T db psql -U bello -d itinerario_bello < backup-itinerario.sql
```

## Checklist De Aceite

- `https://dominio/health` responde `200`.
- Login funciona via HTTPS.
- Camera abre no celular.
- GPS captura latitude e longitude.
- Foto do hodometro e enviada com sucesso.
- PWA instala no celular.
- Porta `5432` do PostgreSQL nao esta exposta publicamente.
- Porta `8000` da API nao esta exposta publicamente.
- `APP_DEBUG=false`.
- `SECRET_KEY` nao esta vazia nem versionada.
