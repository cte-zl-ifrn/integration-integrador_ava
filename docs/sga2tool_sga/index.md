# Broker `sga2tool_sga` — Referência de API

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
| Broker (classe)       | `Sga2ToolSgaBroker` (`src/integrador/brokers/sga2tool_sga/`)  |
| Status                | **Não implementado** — métodos levantam `NotImplementedError`  |

## Propósito

Este broker receberá payloads no **padrão SGA genérico** (adequado para qualquer sistema
acadêmico: SIGAA, qAcadêmico, etc.) e os enviará diretamente ao plugin Moodle `tool_sga`.
Será a estratégia mais flexível, permitindo que qualquer SGA se integre ao Moodle desde que
a instituição adapte o payload ao padrão SGA esperado.

## Compartilhamento com `suap2tool_sga`

Como ambos os brokers (`suap2tool_sga` e `sga2tool_sga`) utilizam o mesmo plugin Moodle
(`tool_sga`) e o mesmo endpoint, compartilham o mock `ToolSgaHTTPMock` e a classe de teste
`ToolSgaHTTPMockTestCase`.

Quando este broker for implementado, considere separar as classes de teste por broker.

## Mock HTTP

O `ToolSgaHTTPMock` já existe e retorna **501** para qualquer chamada autenticada.

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

Documentação do mock: [docs/tests/moodle_mock.md](../tests/moodle_mock.md#broker-sga2tool_sga)
