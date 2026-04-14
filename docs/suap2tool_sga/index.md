# Broker `suap2tool_sga` — Referência de API

> **⚠ Em elaboração**
>
> Este broker ainda não foi implementado. Esta documentação será escrita assim que a
> implementação estiver disponível.

---

## Visão geral

| Item                  | Valor                                                          |
|-----------------------|----------------------------------------------------------------|
| Plugin Moodle         | [`tool_sga`](https://github.com/cte-zl-ifrn/moodle-tool_sga) |
| Endpoint Moodle       | `/local/tool_sga/api/index.php`                                |
| Broker (classe)       | `Suap2ToolSgaBroker` (`src/integrador/brokers/suap2tool_sga/`)|
| Status                | **Não implementado** — métodos levantam `NotImplementedError`  |

## Propósito

Este broker receberá payloads no **padrão Suap**, os traduzirá para o **padrão SGA genérico**
e enviará ao plugin Moodle `tool_sga`. Será indicado para instituições que usam o SUAP e
querem aproveitar funcionalidades extras do `tool_sga`.

## Mock HTTP

O `ToolSgaHTTPMock` já existe e retorna **501** para qualquer chamada autenticada,
servindo como placeholder até a implementação.

Para testar o comportamento atual do stub:

```python
from integrador.moodle_mock import ToolSgaHTTPMock

mock = ToolSgaHTTPMock()
response = mock.post(
    "https://moodle.test/local/tool_sga/api/index.php?qualquer_servico",
    jsonbody={},
    headers={"Authentication": f"Token {ToolSgaHTTPMock.TOKEN}"},
)
assert response.status_code == 501
```

Documentação do mock: [docs/tests/moodle_mock.md](../tests/moodle_mock.md#broker-suap2tool_sga)
