# Politica De Testes

## 1. Objetivo

Os testes automatizados validam que o sistema cumpre as regras obrigatorias de viagem, autenticacao, permissao, fechamento mensal, fotos, GPS, quilometragem e relatorios.

Nenhuma alteracao de codigo, endpoint, regra de negocio, modelo de dados, fluxo de tela ou configuracao critica deve ser considerada pronta sem executar os testes aplicaveis.

## 2. Regra Obrigatoria De Validacao

Sempre que houver alteracao funcional, deve ser executado no minimo:

```bash
pytest
```

Quando a mudanca afetar banco, migracoes ou integracao com PostgreSQL, os testes devem ser executados contra uma base de teste descartavel.

Se os testes nao puderem ser executados, a entrega deve registrar o motivo, o risco e o comando que deve ser executado depois. Se algum teste falhar, a entrega nao deve ser considerada concluida.

## 3. Pontuacao De Risco

Todo teste automatizado deve possuir marcador de risco.

Formato obrigatorio:

```python
@pytest.mark.risco(
    peso=100,
    criticidade="critica",
    area="viagem",
    referencias=("RF-006", "RN-004"),
)
```

Escala oficial:

| Criticidade | Peso | Exemplo |
|---|---:|---|
| `critica` | 100 | Aceitar viagem sem foto, sem GPS, sem token ou com permissao indevida |
| `alta` | 50 | Retorno incompleto em relatorio, falha em listagem de fotos ou sessao inconsistente |
| `media` | 20 | Validacao secundaria ou regra de exibicao que nao bloqueia seguranca |
| `baixa` | 5 | Ajuste de mensagem, formato, detalhe de resposta ou saude tecnica da API |

O peso deve corresponder exatamente a criticidade. Um teste `critica` sempre vale `100`, um teste `alta` sempre vale `50`, e assim por diante.

## 4. Regra De Bloqueio Por Risco

A entrega fica bloqueada quando qualquer uma destas condicoes acontecer:

- `pontos_falha` maior que `0`;
- `pontos_nao_validados` maior que `0`;
- `indice_conformidade_percentual` menor que `100`;
- teste sem marcador `@pytest.mark.risco(...)`;
- teste com peso diferente da criticidade.

Na pratica, qualquer falha ou teste nao executado em funcionalidade aplicavel impede considerar a entrega como pronta.

A suite deve retornar codigo de falha quando o relatorio de risco indicar bloqueio de entrega. Assim, pipelines e execucoes locais nao aprovam uma entrega com testes falhos, pulados, nao executados ou com conformidade menor que `100%`.

## 5. Relatorio Auditavel

Ao executar `pytest`, a suite gera um resumo de risco no terminal e tenta gravar um relatorio JSON em:

```txt
backend/app/tests/reports/risco-testes.json
```

O caminho pode ser alterado:

```bash
pytest --risk-report backend/app/tests/reports/risco-testes.json
```

Tambem e recomendado gerar relatorio JUnit para historico em pipelines:

```bash
pytest --junitxml backend/app/tests/reports/junit.xml
```

Campos principais do relatorio de risco:

| Campo | Significado |
|---|---|
| `pontos_risco_total` | Soma dos pesos dos testes coletados |
| `pontos_falha` | Soma dos pesos dos testes que falharam |
| `pontos_nao_validados` | Soma dos pesos dos testes pulados ou nao executados |
| `indice_conformidade_percentual` | Percentual de pontos validados com sucesso |
| `bloqueia_entrega` | Indica se a entrega deve ser bloqueada |
| `por_criticidade` | Resumo de pontos por criticidade |
| `testes` | Lista auditavel com teste, peso, area, referencias e status |

## 6. Escopo Minimo Obrigatorio

Devem existir testes para:

- saude tecnica da API via endpoint de infraestrutura;
- estrutura inicial do banco, models e migrations;
- autenticacao e sessao;
- recuperação de senha por token temporário;
- permissao por perfil;
- solicitação pública de cadastro com aprovação restrita a admin;
- criacao de viagem;
- obrigatoriedade de foto inicial;
- obrigatoriedade de GPS inicial;
- encerramento de viagem;
- obrigatoriedade de foto final;
- obrigatoriedade de GPS final;
- validacao de `km_final >= km_inicial`;
- rota obrigatoria na chegada;
- fechamento mensal aberto e fechado por motorista;
- endpoints legados de aprovacao/reprovacao retornando `410 Gone`;
- consulta e exportacao de relatorio mensal.
- evidencias de foto, GPS e endereco presentes no item do relatorio mensal e na exportacao;
- cenario de geocodificacao indisponivel validando `endereco = null`, `endereco_resolvido = false` e texto `Endereco nao resolvido` para exibicao/exportacao.
- endpoint de consulta de GPS por viagem.

## 7. Estrutura Atual

```txt
backend/
  app/
    tests/
      conftest.py
      assertions.py
      factories.py
      helpers.py
      test_auth.py
      test_signup_requests.py
      test_trips_start.py
      test_trips_finish.py
      test_approvals.py
      test_permissions.py
      test_photos.py
      test_reports.py
pytest.ini
```

Esses arquivos sao testes de contrato. Eles descrevem o comportamento esperado da API e devem falhar enquanto o backend ainda nao estiver implementado.

## 8. Como Executar

Ha dois modos previstos.

Dentro do container da API, a imagem usa `backend/pytest.ini` copiado para `/app/pytest.ini`, permitindo executar testes direcionados com os mesmos marcadores de risco.

### 8.1 Importando A Aplicacao FastAPI

Por padrao, os testes tentam importar:

```txt
app.main:app
```

Para usar outro caminho:

```bash
$env:APP_IMPORT_PATH="app.main:app"
pytest
```

### 8.2 Testando API Em Execucao

Tambem e possivel testar uma API ja publicada localmente ou em servidor de teste:

```bash
$env:API_BASE_URL="http://localhost:8000"
pytest
```

## 9. Dados De Teste Obrigatorios

Os testes de contrato exigem usuarios e veiculo de teste cadastrados em uma base descartavel.

Variaveis obrigatorias:

```bash
$env:TEST_MOTORISTA_EMAIL="motorista.teste@bello.local"
$env:TEST_MOTORISTA_PASSWORD="pelego@23"
$env:TEST_APROVADOR_EMAIL="aprovador.teste@bello.local"
$env:TEST_APROVADOR_PASSWORD="senha-de-teste"
$env:TEST_ANALISTA_EMAIL="analista.teste@bello.local"
$env:TEST_ANALISTA_PASSWORD="senha-de-teste"
$env:TEST_VEICULO_ID="uuid-do-veiculo-de-teste"
```

Esses dados nao devem apontar para ambiente produtivo.

## 10. Contrato De Upload Validado Pelos Testes

Para simplificar o prototipo, os testes assumem que partida e chegada recebem foto no mesmo request via `multipart/form-data`.

Campos esperados:

- `payload`: JSON serializado com os dados da partida ou chegada;
- `foto_hodometro`: arquivo de imagem do hodometro.

Esse contrato torna executavel a regra de que o usuario nao pode salvar viagem sem foto obrigatoria.
