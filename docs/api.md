# API REST Inicial

## 1. Padrões Gerais

- Backend em Python com `FastAPI`.
- Respostas em JSON.
- Autenticação real com e-mail e senha.
- Endpoints protegidos devem exigir token de acesso.
- Validações críticas devem ocorrer no backend.
- Upload de fotos deve aceitar arquivos de imagem definidos pela configuração do projeto.
- Localizações GPS devem retornar latitude, longitude, endereço aproximado quando disponível, status de resolução e texto de exibição quando não houver endereço resolvido.
- Aprovação individual de viagem não faz parte do fluxo vigente; o fechamento mensal por motorista usa apenas os status `aberto` e `fechado`.

## 2. Infraestrutura

| Método | Endpoint | Finalidade | Autenticação |
|---|---|---|---|
| `GET` | `/health` | Verificar se a API está respondendo | Não |

Resposta esperada:

```json
{
  "status": "ok",
  "app": "Controle Itinerario Comercial Bello",
  "environment": "local"
}
```

## 3. Autenticação

| Método | Endpoint | Finalidade |
|---|---|---|
| `POST` | `/auth/login` | Autenticar usuário |
| `POST` | `/auth/logout` | Encerrar sessão |
| `POST` | `/auth/forgot-password` | Solicitar recuperação de senha |
| `POST` | `/auth/reset-password` | Definir nova senha |
| `GET` | `/auth/me` | Retornar usuário autenticado |

O login retorna um token Bearer com expiração configurável:

```json
{
  "access_token": "token-jwt",
  "token_type": "bearer"
}
```

Endpoints protegidos devem receber o cabeçalho `Authorization: Bearer <token>`.
Quando cabeçalho Bearer e cookie de sessão estiverem presentes ao mesmo tempo, o cabeçalho Bearer tem precedência.

Recuperação de senha:

- `POST /auth/forgot-password` recebe `{ "email": "usuario@bello.local" }` e retorna `202`, sem informar se o e-mail existe.
- Se o e-mail pertencer a usuário ativo, a API cria token temporário, salva apenas o hash e envia link para `FRONTEND_BASE_URL/?reset_token=...`.
- `POST /auth/reset-password` recebe `{ "token": "token-de-recuperacao", "nova_senha": "nova-senha" }`.
- Tokens inválidos, expirados, já usados ou vinculados a usuário inativo retornam `400`.

## 4. Solicitações De Cadastro

| Método | Endpoint | Finalidade | Autenticação |
|---|---|---|---|
| `POST` | `/signup-requests` | Criar solicitação pública de cadastro | Não |
| `GET` | `/signup-requests` | Listar solicitações | Admin |
| `POST` | `/signup-requests/{id}/approve` | Aprovar solicitação e criar usuário/veículo | Admin |
| `POST` | `/signup-requests/{id}/reject` | Reprovar solicitação | Admin |

Criação pública:

```json
{
  "nome": "Nome do Usuario",
  "email": "usuario@bello.local",
  "cargo": "Vendedor",
  "superior": "Nome do Superior",
  "veiculo_placa": "ABC1234",
  "veiculo_modelo": "Onix",
  "veiculo_marca": "Chevrolet",
  "observacao": "Opcional"
}
```

A resposta retorna status `pendente`. O usuário ainda não consegue fazer login.

Aprovação:

```json
{
  "senha_temporaria": "senha-com-8-ou-mais-caracteres",
  "perfil": "motorista",
  "superior_id": "uuid-do-superior-ou-null",
  "pode_aprovar": false,
  "tipo_veiculo": "proprio",
  "tipo_disponibilidade": "fixo"
}
```

`tipo_disponibilidade` é opcional. Quando omitido, veículos `proprio` ou `alugado` viram `fixo`; veículo `empresa` vira `alocado`.

Reprovação:

```json
{
  "motivo": "Dados incompletos."
}
```

## 5. Usuários

| Método | Endpoint | Finalidade | Perfil mínimo |
|---|---|---|---|
| `GET` | `/users` | Listar usuários | Admin |
| `POST` | `/users` | Criar usuário | Admin |
| `GET` | `/users/{id}` | Detalhar usuário | Admin |
| `PATCH` | `/users/{id}` | Atualizar usuário | Admin |
| `PATCH` | `/users/{id}/status` | Ativar ou inativar usuário | Admin |

## 6. Veículos

| Método | Endpoint | Finalidade | Perfil mínimo |
|---|---|---|---|
| `GET` | `/vehicles` | Listar veículos disponíveis | Motorista |
| `GET` | `/vehicles/in-route` | Listar veículos em rota com motorista da viagem em andamento | Autenticado |
| `POST` | `/vehicles` | Cadastrar veículo | Admin |
| `GET` | `/vehicles/{id}` | Detalhar veículo | Motorista |
| `PATCH` | `/vehicles/{id}` | Atualizar veículo | Admin |
| `PATCH` | `/vehicles/{id}/status` | Ativar ou inativar veículo | Admin |

Na listagem para partida, a API deve retornar apenas veículos permitidos para o usuário autenticado:

- veículo `proprio` associado ao próprio usuário;
- veículos `empresa` com `ativo = true`;
- veículos sem itinerário iniciado no dia.

Quando um veículo `empresa` tiver `usuario_responsavel_id`, ele deve aparecer priorizado para o responsável usual, mas continua compartilhável quando estiver disponível.

Consulta de veículos em rota:

```txt
GET /vehicles/in-route
```

Resposta:

```json
[
  {
    "viagem_id": "uuid-da-viagem",
    "veiculo_id": "uuid-do-veiculo",
    "placa": "ABC1234",
    "modelo": "Onix",
    "motorista_id": "uuid-do-motorista",
    "motorista_nome": "Nome do Motorista",
    "em_rota": true,
    "partida_em": "2026-05-01T08:00:00Z"
  }
]
```

Essa consulta considera apenas viagens com status `em_andamento` e não retorna GPS, fotos ou endereço.

Campos principais de veículo:

| Campo | Tipo | Descrição |
|---|---|---|
| `placa` | Texto | Placa única do veículo |
| `modelo` | Texto | Modelo do veículo |
| `marca` | Texto ou nulo | Marca do veículo |
| `tipo` | Enum | `proprio`, `alugado` ou `empresa` |
| `tipo_disponibilidade` | Enum | `fixo` ou `alocado` |
| `usuario_responsavel_id` | UUID ou nulo | Obrigatório para veículo `fixo` |
| `ativo` | Booleano | Define se o veículo pode ser usado |

## 7. Viagens

| Método | Endpoint | Finalidade | Perfil mínimo |
|---|---|---|---|
| `GET` | `/trips` | Listar viagens conforme permissão | Motorista |
| `POST` | `/trips/start` | Registrar partida | Motorista |
| `POST` | `/trips/{id}/finish` | Registrar chegada | Motorista |
| `GET` | `/trips/{id}` | Detalhar viagem | Motorista |
| `PATCH` | `/trips/{id}` | Editar dados permitidos antes do fechamento fechado | Motorista |
| `POST` | `/trips/{id}/submit` | Enviar ou reenviar viagem completa para o fechamento mensal | Motorista |
| `GET` | `/trips/{id}/gps` | Listar coordenadas GPS da viagem | Motorista |

Partida, chegada e reenvio são ações operacionais exclusivas de usuários com perfil `motorista`. Administrador, analista e responsável pelo fechamento fora do perfil `motorista` recebem `403` nesses endpoints; administradores e analistas continuam podendo consultar a base pelos relatórios conforme permissão.

`GET /trips` deve retornar, para usuários sem permissão de fechamento, somente viagens próprias. Usuários com poder de fechamento podem receber também viagens de subordinados conforme permissão, e administradores/analistas podem consultar a base conforme perfil.

Cada item de `GET /trips` e `GET /trips/{id}` deve trazer dados suficientes para o histórico mobile e para a chegada de uma viagem em andamento:

```json
{
  "id": "uuid-da-viagem",
  "usuario_id": "uuid-do-motorista",
  "usuario_nome": "Nome do Motorista",
  "veiculo_id": "uuid-do-veiculo",
  "veiculo_placa": "ABC1234",
  "veiculo_modelo": "Onix",
  "status": "em_andamento",
  "km_inicial": 12345.6,
  "km_final": null,
  "km_rodado": null,
  "rota_utilizada": null,
  "partida_em": "2026-05-01T08:00:00Z",
  "chegada_em": null,
  "foto_hodometro_inicial": {
    "id": "uuid-da-foto-inicial",
    "viagem_id": "uuid-da-viagem",
    "tipo": "inicial",
    "mime_type": "image/jpeg",
    "tamanho_bytes": 123456,
    "criado_em": "2026-05-01T08:00:00Z",
    "download_url": "/photos/uuid-da-foto-inicial"
  },
  "foto_hodometro_final": null
}
```

Endpoints legados de aprovação individual de viagem, como `/trips/{id}/approve`, `/trips/{id}/reject`, `/trips/{id}/request-adjustment` e `/trips/{id}/approvals`, não devem ser consumidos pelo app. Quando expostos durante a transição, devem retornar `410 Gone`.

## 8. Fotos E GPS

| Método | Endpoint | Finalidade | Perfil mínimo |
|---|---|---|---|
| `POST` | `/trips/{id}/photos` | Enviar foto do hodômetro | Motorista |
| `GET` | `/trips/{id}/photos` | Listar fotos da viagem | Motorista |
| `GET` | `/photos/{id}` | Visualizar ou baixar foto | Motorista |
| `GET` | `/trips/{id}/gps` | Listar GPS de partida e chegada da viagem | Motorista |
| `GET` | `/geocoding/reverse` | Resolver endereço aproximado a partir de latitude e longitude | Motorista |

Resposta de `GET /trips/{id}/photos`:

```json
[
  {
    "id": "uuid-da-foto",
    "viagem_id": "uuid-da-viagem",
    "tipo": "inicial",
    "mime_type": "image/jpeg",
    "tamanho_bytes": 123456,
    "criado_em": "2026-05-01T08:00:00Z",
    "download_url": "/photos/uuid-da-foto"
  }
]
```

Resposta de `GET /trips/{id}/gps`:

```json
[
  {
    "id": "uuid-do-gps",
    "viagem_id": "uuid-da-viagem",
    "tipo": "partida",
    "latitude": -23.55052,
    "longitude": -46.633308,
    "precisao_metros": 12.5,
    "endereco": "Praca da Se, Sao Paulo - SP, Brasil",
    "endereco_resolvido": true,
    "endereco_exibicao": "Praca da Se, Sao Paulo - SP, Brasil",
    "capturado_em": "2026-05-01T08:00:00Z"
  }
]
```

Consulta de endereço para exibição imediata no app:

```txt
GET /geocoding/reverse?latitude=-23.55052&longitude=-46.633308
```

Resposta:

```json
{
  "endereco": "Praca da Se, Sao Paulo - SP, Brasil",
  "endereco_resolvido": true,
  "endereco_exibicao": "Praca da Se, Sao Paulo - SP, Brasil"
}
```

`endereco` pode retornar `null` quando a geocodificação reversa estiver desabilitada, indisponível, sem resposta válida ou sem endereço aproximado para a coordenada. Nesses casos, `endereco_resolvido` retorna `false` e `endereco_exibicao` retorna `"Endereco nao resolvido"` para uso em tela e exportação. O endpoint exige autenticação porque latitude e longitude são dados sensíveis.

## 9. Relatórios E Fechamento Mensal

| Método | Endpoint | Finalidade | Perfil mínimo |
|---|---|---|---|
| `GET` | `/reports/monthly` | Consultar viagens do relatório mensal | Analista ou responsável autorizado |
| `GET` | `/reports/monthly/export` | Exportar relatório mensal em PDF | Analista ou responsável autorizado |
| `GET` | `/reports/monthly/closures` | Listar fechamentos mensais por motorista no período | Analista ou responsável autorizado |
| `GET` | `/reports/monthly/closures/{motorista_id}` | Detalhar fechamento mensal de um motorista | Analista ou responsável autorizado |
| `POST` | `/reports/monthly/closures/{motorista_id}/close` | Fechar consolidado mensal do motorista | Superior com permissão de fechamento |

Responsável pelo fechamento é o usuário com `pode_aprovar = true`, normalmente coordenador ou cargo acima. Para fechar o consolidado mensal, deve ser superior imediato do motorista, exceto regra administrativa explícita. Supervisor não recebe permissão automaticamente pelo cargo.

Endpoints legados de decisão do fechamento mensal, como `/reports/monthly/closures/{motorista_id}/approve` e `/reports/monthly/closures/{motorista_id}/reject`, não devem ser consumidos pelo app e retornam `410 Gone`.

## 10. Contrato Para Partida

Para o protótipo, a partida deve ser enviada em `multipart/form-data`, garantindo que a foto obrigatória seja validada no mesmo request que cria a viagem.

Campos do formulário:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `payload` | JSON serializado | Sim | Dados da partida |
| `foto_hodometro` | Arquivo de imagem | Sim | Foto inicial do hodômetro |

Conteúdo de `payload`:

```json
{
  "veiculo_id": "uuid",
  "km_inicial": 12345.6,
  "gps": {
    "latitude": -23.55052,
    "longitude": -46.633308,
    "precisao_metros": 12.5,
    "endereco": "Praca da Se, Sao Paulo - SP, Brasil"
  }
}
```

`endereco` é opcional no payload. Se não vier informado, o backend pode tentar resolver por geocodificação reversa quando o serviço estiver habilitado. Se `foto_hodometro` não for enviado, a API deve rejeitar a partida.

## 11. Contrato Para Chegada

Para o protótipo, a chegada também deve ser enviada em `multipart/form-data`, garantindo foto final, GPS, rota e km final no mesmo request.

Campos do formulário:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `payload` | JSON serializado | Sim | Dados da chegada |
| `foto_hodometro` | Arquivo de imagem | Sim | Foto final do hodômetro |

Conteúdo de `payload`:

```json
{
  "km_final": 12410.8,
  "rota_utilizada": "Cliente A -> Cliente B -> Unidade Bello",
  "gps": {
    "latitude": -23.551,
    "longitude": -46.634,
    "precisao_metros": 10.0,
    "endereco": "Avenida Paulista, Sao Paulo - SP, Brasil"
  }
}
```

`endereco` é opcional no payload. Se não vier informado, o backend pode tentar resolver por geocodificação reversa quando o serviço estiver habilitado. Se `foto_hodometro` não for enviado, a API deve rejeitar a chegada.

## 12. Contrato Para Relatório Mensal

Consulta:

```txt
GET /reports/monthly?ano=2026&mes=5&motorista_id=uuid-opcional
GET /reports/monthly?ano=2026&mes=5&veiculo_id=uuid-do-veiculo
```

Exportação:

```txt
GET /reports/monthly/export?ano=2026&mes=5&motorista_id=uuid-opcional
GET /reports/monthly/export?ano=2026&mes=5&veiculo_id=uuid-do-veiculo
```

Parâmetros:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `ano` | Inteiro | Sim | Ano do relatório |
| `mes` | Inteiro | Sim | Mês do relatório, de `1` a `12` |
| `motorista_id` | UUID | Não | Filtra um motorista individual |
| `veiculo_id` | UUID | Não | Filtra um veículo, fixo ou alocado, para relatório administrativo por veículo; uso restrito a administrador |

Item de resposta:

```json
{
  "id": "uuid-da-viagem",
  "usuario_id": "uuid-do-motorista",
  "usuario_nome": "Nome do Motorista",
  "veiculo_id": "uuid-do-veiculo",
  "veiculo_placa": "ABC1234",
  "veiculo_modelo": "Onix",
  "partida_em": "2026-05-01T08:00:00Z",
  "chegada_em": "2026-05-01T18:00:00Z",
  "km_inicial": 12345.6,
  "km_final": 12410.8,
  "km_rodado": 65.2,
  "rota_utilizada": "Cliente A -> Cliente B",
  "foto_hodometro_inicial": {
    "id": "uuid-da-foto-inicial",
    "viagem_id": "uuid-da-viagem",
    "tipo": "inicial",
    "mime_type": "image/jpeg",
    "tamanho_bytes": 123456,
    "criado_em": "2026-05-01T08:00:00Z",
    "download_url": "/photos/uuid-da-foto-inicial"
  },
  "foto_hodometro_final": {
    "id": "uuid-da-foto-final",
    "viagem_id": "uuid-da-viagem",
    "tipo": "final",
    "mime_type": "image/jpeg",
    "tamanho_bytes": 123456,
    "criado_em": "2026-05-01T18:00:00Z",
    "download_url": "/photos/uuid-da-foto-final"
  },
  "gps_partida": {
    "id": "uuid-do-gps-partida",
    "viagem_id": "uuid-da-viagem",
    "tipo": "partida",
    "latitude": -23.55052,
    "longitude": -46.633308,
    "precisao_metros": 12.5,
    "endereco": "Praca da Se, Sao Paulo - SP, Brasil",
    "endereco_resolvido": true,
    "endereco_exibicao": "Praca da Se, Sao Paulo - SP, Brasil",
    "capturado_em": "2026-05-01T08:00:00Z"
  },
  "gps_chegada": {
    "id": "uuid-do-gps-chegada",
    "viagem_id": "uuid-da-viagem",
    "tipo": "chegada",
    "latitude": -23.551,
    "longitude": -46.634,
    "precisao_metros": 10.0,
    "endereco": "Avenida Paulista, Sao Paulo - SP, Brasil",
    "endereco_resolvido": true,
    "endereco_exibicao": "Avenida Paulista, Sao Paulo - SP, Brasil",
    "capturado_em": "2026-05-01T18:00:00Z"
  },
  "status": "concluida",
  "fechamento_mensal_id": "uuid-do-fechamento",
  "status_fechamento": "fechado",
  "superior_id": "uuid-do-superior",
  "avaliado_em": "2026-05-31T18:00:00Z",
  "observacao_fechamento": null
}
```

O item do relatório mensal deve entregar as evidências diretamente no JSON. Fotos devem trazer metadados e `download_url`; GPS deve trazer coordenadas, `endereco`, `endereco_resolvido` e `endereco_exibicao` de partida e chegada. Na exportação mensal em PDF, os locais de saída e chegada usam o endereço resolvido quando disponível; quando indisponível, permanecem sem endereço textual e as coordenadas continuam como evidência.

Quando `veiculo_id` é informado, apenas administradores podem consultar/exportar. A exportação em PDF passa a focar no veículo selecionado e a primeira coluna da tabela identifica o vendedor responsável por cada itinerário do dia. As fotos do hodômetro permanecem incluídas quando os arquivos estiverem disponíveis.

## 13. Contrato Para Fechamento Mensal

Detalhe:

```txt
GET /reports/monthly/closures/{motorista_id}?ano=2026&mes=5
```

Fechamento:

```txt
POST /reports/monthly/closures/{motorista_id}/close?ano=2026&mes=5
```

Corpo:

```json
{
  "observacao": "Consolidado conferido."
}
```

Resposta:

```json
{
  "id": "uuid-do-fechamento",
  "motorista_id": "uuid-do-motorista",
  "motorista_nome": "Nome do Motorista",
  "ano": 2026,
  "mes": 5,
  "status": "fechado",
  "superior_id": "uuid-do-superior",
  "avaliado_em": "2026-05-31T18:00:00Z",
  "observacao": "Consolidado conferido.",
  "total_viagens": 12,
  "km_total": 840.5
}
```

Legado:

```txt
POST /reports/monthly/closures/{motorista_id}/approve?ano=2026&mes=5
POST /reports/monthly/closures/{motorista_id}/reject?ano=2026&mes=5
```

Essas rotas retornam `410 Gone` no fluxo vigente.

## 14. Códigos De Resposta

| Código | Uso |
|---|---|
| `200` | Consulta ou atualização realizada |
| `201` | Registro criado |
| `400` | Dados inválidos |
| `401` | Usuário não autenticado |
| `403` | Usuário sem permissão |
| `404` | Registro não encontrado |
| `409` | Conflito de regra de negócio |
| `410` | Endpoint legado indisponível no fluxo vigente |
| `422` | Erro de validação |
| `500` | Erro interno inesperado |
