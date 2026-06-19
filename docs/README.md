# Documentação Do Projeto

## CONTROLE ITINERÁRIO COMERCIAL BELLO

Aplicativo mobile para digitalizar o controle de quilômetros rodados. O usuário registra km inicial e final, foto do hodômetro, localização GPS e endereço aproximado, evitando planilhas manuais e reconciliações offline no fim do mês.

## Índice Da Documentação

| Arquivo | Finalidade |
|---|---|
| `../AGENTS.md` | Guia operacional para a IA trabalhar no projeto |
| `requisitos.md` | Requisitos funcionais, não funcionais, perfis e critérios de sucesso |
| `regras-negocio.md` | Regras obrigatórias, validações, status e fechamento mensal |
| `telas-fluxos.md` | Telas mobile, fluxos e critérios de aceite por tela |
| `modelo-dados.md` | Entidades, campos obrigatórios e relacionamentos |
| `api.md` | Endpoints REST iniciais e contratos sugeridos |
| `arquitetura.md` | Stack, Docker, estrutura de pastas e decisões técnicas |
| `testes.md` | Política obrigatória de testes e validação automatizada |
| `agentes/` | Três agentes validadores: `agente-backend.md` (backend completo), `agente-frontend.md` (telas e fluxos mobile), `agente-relatorios.md` (relatórios e documentação) |

## Contexto

Hoje, o controle de quilômetros rodados é feito manualmente em planilhas. No fim do mês, os dados precisam ser reconciliados offline, o que gera retrabalho, risco de erro e baixa rastreabilidade.

O protótipo deve permitir testes reais com usuários externos, em servidor acessível pela internet e com login real por e-mail e senha.

## Fluxo Principal

```txt
Login
  -> Selecionar veículo
  -> Registrar partida com km, foto, GPS e endereço quando disponível
  -> Registrar chegada com km, foto, GPS, endereço quando disponível e rota
  -> Exibir conclusão da viagem e opção de sair
  -> Entrar no fechamento mensal
  -> Consultar consolidado mensal aberto ou fechado por motorista
  -> Gerar relatório mensal
```

## Prioridade Inicial

1. Definir modelo de dados e endpoints.
2. Criar backend com FastAPI, PostgreSQL e Docker.
3. Implementar autenticação real.
4. Criar fluxo de partida e chegada.
5. Aplicar validações de foto, GPS e km.
6. Criar histórico, fechamento mensal e relatório mensal.
7. Executar os testes automatizados aplicáveis antes de considerar qualquer entrega pronta.
8. Acionar os agentes validadores obrigatórios e registrar seus vereditos antes de considerar uma entrega pronta.
