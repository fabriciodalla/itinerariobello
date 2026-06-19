# Telas E Fluxos

## 1. Princípios De Interface

- Interface mobile simples, objetiva e rápida.
- Fluxo principal deve exigir poucos toques.
- Campos obrigatórios devem ser claros antes do envio.
- Mensagens de erro devem explicar exatamente o que falta.
- O usuário não deve conseguir salvar registro incompleto.
- A tela de fechamento mensal deve funcionar por motorista individual.
- Visual deve parecer aplicativo operacional mobile, com botões de toque amplos, navegação inferior fixa, ícones funcionais e indicadores claros de foto, GPS e status.
- Cores do frontend devem ser padronizadas por tokens: azul royal para ações principais e marca, azul claro/ciano para fundos e bordas de destaque, verde apenas para sucesso/evidência capturada, amarelo para pendências e azul para informação/consulta.
- Evitar aparência genérica de template: sem cards decorativos excessivos, textos promocionais, gradientes chamativos ou ilustrações sem função no fluxo.

## 2. Tela Login

### Objetivo

Autenticar o usuário com e-mail e senha.

### Elementos

- Campo de e-mail.
- Campo de senha.
- Botão de entrar.
- Link de recuperação de senha.

### Critérios De Aceite

- Bloqueia login sem e-mail ou senha.
- Exibe erro quando credenciais forem inválidas.
- Mantém sessão segura quando o login for válido.
- Oferece caminho para recuperação de acesso.

## 3. Tela Selecionar Carro

### Objetivo

Permitir que o usuário escolha o veículo antes de iniciar a viagem.

### Elementos

- Lista de veículos próprios vinculados ao usuário.
- Lista de veículos de empresa disponíveis.
- Dados mínimos do veículo: placa, modelo, tipo e disponibilidade.
- Botão para confirmar seleção.

### Critérios De Aceite

- Não permite iniciar partida sem veículo.
- Mostra veículo próprio do usuário e veículos de empresa ativos sem itinerário iniciado no dia.
- Prioriza o veículo de empresa do responsável usual, quando houver.
- Salva o veículo selecionado na viagem.

## 4. Tela Partida

### Objetivo

Registrar início da viagem com km inicial, foto do hodômetro e GPS.

### Elementos

- Campo de km inicial.
- Botão principal para abrir a câmera nativa do celular.
- Botão secundário para anexar foto da galeria.
- Captura automática de GPS.
- Exibição do endereço aproximado quando resolvido.
- Indicador de resolução de endereço após capturar o GPS, exibindo `Endereco nao resolvido` quando a geocodificação não retornar endereço.
- Indicador de foto anexada.
- Indicador de GPS capturado.
- Botão de iniciar viagem.

### Critérios De Aceite

- Bloqueia envio sem km inicial.
- Bloqueia envio sem foto do hodômetro.
- Bloqueia envio sem GPS.
- Mantém latitude e longitude como dados obrigatórios; endereço não bloqueia a partida quando indisponível.
- Registra data e hora automaticamente.
- Cria viagem com status `em_andamento`.

## 5. Tela Viagem Em Andamento

### Objetivo

Mostrar que a partida foi registrada e permitir que o usuário escolha entre sair do aplicativo ou registrar a chegada.

### Elementos

- Resumo do veículo, km inicial e data/hora da partida.
- Botão para fazer chegada.
- Botão para sair do aplicativo.

### Critérios De Aceite

- Aparece após a partida ser registrada com sucesso.
- Não abre a chegada automaticamente sem ação do usuário.
- Permite retomar a chegada enquanto houver viagem `em_andamento` do usuário autenticado.
- Mostra placa e modelo do veículo usado na viagem, não apenas o identificador interno.

## 6. Tela Chegada

### Objetivo

Registrar fim da viagem com km final, foto do hodômetro, GPS e rota utilizada.

### Elementos

- Campo de km final.
- Botão principal para abrir a câmera nativa do celular.
- Botão secundário para anexar foto da galeria.
- Captura automática de GPS.
- Exibição do endereço aproximado quando resolvido.
- Indicador de resolução de endereço após capturar o GPS, exibindo `Endereco nao resolvido` quando a geocodificação não retornar endereço.
- Campo de rota utilizada.
- Resumo do km inicial e veículo.
- Botão de finalizar viagem.

### Critérios De Aceite

- Bloqueia envio sem km final.
- Bloqueia envio sem foto do hodômetro.
- Bloqueia envio sem GPS.
- Mantém latitude e longitude como dados obrigatórios; endereço não bloqueia a chegada quando indisponível.
- Bloqueia envio se km final for menor que km inicial.
- Bloqueia envio sem rota utilizada.
- Altera status para `concluida`, indicando viagem pronta para fechamento mensal.

## 7. Tela Conclusão Da Viagem

### Objetivo

Confirmar para o usuário que o itinerário foi registrado e permitir sair do aplicativo ao fim do trabalho.

### Elementos

- Mensagem de itinerário registrado.
- Informação de que a viagem ficou pronta para fechamento mensal.
- Botão de sair do aplicativo.
- Botão opcional para registrar outra viagem.

### Critérios De Aceite

- Aparece somente após a chegada ser registrada com sucesso.
- Não substitui validações obrigatórias de km, foto, GPS e rota.
- Permite encerrar a sessão pelo fluxo principal, além do botão de sair no topo do app.

## 8. Tela Editar

### Objetivo

Permitir correções antes do fechamento mensal fechado.

### Elementos

- Dados da viagem.
- Campos editáveis permitidos.
- Botão de salvar alterações.
- Botão de reenviar para o fechamento mensal.

### Critérios De Aceite

- Permite edição apenas enquanto o fechamento mensal estiver `aberto`.
- Não permite editar viagem em fechamento mensal `fechado`.
- Mantém validações de foto, GPS e km.
- Registra data e usuário da alteração.

## 9. Tela Fechamento Mensal

### Objetivo

Permitir que o superior consulte o consolidado mensal de um motorista individual.

### Elementos

- Filtros por mês, motorista, veículo e status.
- Lista de motoristas subordinados com status do fechamento no mês.
- Resumo do motorista selecionado com total de viagens no período e status `aberto` ou `fechado`.
- Lista de todas as viagens do motorista no mês.
- Detalhes de cada viagem: km, fotos, GPS, endereço resolvido ou indicador `Endereco nao resolvido`, rota, veículo, data e status.
- Evidências de cada viagem disponíveis diretamente no item do relatório: foto inicial, foto final, GPS e endereço de partida e GPS e endereço de chegada.
- Exportação para relatório, quando permitido.

### Critérios De Aceite

- Responsável autorizado vê apenas fechamentos de motoristas subordinados.
- Analista vê dados consolidados conforme permissão.
- Tela não oferece ação de aprovação individual por viagem.
- Tela não oferece botões de aprovar ou reprovar fechamento mensal.
- Fechamento mensal `fechado` registra responsável, data/hora, status e observação quando informada.
- O fechamento mensal é feito por motorista individual, não por equipe inteira.

## 10. Fluxo Principal Da Viagem

```txt
Login
  -> Selecionar carro
  -> Partida
  -> Viagem em andamento
  -> Fazer chegada ou sair do aplicativo
  -> Chegada
  -> Conclusão da viagem / sair do aplicativo
  -> Viagem pronta para fechamento mensal
  -> Fechamento mensal por motorista
  -> Consolidado mensal aberto ou fechado
  -> Relatório mensal
```
