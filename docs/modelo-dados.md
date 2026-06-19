# Modelo De Dados Inicial

## 1. Visão Geral

O modelo deve garantir rastreabilidade da viagem, vínculo com usuário e veículo, fotos obrigatórias, GPS de partida e chegada, endereço aproximado quando disponível, status da viagem e fechamento mensal por motorista individual.

## 2. Entidades Principais

| Entidade | Finalidade |
|---|---|
| `Usuario` | Representa quem acessa o sistema |
| `Veiculo` | Representa carro próprio, alugado ou disponível |
| `Viagem` | Registro principal do deslocamento |
| `FotoHodometro` | Foto vinculada à partida ou chegada |
| `LocalizacaoGPS` | Coordenada capturada na partida ou chegada |
| `FechamentoMensal` | Consolidação mensal de viagens de um motorista, aberta ou fechada pelo responsável |
| `RelatorioMensal` | Consulta ou visão consolidada para análise e exportação, incluindo evidências diretas de fotos e GPS por viagem |

`Aprovacao` por viagem não faz parte do fluxo vigente e não deve ser usada por novos endpoints. O fechamento mensal é a entidade de controle do processo atual.

## 3. Usuario

| Campo | Tipo sugerido | Obrigatório | Observação |
|---|---|---|---|
| `id` | UUID | Sim | Identificador único |
| `nome` | Texto | Sim | Nome do usuário |
| `email` | Texto | Sim | Deve ser único |
| `senha_hash` | Texto | Sim | Nunca salvar senha em texto puro |
| `perfil` | Enum | Sim | `motorista`, `supervisor`, `analista`, `admin` |
| `cargo` | Texto | Não | Cargo vindo da planilha de usuários |
| `superior_id` | UUID | Não | Superior imediato responsável por acompanhar e fechar relatórios quando tiver permissão |
| `pode_aprovar` | Booleano | Sim | Flag técnica que concede permissão de fechamento mensal para coordenador e cargos acima |
| `ativo` | Booleano | Sim | Permite bloquear acesso |
| `criado_em` | Data/hora | Sim | Auditoria |
| `atualizado_em` | Data/hora | Sim | Auditoria |

Observação: todos os usuários importados da planilha operacional devem poder registrar viagens. O cargo não substitui o perfil operacional. Supervisores não recebem permissão de fechamento automaticamente; essa permissão fica restrita a coordenador e níveis superiores.

## 4. Veiculo

| Campo | Tipo sugerido | Obrigatório | Observação |
|---|---|---|---|
| `id` | UUID | Sim | Identificador único |
| `placa` | Texto | Sim | Deve ser única |
| `modelo` | Texto | Sim | Exemplo: Onix, Saveiro |
| `tipo` | Enum | Sim | `proprio`, `alugado`, `empresa` |
| `tipo_disponibilidade` | Enum | Sim | `fixo` ou `alocado` |
| `usuario_responsavel_id` | UUID | Depende | Obrigatório quando `tipo_disponibilidade = fixo` |
| `unidade` | Texto | Não | Unidade operacional da planilha |
| `categoria` | Texto | Não | Categoria ou classificação operacional |
| `ativo` | Booleano | Sim | Controla disponibilidade |
| `criado_em` | Data/hora | Sim | Auditoria |
| `atualizado_em` | Data/hora | Sim | Auditoria |

Regras de disponibilidade:

- `proprio` na planilha: veículo vinculado a um usuário específico, salvo como `tipo = proprio` e `tipo_disponibilidade = fixo`.
- `empresa` na planilha: veículo compartilhável, salvo como `tipo = empresa` e `tipo_disponibilidade = alocado`.
- Mesmo quando o veículo é compartilhável, `usuario_responsavel_id` pode indicar o responsável usual para priorizar a seleção.
- Veículo `fixo` deve ter `usuario_responsavel_id`.
- Veículo inativo não deve aparecer como opção para iniciar viagem.

## 5. Viagem

| Campo | Tipo sugerido | Obrigatório | Observação |
|---|---|---|---|
| `id` | UUID | Sim | Identificador único |
| `usuario_id` | UUID | Sim | Usuário que registrou |
| `veiculo_id` | UUID | Sim | Veículo selecionado |
| `status` | Enum | Sim | Ver `docs/regras-negocio.md` |
| `km_inicial` | Decimal | Sim | Informado na partida |
| `km_final` | Decimal | Não | Obrigatório para chegada |
| `km_rodado` | Decimal | Não | Calculado como `km_final - km_inicial` |
| `rota_utilizada` | Texto | Não | Obrigatório antes de entrar no fechamento mensal |
| `partida_em` | Data/hora | Sim | Definido pelo backend |
| `chegada_em` | Data/hora | Não | Definido pelo backend |
| `criado_em` | Data/hora | Sim | Auditoria |
| `atualizado_em` | Data/hora | Sim | Auditoria |

## 6. FotoHodometro

| Campo | Tipo sugerido | Obrigatório | Observação |
|---|---|---|---|
| `id` | UUID | Sim | Identificador único |
| `viagem_id` | UUID | Sim | Viagem vinculada |
| `tipo` | Enum | Sim | `inicial` ou `final` |
| `arquivo_path` | Texto | Sim | Caminho local no protótipo |
| `mime_type` | Texto | Sim | Exemplo: `image/jpeg` |
| `tamanho_bytes` | Inteiro | Sim | Ajuda a controlar limite |
| `criado_em` | Data/hora | Sim | Auditoria |

## 7. LocalizacaoGPS

| Campo | Tipo sugerido | Obrigatório | Observação |
|---|---|---|---|
| `id` | UUID | Sim | Identificador único |
| `viagem_id` | UUID | Sim | Viagem vinculada |
| `tipo` | Enum | Sim | `partida` ou `chegada` |
| `latitude` | Decimal | Sim | Coordenada capturada |
| `longitude` | Decimal | Sim | Coordenada capturada |
| `precisao_metros` | Decimal | Não | Quando disponível |
| `endereco` | Texto | Não | Endereço aproximado resolvido a partir das coordenadas ou recebido no payload; permanece nulo quando não resolvido |
| `capturado_em` | Data/hora | Sim | Horário da captura |

## 8. FechamentoMensal

| Campo | Tipo sugerido | Obrigatório | Observação |
|---|---|---|---|
| `id` | UUID | Sim | Identificador único |
| `motorista_id` | UUID | Sim | Motorista dono do consolidado mensal |
| `superior_id` | UUID | Depende | Responsável que fechou o consolidado; obrigatório quando `status = fechado` |
| `ano` | Inteiro | Sim | Ano do fechamento |
| `mes` | Inteiro | Sim | Mês do fechamento, de `1` a `12` |
| `status` | Enum | Sim | `aberto`, `fechado` |
| `observacao` | Texto | Não | Observação opcional do fechamento |
| `avaliado_em` | Data/hora | Depende | Obrigatória quando `status = fechado` |
| `criado_em` | Data/hora | Sim | Auditoria |
| `atualizado_em` | Data/hora | Sim | Auditoria |

Regras técnicas:

- Deve existir no máximo um fechamento mensal por `motorista_id`, `ano` e `mes`.
- O fechamento mensal não substitui as viagens; ele aponta o estado consolidado do mês.
- O fechamento mensal `fechado` não altera o status das viagens; elas permanecem `concluida`.
- A constraint `ck_fechamentos_mensais_fechamento_completo` exige `superior_id` e `avaliado_em` quando `status = fechado`.

## 9. RelatorioMensal

`RelatorioMensal` é uma visão de consulta e exportação, não uma tabela própria no protótipo. Cada item deve consolidar dados de `Viagem`, `Usuario`, `Veiculo`, `FechamentoMensal`, `FotoHodometro` e `LocalizacaoGPS`.

Campos obrigatórios de evidência no item:

| Campo | Origem | Observação |
|---|---|---|
| `foto_hodometro_inicial` | `FotoHodometro` com `tipo = inicial` | Deve trazer identificador, metadados e caminho de download |
| `foto_hodometro_final` | `FotoHodometro` com `tipo = final` | Deve trazer identificador, metadados e caminho de download |
| `gps_partida` | `LocalizacaoGPS` com `tipo = partida` | Deve trazer latitude, longitude, precisão, endereço quando disponível, status de resolução, texto de exibição e captura |
| `gps_chegada` | `LocalizacaoGPS` com `tipo = chegada` | Deve trazer latitude, longitude, precisão, endereço quando disponível, status de resolução, texto de exibição e captura |

## 10. Relacionamentos

```txt
Usuario 1:N Viagem
Usuario 1:N Usuario (superior e subordinados)
Usuario 1:N Veiculo (responsável usual ou veículo fixo)
Usuario 1:N FechamentoMensal (motorista)
Usuario 1:N FechamentoMensal (responsável pelo fechamento)
Veiculo 1:N Viagem
Viagem 1:N FotoHodometro
Viagem 1:N LocalizacaoGPS
```

## 11. Regras Técnicas Do Modelo

- Usar UUID como identificador principal.
- Usar campos `criado_em` e `atualizado_em` nas tabelas principais.
- Nunca salvar senha em texto puro.
- Guardar fotos localmente no protótipo e manter caminho no banco.
- Guardar endereço do GPS como dado complementar e aproximado, sem substituir latitude e longitude; texto como `"Endereco nao resolvido"` deve ser gerado para exibição/exportação, não salvo como endereço real.
- Calcular `km_rodado` a partir de `km_final - km_inicial`.
- Validar status da viagem no backend.
- Validar status do fechamento mensal no backend.
- Validar que veículo fixo tenha usuário responsável.
- Validar que fechamento mensal seja executado por usuário com `pode_aprovar = true` e vínculo de superior imediato, exceto regras administrativas explícitas.
