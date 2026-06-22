# Requisitos Do Sistema

## 1. Visão Geral

O sistema CONTROLE ITINERÁRIO COMERCIAL BELLO deve digitalizar o controle de quilômetros rodados, substituindo planilhas manuais por registros móveis com foto do hodômetro, localização GPS, endereço aproximado, validação e fechamento mensal aberto ou fechado pelo responsável.

O protótipo deve funcionar em servidor acessível pela internet para testes reais com usuários externos à rede local.

## 2. Perfis E Permissões

| Perfil | Permissões |
|---|---|
| Motorista/Coordenador operacional | Fazer login, selecionar veículo, registrar partida, registrar chegada, editar viagem antes do fechamento fechado e visualizar próprias viagens |
| Responsável pelo fechamento | Visualizar viagens e fechamentos mensais de motoristas subordinados, fechar o consolidado mensal individual e consultar relatórios da equipe. Deve ser coordenador ou cargo acima |
| Analista | Consultar dados consolidados, gerar relatórios mensais e exportar informações |
| Administrador | Cadastrar usuários, veículos, vínculos, perfis, permissões e analisar solicitações de cadastro, sem executar o fluxo operacional de viagem |

O fluxo operacional de viagem, incluindo seleção de veículo, partida, chegada e histórico próprio, é exclusivo de usuários com perfil técnico `motorista`. Administradores não registram viagens; acessam cadastros, usuários e consultas/relatórios conforme permissão.

Todos os usuários importados da planilha operacional com perfil `motorista` devem poder registrar viagens. A permissão de fechamento não é dada automaticamente a supervisores; ela é definida pela flag técnica `pode_aprovar`, começando em coordenador e níveis superiores.

## 3. Requisitos Funcionais

| Código | Requisito | Critério de aceite |
|---|---|---|
| RF-001 | O usuário deve fazer login com e-mail e senha | Login válido gera sessão autenticada |
| RF-002 | O usuário deve recuperar ou alterar senha esquecida | Usuário recebe link por e-mail, usa token temporário e define nova senha |
| RF-003 | O app deve manter sessão segura no celular | Usuário não precisa fazer login a cada abertura enquanto a sessão for válida |
| RF-004 | O usuário deve selecionar um veículo antes da partida | Sistema permite veículo próprio do usuário ou veículo de empresa ativo, bloqueia veículo já usado em itinerário iniciado no dia e não permite iniciar viagem sem veículo |
| RF-005 | O usuário deve registrar km inicial | Sistema salva km inicial com data e hora |
| RF-006 | O usuário deve anexar foto do hodômetro na partida | Sistema bloqueia partida sem foto |
| RF-007 | O sistema deve capturar GPS na partida | Sistema bloqueia partida sem latitude e longitude e registra endereço aproximado quando disponível |
| RF-008 | O usuário deve registrar km final | Sistema salva km final com data e hora |
| RF-009 | O usuário deve anexar foto do hodômetro na chegada | Sistema bloqueia chegada sem foto |
| RF-010 | O sistema deve capturar GPS na chegada | Sistema bloqueia chegada sem latitude e longitude e registra endereço aproximado quando disponível |
| RF-011 | O usuário deve informar rota utilizada | Sistema permite editar rota antes do fechamento mensal fechado |
| RF-012 | O sistema deve validar km final maior ou igual ao km inicial | Sistema rejeita encerramento inválido |
| RF-013 | O usuário deve visualizar histórico de viagens | Lista mostra somente viagens próprias para usuários sem permissão de fechamento, com status, veículo, datas, km e opção de visualizar fotos do hodômetro |
| RF-014 | O responsável autorizado deve fechar o fechamento mensal de um motorista individual | Ação registra responsável, data/hora, status e observação quando informada |
| RF-015 | O sistema deve permitir correção antes do fechamento mensal fechado | Viagens podem ser corrigidas enquanto o consolidado mensal estiver aberto |
| RF-016 | O sistema deve gerar relatório mensal | Relatório contém usuário, veículo, datas, km, fotos, GPS, endereço, rota, status da viagem e status do fechamento; cada item deve trazer diretamente foto inicial/final e GPS com endereço de partida/chegada |
| RF-017 | O sistema deve exportar relatório | Exportação deve gerar arquivo estruturado para análise mensal |
| RF-018 | O sistema não deve usar aprovação individual de viagem | App não deve consumir `/trips/{id}/approve`; controle mensal ocorre no fechamento aberto/fechado |
| RF-019 | O usuário externo deve solicitar cadastro pelo login | Solicitação pública registra dados pessoais, cargo, superior e veículo; somente administrador aprova ou reprova antes de criar usuário ativo |
| RF-020 | O usuário deve visualizar veículos em rota na tela inicial | Tela inicial autenticada lista viagens em andamento com veículo, status em rota, motorista responsável e horário de partida |

## 4. Requisitos Não Funcionais

| Código | Requisito | Diretriz |
|---|---|---|
| RNF-001 | Segurança de senha | Senhas devem ser armazenadas com hash seguro |
| RNF-002 | Controle de sessão | Usar token ou sessão segura com expiração |
| RNF-003 | Auditoria | Registrar criação, edição e fechamento mensal |
| RNF-004 | Privacidade | Proteger dados pessoais e localização conforme LGPD |
| RNF-005 | Disponibilidade do protótipo | Servidor deve ser acessível por usuários externos autorizados |
| RNF-006 | Fotos | Definir tamanho máximo, formato aceito e estratégia de compressão |
| RNF-007 | Performance | Fluxo completo de viagem deve ser possível em até 2 minutos |
| RNF-008 | Compatibilidade mobile | Interface deve funcionar bem em tela de celular |
| RNF-009 | Backup | Banco e fotos devem ter estratégia de backup antes de uso produtivo |
| RNF-010 | Observabilidade | Logs devem ajudar a diagnosticar falhas de API, upload e banco |

## 5. Critérios De Sucesso Do Protótipo

- Usuário registra uma viagem completa em menos de 2 minutos, considerando login já ativo.
- App impede registros sem foto obrigatória.
- App impede registros sem GPS obrigatório.
- Backend entrega dados prontos para relatório mensal, incluindo coordenadas GPS e endereço quando disponível.
- Responsável autorizado consegue fechar fechamento mensal por motorista individual.
- Analista consegue consultar dados consolidados por período.

## 6. Roadmap Inicial

1. Definir modelo de dados e endpoints principais.
2. Criar backend mínimo com FastAPI, PostgreSQL e Docker.
3. Implementar autenticação real com e-mail e senha.
4. Criar fluxo de seleção de veículo, partida e chegada.
5. Validar foto obrigatória, GPS obrigatório e km final.
6. Criar histórico, fechamento mensal e correção antes do fechamento final.
7. Criar relatório mensal e exportação.
