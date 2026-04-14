# Broker `suap2local_suap` — Referência de API

Este documento descreve a API de integração do broker `suap2local_suap`:
o broker que recebe payloads no **padrão Suap** e os envia ao plugin Moodle **`local_suap`**.

**Status:** implementado e em produção.

---

## Visão geral

| Item                  | Valor                                              |
|-----------------------|----------------------------------------------------|
| Plugin Moodle         | [`local_suap`](https://github.com/cte-zl-ifrn/moodle-local_suap) |
| Endpoint Moodle       | `/local/suap/api/index.php`                        |
| Broker (classe)       | `Suap2LocalSuapBroker` (`src/integrador/brokers/suap2local_suap/`) |
| Autenticação Moodle   | `Authentication: Token <token_do_ambiente>`        |
| Autenticação cliente  | `Authentication: Token <SUAP_INTEGRADOR_KEY>`      |

---

## Endpoints do Integrador

### `POST /api/enviar_diarios/`

Sincroniza matrículas, papéis e coortes no Moodle para um diário.

#### Headers obrigatórios

```http
Authentication: Token <SUAP_INTEGRADOR_KEY>
Content-Type: application/json
```

#### Payload (padrão Suap)

Todos os campos a seguir são obrigatórios.

```json
{
    "campus": {
        "id":       1,
        "sigla":    "ZL",
        "descricao":"Campus Zona Leste"
    },
    "curso": {
        "id":     1,
        "codigo": "15806",
        "nome":   "Sistemas Operacionais Abertos"
    },
    "turma": {
        "id":     2,
        "codigo": "20261.6.15806.1E"
    },
    "componente": {
        "id":       1,
        "sigla":    "TEC.1023",
        "descricao":"Bancos de Dados"
    },
    "diario": {
        "id":       2,
        "sigla":    "TEC.1023",
        "situacao": "Aberto"
    }
}
```

##### Campos obrigatórios por objeto

| Objeto       | Campos obrigatórios          |
|--------------|------------------------------|
| `campus`     | `id`, `sigla`, `descricao`   |
| `curso`      | `id`, `codigo`, `nome`       |
| `turma`      | `id`, `codigo`               |
| `componente` | `id`, `sigla`, `descricao`   |
| `diario`     | `id`, `sigla`, `situacao`    |

#### Payload enviado ao Moodle

O broker injeta a lista de **coortes** selecionadas (calculada pelo `BaseBroker.get_cohort()`
com base nas regras `rule_diario` e `rule_coordenacao` dos cohorts ativos) antes de enviar
ao Moodle:

```json
{
    "campus":     { ... },
    "curso":      { ... },
    "turma":      { ... },
    "componente": { ... },
    "diario":     { ... },
    "coortes": [
        {
            "nome":    "Professores ZL",
            "role":    "editingteacher",
            "ativo":   true,
            "idnumber":"prof-zl",
            "descricao":"Corpo docente do campus ZL",
            "colaboradores": [
                {
                    "nome":   "João da Silva",
                    "email":  "joao@ifrn.edu.br",
                    "login":  "joao.silva",
                    "status": true
                }
            ]
        }
    ]
}
```

#### Resposta de sucesso (HTTP 200)

O Integrador adiciona `ambiente` à resposta do plugin:

```json
{
    "url":                  "https://ava.zl.ifrn.edu.br/course/view.php?id=42",
    "url_sala_coordenacao": "https://ava.zl.ifrn.edu.br/course/view.php?id=43",
    "roles_not_found":      [],
    "ambiente":             "https://ava.zl.ifrn.edu.br"
}
```

#### Respostas de erro

| Código | Condição                                                         |
|--------|------------------------------------------------------------------|
| 400    | Método não é POST                                                |
| 401    | Header `Authentication` ausente ou token inválido                |
| 404    | Nenhum Ambiente ativo corresponde ao payload                     |
| 422    | Payload com campos obrigatórios ausentes                         |
| 525    | Erro ao obter coortes (falha interna antes de chamar o Moodle)   |
| 5xx    | Erro do Moodle ou falha de comunicação                            |

Corpo do erro (exemplo 422):

```json
{
    "code":     422,
    "error":    "Campos obrigatórios ausentes no payload de sync_up_enrolments: campus.id, curso.nome.",
    "event_id": "sentry-event-id"
}
```

---

### `GET /api/baixar_notas/`

Baixa as notas de um diário do Moodle.

#### Headers obrigatórios

```http
Authentication: Token <SUAP_INTEGRADOR_KEY>
```

#### Query parameters

| Parâmetro     | Tipo   | Obrigatório | Descrição                              |
|---------------|--------|-------------|----------------------------------------|
| `campus_sigla`| string | Sim         | Sigla do campus (para seleção do ambiente) |
| `diario_id`   | int    | Sim         | ID do diário no SUAP                   |

Exemplo:

```http
GET /api/baixar_notas/?campus_sigla=ZL&diario_id=2
Authentication: Token <SUAP_INTEGRADOR_KEY>
```

#### Resposta de sucesso (HTTP 200)

```json
[
    {
        "matricula": "20261001",
        "nota":       8.5,
        "diario_id":  "2"
    }
]
```

#### Respostas de erro

| Código | Condição                                                  |
|--------|-----------------------------------------------------------|
| 400    | Método não é GET                                          |
| 401    | Header `Authentication` ausente ou token inválido         |
| 404    | Nenhum Ambiente ativo corresponde ao `campus_sigla`       |
| 5xx    | Erro do Moodle ou falha de comunicação                     |

---

## Stack de decorators

As views são compostas por decorators aplicados de fora para dentro:

### `sync_up_enrolments`

```
@transaction.atomic
@json_response         ← garante JsonResponse na saída
@exception_as_json     ← captura exceções → JSON + Sentry
@check_is_post         ← rejeita se não for POST (400)
@valid_token           ← valida SUAP_INTEGRADOR_KEY (401)
@check_json(operacao)  ← valida Content-Type e carrega JSON recebido
@detect_ambiente       ← seleciona Ambiente via expressao_seletora
@try_solicitacao       ← cria registro Solicitacao, atualiza status
```

### `sync_down_grades`

```
@transaction.atomic
@json_response
@exception_as_json
@check_is_get          ← rejeita se não for GET (400)
@valid_token
@detect_ambiente       ← usa ?campus_sigla= para seleção
@try_solicitacao
```

---

## Fluxo completo — `sync_up_enrolments`

```
SGA (SUAP)
  │  POST /api/enviar_diarios/
  │  Authentication: Token <SUAP_INTEGRADOR_KEY>
  │  { campus, curso, turma, componente, diario }
  ▼
Integrador (Django)
  ├── valid_token → verifica SUAP_INTEGRADOR_KEY
  ├── check_json  → carrega JSON recebido
  ├── detect_ambiente → seleciona Ambiente via expressao_seletora
  ├── try_solicitacao → cria Solicitacao(status=P)
  ├── _validate_sync_payload → verifica campos obrigatórios (422 se falhar)
  ├── get_cohort → calcula lista de coortes elegíveis
  ├── POST local_suap → { ...payload, coortes: [...] }
  └── atualiza Solicitacao(status=S/F) + retorna ao SGA
  ▼
Plugin Moodle (local_suap)
  Authentication: Token <token_do_ambiente>
  → cria curso, matricula usuários, atribui papéis
  → retorna { url, url_sala_coordenacao, roles_not_found }
```

---

## Variáveis de ambiente

| Variável              | Descrição                                                           |
|-----------------------|---------------------------------------------------------------------|
| `SUAP_INTEGRADOR_KEY` | Token que o SGA deve enviar no header `Authentication`              |
| `DJANGO_SECRET_KEY`   | Chave secreta Django                                                |

Configuradas em `src/settings/securities.py` e injetadas via `.env` ou Docker Compose.

---

## Teste local sem Moodle real

Use `LocalSuapHTTPMock` para simular o endpoint `/local/suap/api/index.php`:

```python
from integrador.moodle_mock import LocalSuapHTTPMock

mock = LocalSuapHTTPMock()
response = mock.post(
    "https://moodle.test/local/suap/api/index.php?sync_up_enrolments",
    jsonbody={
        "campus":     {"id": 1, "sigla": "ZL",       "descricao": "Campus ZL"},
        "curso":      {"id": 1, "codigo": "15806",   "nome": "Sistemas Operacionais Abertos"},
        "turma":      {"id": 2, "codigo": "20261.6.15806.1E"},
        "componente": {"id": 1, "sigla": "TEC.1023", "descricao": "Bancos de Dados"},
        "diario":     {"id": 2, "sigla": "TEC.1023", "situacao": "Aberto"},
    },
    headers={"Authentication": f"Token {LocalSuapHTTPMock.TOKEN}"},
)
assert response.ok
```

Documentação completa do mock: [docs/MOODLE_HTTP_MOCK.md](../MOODLE_HTTP_MOCK.md#broker-suap2local_suap)

---

## Referências de código

| Artefato                  | Caminho                                             |
|---------------------------|-----------------------------------------------------|
| Broker                    | `src/integrador/brokers/suap2local_suap/__init__.py`|
| Base do broker            | `src/integrador/brokers/base/__init__.py`           |
| Views                     | `src/integrador/views.py`                           |
| URLs                      | `src/integrador/urls.py`                            |
| Decorators                | `src/integrador/decorators.py`                      |
| Mock HTTP                 | `src/integrador/moodle_mock.py`                     |
| Testes                    | `src/integrador/tests.py` → `Suap2LocalSuapBrokerTestCase`, `LocalSuapHTTPMockTestCase` |
| Exemplo de requisição     | `requests.http` (raiz do projeto)                   |
