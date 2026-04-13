# Moodle HTTP Mock

Este documento descreve o mock HTTP de Moodle da app `integrador`, criado para permitir:

- testes automatizados sem depender de Moodle real com dados;
- desenvolvimento de interface com respostas previsíveis;
- execução local mais estável em modo debug.

## Visão geral

O mock foi implementado em `integrador/moodle_mock.py` e integrado no fluxo HTTP em `integrador/utils.py`.

Quando habilitado, chamadas para endpoints do plugin local do Moodle (`/local/suap/api/index.php`) deixam de usar rede externa e passam a responder localmente com payloads mockados.

## Endpoints simulados

Atualmente o mock cobre os serviços usados no broker `Suap2LocalSuapBroker`:

- `sync_up_enrolments` (POST)
- `sync_down_grades` (GET)

### Exemplo de retorno `sync_up_enrolments`

```json
{
    "status": "success",
    "mock": true,
    "url": "https://moodle.test.com/course/view.php?id=1",
    "cohort_count": 1
}
```

### Exemplo de retorno `sync_down_grades`

```json
[
    {
        "matricula": "20260001",
        "nota": 8.5,
        "diario_id": "123",
        "mock": true
    }
]
```

## Variáveis de ambiente

As variáveis são carregadas em `settings/developments.py`:

- `MOODLE_HTTP_MOCK_ENABLED`:
    - `true`: usa o mock nas chamadas HTTP para `/local/suap/api/index.php`.
    - `false`: usa `requests` normalmente.

- `MOODLE_HTTP_MOCK_BACKGROUND`:
    - `true`: sobe servidor HTTP mock em background ao iniciar a app em DEBUG.
    - `false`: não sobe servidor.

- `MOODLE_HTTP_MOCK_HOST`:
    - host de bind do servidor mock (default: `0.0.0.0`).

- `MOODLE_HTTP_MOCK_PORT`:
    - porta do servidor mock (default: `18091`).

## Fluxo em modo debug (interface)

No `docker-compose.yml` do workspace, o serviço `integrador` já está configurado para:

- `MOODLE_HTTP_MOCK_ENABLED=true`
- `MOODLE_HTTP_MOCK_BACKGROUND=true`
- `MOODLE_HTTP_MOCK_HOST=0.0.0.0`
- `MOODLE_HTTP_MOCK_PORT=18091`

Com isso, ao subir o ambiente em DEBUG, você pode validar fluxos de interface que dependem de integração sem precisar provisionar dados no Moodle.

## Uso em testes

### 1) Testes unitários com mock habilitado

Use `override_settings`:

```python
@override_settings(MOODLE_HTTP_MOCK_ENABLED=True)
def test_sync_up_uses_mock(self):
    result = self.broker.sync_up_enrolments()
    self.assertTrue(result["mock"])
```

### 2) Garantia de não usar rede externa

Você pode validar que `requests` não foi chamado:

```python
@override_settings(MOODLE_HTTP_MOCK_ENABLED=True)
@patch("integrador.utils.requests.post")
def test_http_post_json_uses_mock(self, mock_post):
    http_post_json("https://moodle.test.com/local/suap/api/index.php?sync_up_enrolments", {"coortes": []})
    mock_post.assert_not_called()
```

## Quando usar mock e quando usar Moodle real

Use mock quando:

- o objetivo é validar fluxo da aplicação (UI/API) e regras internas do integrador;
- você precisa de ambiente determinístico para testes repetíveis;
- o Moodle local não está pronto ou sem dados mínimos.

Use Moodle real quando:

- você precisa validar contrato completo de integração;
- quer testar diferenças de payload/erros de plugin real;
- precisa validar comportamento fim a fim em ambiente próximo de produção.

## Troubleshooting

- Sintoma: integração continua chamando Moodle real.
    - Verifique `MOODLE_HTTP_MOCK_ENABLED=true`.
    - Confirme se a URL chamada contém `/local/suap/api/index.php`.

- Sintoma: porta do mock em conflito.
    - Ajuste `MOODLE_HTTP_MOCK_PORT`.

- Sintoma: servidor mock não sobe em background.
    - Verifique se `DJANGO_DEBUG=true`.
    - Verifique `MOODLE_HTTP_MOCK_BACKGROUND=true`.
    - Confira logs da app `integrador`.

## Referências de código

- Implementação do mock: `src/integrador/moodle_mock.py`
- Integração no HTTP client: `src/integrador/utils.py`
- Startup em DEBUG: `src/integrador/apps.py`
- Settings de mock: `src/settings/developments.py`
- Testes do mock: `src/integrador/tests.py`
