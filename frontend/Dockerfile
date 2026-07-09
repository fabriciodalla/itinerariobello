FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build

FROM nginx:alpine

# CERT_SAN_IP: IP da rede local a incluir no certificado autoassinado
# (necessario para HTTPS via acesso direto por IP, sem dominio)
ARG CERT_SAN_IP=127.0.0.1

RUN apk add --no-cache openssl \
    && mkdir -p /etc/nginx/certs \
    && SAN="DNS:localhost,IP:127.0.0.1"; \
       if [ -n "$CERT_SAN_IP" ] && [ "$CERT_SAN_IP" != "127.0.0.1" ]; then SAN="$SAN,IP:$CERT_SAN_IP"; fi; \
       openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout /etc/nginx/certs/localhost.key \
        -out /etc/nginx/certs/localhost.crt \
        -subj "/CN=localhost" \
        -addext "subjectAltName=$SAN"

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80 443
