# Regras De Negócio

## 1. Status Da Viagem

| Status | Significado |
|---|---|
| `em_andamento` | Partida registrada e chegada pendente |
| `concluida` | Viagem completa e disponível para relatório/fechamento mensal |

## 2. Status Do Fechamento Mensal

| Status | Significado |
|---|---|
| `aberto` | Consolidado mensal ainda não fechado |
| `fechado` | Consolidado mensal conferido e fechado pelo responsável |

O fechamento mensal é sempre por motorista individual, considerando as viagens do motorista no mês informado. Não há aprovação individual de viagem nem botões de aprovar/reprovar no app.

## 3. Regras Obrigatórias

| Código | Regra | Onde validar |
|---|---|---|
| RN-001 | Toda viagem deve estar vinculada a um usuário autenticado | Backend |
| RN-002 | Toda viagem deve estar vinculada a um veículo | App e backend |
| RN-003 | Km inicial é obrigatório na partida | App e backend |
| RN-004 | Foto do hodômetro inicial é obrigatória | App e backend |
| RN-005 | GPS inicial é obrigatório | App e backend |
| RN-006 | Data e hora da partida devem ser registradas automaticamente | Backend |
| RN-007 | Km final é obrigatório na chegada | App e backend |
| RN-008 | Foto do hodômetro final é obrigatória | App e backend |
| RN-009 | GPS final é obrigatório | App e backend |
| RN-010 | Data e hora da chegada devem ser registradas automaticamente | Backend |
| RN-011 | Km final não pode ser menor que km inicial | Backend |
| RN-012 | Rota utilizada deve ser informada antes de a viagem entrar no fechamento mensal | App e backend |
| RN-013 | Viagem em fechamento mensal fechado não pode ser editada | Backend |
| RN-014 | Observação do fechamento mensal é opcional e deve ser registrada quando informada | Backend |
| RN-015 | Fechamento mensal fechado deve registrar responsável, data, hora, status e observação quando informada | Backend |
| RN-016 | Na partida, o veículo selecionado deve ser próprio do usuário ou veículo de empresa ativo | Backend |
| RN-017 | Veículo próprio deve estar associado a um usuário responsável | Backend |
| RN-018 | Veículo com itinerário iniciado no dia deve ficar bloqueado para nova partida | Backend |
| RN-019 | Usuários da planilha operacional com perfil `motorista` devem poder registrar viagens | Backend |
| RN-020 | Fechamento mensal final deve ser feito pelo superior imediato com permissão de fechamento, limitado a coordenador e cargos acima | Backend |
| RN-021 | O fechamento mensal deve ser feito por motorista individual, não por equipe inteira | Backend |
| RN-022 | Endpoints legados de aprovação/reprovação, como `/trips/{id}/approve` e `/reports/monthly/closures/{id}/approve`, não devem ser usados pelo fluxo vigente | Backend e app |
| RN-023 | Endereço de partida e chegada é complemento do GPS e deve ser salvo quando resolvido, sem substituir latitude e longitude | Backend e app |
| RN-024 | Token de recuperação de senha deve expirar e ser usado uma única vez | Backend |
| RN-025 | Solicitação pública de cadastro não cria usuário ativo sem aprovação de administrador | Backend |
| RN-026 | Somente usuários com perfil `motorista` podem iniciar, finalizar ou reenviar viagem; administrador, analista e responsável pelo fechamento não executam o fluxo operacional de viagem | Backend e app |
| RN-027 | A tela inicial autenticada deve listar veículos em rota a partir de viagens com status `em_andamento`, exibindo veículo, status em rota e motorista responsável pela execução | Backend e app |

## 4. Fluxo De Validação Da Partida

1. Motorista autenticado seleciona veículo próprio associado a ele ou veículo de empresa ativo.
2. Usuário informa km inicial.
3. Usuário envia foto do hodômetro inicial.
4. App captura latitude e longitude.
5. App ou backend resolve endereço aproximado quando houver serviço disponível.
6. Backend valida dados obrigatórios.
7. Backend valida se o veículo selecionado é permitido para o usuário e se não há itinerário iniciado no dia para o veículo.
8. Backend cria viagem com status `em_andamento`.

## 5. Fluxo De Validação Da Chegada

1. Motorista autenticado seleciona viagem `em_andamento`.
2. Usuário informa km final.
3. Usuário envia foto do hodômetro final.
4. App captura latitude e longitude.
5. App ou backend resolve endereço aproximado quando houver serviço disponível.
6. Usuário informa rota utilizada.
7. Backend valida km final maior ou igual ao km inicial.
8. Backend altera status para `concluida`, indicando que a viagem está pronta para o fechamento mensal.

## 6. Fluxo De Fechamento Mensal

1. Superior autorizado acessa o fechamento mensal de um motorista individual.
2. Sistema lista todas as viagens do motorista no mês, com km, fotos, GPS, endereço, rotas, veículo e status.
3. Superior confere o consolidado mensal.
4. Superior fecha o consolidado mensal quando a conferência estiver encerrada.
5. Backend registra responsável, data/hora, status `fechado` e observação quando informada.
6. As viagens do período permanecem com status `concluida`.
7. Correções só são permitidas enquanto o fechamento mensal estiver `aberto`.

## 6.1 Fluxo De Consulta De Veículos Em Rota

1. Usuário autenticado acessa a tela inicial `Em rota`.
2. Backend lista viagens com status `em_andamento`.
3. App exibe placa, modelo, status `Em rota`, motorista e data/hora de partida.
4. A tela não exibe latitude, longitude, fotos ou endereço; esses dados continuam restritos aos fluxos de viagem, histórico, fechamento e relatório conforme permissão.

## 7. Campos Editáveis Antes Do Fechamento Mensal Fechado

| Campo | Motorista pode editar? | Observação |
|---|---|---|
| Veículo | Sim, antes do fechamento fechado | Deve manter histórico se já enviado |
| Km inicial | Sim, antes do fechamento fechado | Pode exigir justificativa |
| Km final | Sim, antes do fechamento fechado | Nunca pode ser menor que km inicial |
| Rota utilizada | Sim, antes do fechamento fechado | Campo principal para ajustes |
| Foto inicial | Sim, antes do fechamento fechado | Deve manter rastreabilidade |
| Foto final | Sim, antes do fechamento fechado | Deve manter rastreabilidade |
| GPS inicial | Não manualmente | Latitude e longitude devem vir da captura do dispositivo; endereço pode ser resolvido automaticamente |
| GPS final | Não manualmente | Latitude e longitude devem vir da captura do dispositivo; endereço pode ser resolvido automaticamente |

## 8. Dados Para Relatório Mensal

O relatório mensal deve conter:

- usuário;
- veículo;
- data e hora de partida;
- km inicial;
- foto do hodômetro inicial;
- GPS inicial;
- endereço inicial, quando disponível;
- data e hora de chegada;
- km final;
- foto do hodômetro final;
- GPS final;
- endereço final, quando disponível;
- rota utilizada;
- km rodado;
- status da viagem;
- status do fechamento mensal;
- superior responsável pelo fechamento;
- data e hora do fechamento;
- observação do fechamento, quando informada.

Cada item retornado pela consulta do relatório mensal deve entregar diretamente as evidências da viagem, sem exigir chamadas adicionais para montar o fechamento:

- foto do hodômetro inicial com identificador e caminho de download;
- foto do hodômetro final com identificador e caminho de download;
- GPS de partida com latitude, longitude, precisão, endereço quando disponível e data/hora da captura;
- GPS de chegada com latitude, longitude, precisão, endereço quando disponível e data/hora da captura.

O frontend também deve ter endpoint específico para consultar o GPS de uma viagem quando precisar abrir o detalhe individual.

Latitude e longitude continuam sendo a evidência obrigatória de localização. O endereço é aproximado, depende de geocodificação reversa e não deve bloquear partida, chegada ou fechamento quando não puder ser resolvido. Quando o provedor retornar número do endereço, o sistema deve exibi-lo junto ao logradouro; quando não retornar, o sistema não deve inventar número aproximado. Quando o endereço não for resolvido, a API deve manter `endereco = null` e entregar um texto de exibição como `"Endereco nao resolvido"` junto do status `endereco_resolvido = false`.

Administradores podem consultar e exportar o relatório mensal filtrando por veículo, seja fixo ou alocado. Nessa visão, o fechamento mensal continua sendo por motorista, mas a consulta lista todos os itinerários do veículo no mês e destaca o vendedor que executou cada itinerário.

## 9. Fluxo De Recuperação De Senha

1. Usuário informa e-mail na tela de login.
2. Backend responde sempre de forma genérica para evitar enumeração de usuários.
3. Se o e-mail pertencer a usuário ativo, backend invalida tokens anteriores em aberto, cria token temporário, salva apenas `token_hash` e envia link por e-mail.
4. Usuário abre o link e informa nova senha.
5. Backend valida token, expiração, uso único e usuário ativo.
6. Senha é salva somente como hash seguro e o token fica marcado como usado.

## 10. Fluxo De Solicitação De Cadastro

1. Interessado acessa `Solicitar cadastro` na tela de login.
2. Solicitação registra nome, e-mail, cargo, superior informado, placa, modelo e marca do veículo.
3. Solicitação fica com status `pendente`.
4. Administrador acessa a área de cadastros, confere os dados, define perfil, superior, permissão de fechamento e senha temporária.
5. Ao aprovar, o backend cria usuário ativo, cria ou vincula veículo e marca a solicitação como `aprovada`.
6. Ao reprovar, o backend registra motivo e marca a solicitação como `rejeitada`.
7. Usuário pendente ou reprovado não consegue autenticar até existir usuário ativo aprovado.
