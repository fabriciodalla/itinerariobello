# Telas E Fluxos

## 1. Princípios De Interface

- Interface mobile simples, objetiva e rápida.
- Fluxo principal deve exigir poucos toques.
- Campos obrigatórios devem ser claros antes do envio.
- Mensagens de erro devem explicar exatamente o que falta.
- O usuário não deve conseguir salvar registro incompleto.
- A tela de fechamento mensal deve funcionar por motorista individual.
- Visual deve parecer aplicativo operacional mobile, com botões de toque amplos, navegação inferior fixa, ícones funcionais e indicadores claros de foto, GPS e status.
- A tela `Em rota` é a primeira tela após login para todos os usuários autenticados.
- As abas `Viagem` e `Historico` aparecem somente para usuários com perfil `motorista`; administradores não veem o fluxo operacional de viagem.
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
- Link de solicitação de cadastro.

### Critérios De Aceite

- Bloqueia login sem e-mail ou senha.
- Exibe erro quando credenciais forem inválidas.
- Mantém sessão segura quando o login for válido.
- Oferece caminho para recuperação de acesso.
- Oferece caminho para solicitação pública de cadastro.

## 3. Tela Recuperação De Senha

### Objetivo

Permitir que usuário receba link por e-mail para redefinir senha.

### Elementos

- Campo de e-mail.
- Botão de enviar link.
- Formulário de nova senha quando a tela for aberta com `reset_token`.

### Critérios De Aceite

- Bloqueia envio sem e-mail.
- Resposta pública não informa se o e-mail existe.
- Permite definir nova senha com token válido.
- Exibe erro quando token estiver inválido ou expirado.

## 4. Tela Solicitar Cadastro

### Objetivo

Registrar solicitação pública de novo usuário para análise do administrador.

### Elementos

- Nome.
- E-mail.
- Cargo.
- Superior informado.
- Placa, modelo e marca do veículo.
- Observação opcional.
- Botão de enviar solicitação.

### Critérios De Aceite

- Bloqueia envio sem dados obrigatórios.
- Cria solicitação com status `pendente`.
- Não cria usuário ativo automaticamente.
- Permite voltar ao login.

## 4.1 Tela Inicial Em Rota

### Objetivo

Mostrar os veículos com rota em andamento.

### Elementos

- Total de veículos em rota.
- Lista de veículos em rota.
- Placa e modelo do veículo.
- Status `Em rota`.
- Motorista que está executando a rota.
- Data e hora de partida.

### Critérios De Aceite

- É a primeira tela exibida após login.
- Lista somente viagens com status `em_andamento`.
- Não exibe GPS, foto ou endereço.
- Exige usuário autenticado.

## 5. Tela Selecionar Carro

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

## 6. Tela Partida

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

## 7. Tela Viagem Em Andamento

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

## 8. Tela Chegada

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

## 9. Tela Conclusão Da Viagem

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

## 10. Tela Editar

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

## 11. Tela Fechamento Mensal

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

## 12. Tela Cadastros

### Objetivo

Permitir que administrador aprove ou reprove solicitações públicas de cadastro.

### Elementos

- Lista de solicitações pendentes.
- Dados do solicitante, cargo, superior informado e veículo.
- Campo de senha temporária.
- Seletores de perfil, superior técnico e tipo do veículo.
- Controle de permissão de fechamento.
- Campo de motivo para reprovação.
- Botões de aprovar e reprovar.

### Critérios De Aceite

- Disponível somente para administrador.
- Aprovação cria usuário ativo e veículo novo ou vinculado.
- Reprovação exige motivo.
- Solicitação processada não pode ser processada novamente.

## 13. Fluxo Principal Da Viagem

Disponível somente para usuários com perfil `motorista`.

```txt
Login
  -> Em rota
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

## 14. Fluxos De Acesso

```txt
Login
  -> Esqueci minha senha
  -> Receber link por e-mail
  -> Redefinir senha
  -> Login

Login
  -> Solicitar cadastro
  -> Solicitação pendente
  -> Admin aprova ou reprova
  -> Login com senha temporária quando aprovado
```
