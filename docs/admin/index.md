# Guia do administrador — Integrador AVA

Este documento descreve como configurar e operar o Integrador AVA pela interface Django admin
(`/admin/`).

O acesso requer conta com permissão de staff ou superusuário. A autenticação é feita via OAuth
com o SUAP (ver configuração em `settings/securities.py`).

---

## Módulos do admin

| Módulo       | URL admin                           | Finalidade                                             |
|--------------|-------------------------------------|--------------------------------------------------------|
| Ambientes    | `/admin/integrador/ambiente/`       | Configurar instâncias Moodle de destino                |
| Solicitações | `/admin/integrador/solicitacao/`    | Monitorar e reprocessar integrações                    |
| Cohorts      | `/admin/coorte/cohort/`             | Gerenciar coortes e regras de seleção                  |
| Roles        | `/admin/coorte/role/`               | Gerenciar papéis (perfis no Moodle)                    |
| Enrolments   | `/admin/coorte/enrolment/`          | Gerenciar vínculos usuário ↔ cohort                    |

---

## Ambientes

### O que é um Ambiente

Um **Ambiente** representa uma instância de Moodle de destino. O Integrador pode ter
múltiplos Ambientes cadastrados e escolhe automaticamente qual usar em cada requisição com
base na `expressao_seletora` avaliada sobre o payload recebido.

### Criar um Ambiente

Acesse `/admin/integrador/ambiente/add/` e preencha:

| Campo                | Descrição                                                                                       | Exemplo                       |
|----------------------|-------------------------------------------------------------------------------------------------|-------------------------------|
| **Nome**             | Nome descritivo (identificação interna)                                                         | `Moodle Produção ZL`          |
| **URL**              | URL base do Moodle, **sem barra final**                                                         | `https://ava.zl.ifrn.edu.br`  |
| **Token**            | Token configurado no plugin Moodle (`local_suap` ou `tool_sga`). Deve ser idêntico ao do plugin | `token_super_secreto`         |
| **Expressão seletora** | Expressão `rule_engine` que determina quando este ambiente é escolhido (ver abaixo)           | `campus.sigla == "ZL"`        |
| **Ordem**            | Prioridade de seleção: menor valor = maior prioridade. Use 0 para o ambiente principal          | `1`                           |
| **Ativo**            | Desmarque para desativar o ambiente sem excluí-lo                                               | ✓                             |

#### Expressão seletora — exemplos

A expressão é avaliada sobre o JSON recebido na requisição. Sintaxe da biblioteca
[`rule_engine`](https://zerosteiner.github.io/rule-engine/).

```
# Campus específico
campus.sigla == "ZL"

# Múltiplos campi
campus.sigla in ["ZL", "CE", "NA"]

# Catch-all (sempre corresponde — use com ordem alta)
1 == 1
```

> Se dois ambientes correspondem ao mesmo payload, o de menor `ordem` é escolhido.
> Se a expressão referir a um campo ausente no JSON, o ambiente é ignorado (não causa erro).

#### Importar/exportar Ambientes

O admin suporta importação e exportação via CSV/XLS. Use o botão **Exportar** na lista e
**Importar** para carregar ambientes em lote. O campo `nome` é usado como chave de
identificação na importação (registros existentes são atualizados).

### Editar ou desativar um Ambiente

- Para editar, clique no nome do ambiente na lista.
- Para desativar temporariamente sem excluir, desmarque o campo **Ativo**.
- Para excluir permanentemente, use o botão **Excluir** na página de edição.

> **Atenção:** excluir um Ambiente não exclui as Solicitações associadas (o campo `ambiente`
> nas solicitações aceita `null`).

---

## Solicitações

### O que é uma Solicitação

Uma **Solicitação** é o registro de uma operação de integração: contém o payload recebido do
SGA, o payload enviado ao Moodle (com coortes injetadas) e a resposta obtida. É criada
automaticamente a cada chamada aos endpoints do Integrador.

### Listar e filtrar

Acesse `/admin/integrador/solicitacao/`. Use os filtros à direita:

| Filtro         | Descrição                                          |
|----------------|----------------------------------------------------|
| **Operação**   | `Sync UP: Diário` ou `Sync DOWN: Notas`            |
| **Tipo**       | `regular`, `coordenacao`, etc.                     |
| **Ambiente**   | Filtra por instância Moodle                        |
| **Status**     | `Sucesso`, `Falha`, `Processando`, `Não Definido`  |
| **Status code**| Código HTTP da resposta do Moodle (ex.: `200`)     |
| **Campus**     | Sigla do campus extraída do payload                |

Use a **hierarquia de datas** no topo para navegar por período.

Use a **busca** para encontrar por `diario_codigo` ou `diario_id`.

### Visualizar uma Solicitação

Clique em qualquer linha para ver o detalhe. Os campos JSON (`recebido`, `enviado`,
`respondido`) são exibidos no widget JSON interativo (editável apenas por staff autorizado).

### Reenviar (reprocessar)

Na coluna **Ações** da lista, clique em **Reenviar** para disparar novamente a integração
usando o payload `recebido` original. Isso cria uma nova Solicitação com o resultado do
reprocessamento.

> Use "Reenviar" quando uma integração falhou por indisponibilidade temporária do Moodle ou
> por problemas de rede, após o problema ser resolvido.

### Interpretar Status

| Status      | Código | Significado                                                        |
|-------------|--------|--------------------------------------------------------------------|
| Sucesso     | `S`    | O Moodle processou e retornou com sucesso                          |
| Falha       | `F`    | O Moodle retornou erro ou houve falha de comunicação               |
| Processando | `P`    | A solicitação foi recebida mas ainda não concluída (estado inicial)|
| Não Definido| `None` | Estado indefinido (registros antigos ou incompletos)               |

O campo **status_code** contém o código HTTP retornado pelo Moodle (ex.: `200`, `422`, `500`).

---

## Cohorts (Coortes)

### O que são Cohorts

Cohorts são grupos do Moodle (coortes) que determinam quais usuários fazem parte de um curso.
O Integrador injecta automaticamente a lista de cohorts no payload enviado ao Moodle com
base em regras configuradas.

### Criar um Cohort

Acesse `/admin/coorte/cohort/add/`:

| Campo              | Descrição                                                              |
|--------------------|------------------------------------------------------------------------|
| **Nome**           | Nome do cohort no Moodle                                               |
| **Idnumber**       | Identificador único do cohort no Moodle                                |
| **Descrição**      | Texto descritivo                                                       |
| **Role**           | Papel (role) associado ao cohort                                       |
| **rule_diario**    | Expressão `rule_engine` avaliada sobre o payload para cohorts de diário |
| **rule_coordenacao** | Expressão `rule_engine` avaliada para cohorts de coordenação         |
| **Ativo**          | Se o cohort está ativo para seleção                                    |

### Roles

Os Roles representam papéis no Moodle (ex.: `editingteacher`, `student`). Acesse
`/admin/coorte/role/` para gerenciar.

---

## Referências

| Artefato          | Caminho                                      |
|-------------------|----------------------------------------------|
| Admin integrador  | `src/integrador/admin.py`                    |
| Admin coorte      | `src/coorte/admin.py`                        |
| Modelos           | [docs/model/](../model/index.md                     |
| Configuração completa | [docs/](../index.md) → "Configuração"          |
