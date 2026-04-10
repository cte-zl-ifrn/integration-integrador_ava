# Integrador integrador SUAP-Moodle

O Integrador é um Middleware que integra o SUAP ao Moodle.

> Neste projeto usamos Git, Python 3.14+, [Docker](https://docs.docker.com/engine/install/) e o [Docker Compose Plugin](https://docs.docker.com/compose/install/compose-plugin/#:~:text=%20Install%20the%20plugin%20manually%20%F0%9F%94%97%20%201,of%20Compose%20you%20want%20to%20use.%20More%20). O setup foi todo testado usando o Linux (inclusive WSL2) e Mac OS.

## Como funciona

...

As variáveis de ambiente no SUAP têm as seguintes definições:

- `VARNAME` - ...

## Como implantar

### Via GitHub Actions

O projeto está configurado para deploy automático no Docker Hub via GitHub Actions.

**Configuração necessária:**

1. No repositório GitHub, vá para **Settings > Secrets and variables > Actions**.
2. Adicione os seguintes secrets:
    - `DOCKER_USERNAME`: Seu nome de usuário no Docker Hub (ctezlifrn).
    - `DOCKER_PASSWORD`: Seu token de acesso do Docker Hub (gerado em Docker Hub > Account Settings > Security > New Access Token).

**Deploy automático:**

- O workflow é acionado em push para a branch `main`.
- A imagem é construída para o estágio `production` e enviada para `ctezlifrn/avaintegrador:latest` e `ctezlifrn/avaintegrador:<commit-sha>`.

### Manualmente

Para deploy manual, siga as instruções em "Como construir a imagem localmente" e depois faça push para o Docker Hub.

```bash
docker push ctezlifrn/avaintegrador:<tag>
```

## Como construir a imagem localmente

```bash
cd ~/projetos/IFRN/ava/integration/integrador_ava

git checkout proximo
docker build -t ctezlifrn/avaintegrador:proximo .

git checkout teste
docker build -t ctezlifrn/avaintegrador:teste .

git checkout producao
docker build -t ctezlifrn/avaintegrador:producao .
```

## Como iniciar o desenvolvimento

Veja o `ava_workspace` para o desenvolvimento.

## Qualidade de código e cobertura

O projeto usa gates de qualidade locais (pre-commit/pre-push) e no CI.

### 1) Ativar pre-commit

```bash
cd ~/projetos/IFRN/ava/integration/integrador_ava
python -m pip install -r requirements-dev.txt
pre-commit install --hook-type pre-commit --hook-type pre-push
```

Para validar manualmente todos os arquivos:

```bash
pre-commit run --all-files
```

Para validar somente templates Django (HTML) manualmente:

```bash
python -m djlint --profile=django --check --lint src
```

### 2) Regras aplicadas

- Lint Python: `ruff`, `black`
- Lint JS/CSS/Markdown: `prettier --check`
- Lint HTML: `djlint --check --lint`
- SAST: `bandit` (Python) e `semgrep` (Python/JS/CSS/Markdown/HTML)
- Testes unitários com cobertura no `pre-push` (via `coverage run src/manage.py test`)

### 3) Política de cobertura

- Mínimo obrigatório: **91%**
- Meta ideal: **95%**
- Não regressão (se possível): comparação com baseline em `.coverage-baseline`

O gate de cobertura é aplicado por `src/check_coverage_gate.py`.

Importante: o runner de testes usa Django com PostgreSQL (`POSTGRES_HOST=db`).
Em ambiente local, execute com banco disponível (ex.: Docker Compose do projeto).

Para criar/atualizar baseline local:

```bash
coverage run --rcfile=src/.coveragerc src/manage.py test --verbosity 1
coverage report --fail-under=91
coverage xml -o coverage.xml
python src/check_coverage_gate.py --coverage-xml coverage.xml --baseline-file .coverage-baseline --min 91 --ideal 95 --write-baseline
```

## CI/CD e Codecov

O workflow em `.github/workflows/docker-deploy.yml` executa:

1. Qualidade em diff (lint e SAST nos arquivos alterados)
2. Testes unitários com cobertura (91% mínimo) em ambiente com PostgreSQL de serviço
3. Upload da cobertura para o Codecov
4. Build/push Docker somente em tags
5. Deploy somente em tags (apenas após qualidade aprovada)

Para envio ao Codecov, configure o secret:

- `CODECOV_TOKEN`

As regras de status do Codecov ficam em `codecov.yml`:

- `project.target: auto` (evita regressão em relação ao baseline da branch base)
- `patch.target: 80%`

## Screenshots

...

## Tipo de commits

- `feat:` novas funcionalidades.
- `fix:` correção de bugs.
- `refactor:` refatoração ou performances (sem impacto em lógica).
- `style:` estilo ou formatação de código (sem impacto em lógica).
- `test:` testes.
- `doc:` documentação no código ou do repositório.
- `env:` CI/CD ou settings.
- `build:` build ou dependências.

## Como configurar o Integrador com o Moodle Local

### 1. Crie o ambiente no Integrador

Acesse **Ambientes > Adicionar**.

**Identificação**

- **Nome do ambiente:** Escolha um nome à sua escolha

**Integração**

- **Ativo?:** Marque este campo
- **URL:** `http://moodle`
- **Token:** `changeme`
- **Expressão regular:** `{campus}='ZL'`
- **Order:** `0´

---

### 2. Adicione uma solicitação no Integrador

Exemplo de solicitação (JSON):

```json
{
    "polo": null,
    "curso": {
        "id": 2039,
        "nome": "Curso de Formação Inicial e Continuada FIC em Português Brasileiro para Estrangeiros/as Intermediário",
        "codigo": "151036",
        "descricao": "FIC+ em Português Brasileiro para Estrangeiros/as Intermediário"
    },
    "turma": {
        "id": 56799,
        "codigo": "20251.1.151036.442.2E"
    },
    "alunos": [],
    "campus": {
        "id": 14,
        "sigla": "ZL",
        "descricao": "CAMPUS AVANÇADO NATAL-ZONA LESTE"
    },
    "diario": {
        "id": 148665,
        "sigla": "FIC.1101",
        "situacao": "Aberto",
        "descricao": "Seminários de Conclusão de Português Intermediário",
        "descricao_historico": "Seminários de Conclusão de Português Intermediário"
    },
    "componente": {
        "id": 14482,
        "tipo": 2,
        "sigla": "FIC.1101",
        "periodo": 1,
        "optativo": false,
        "descricao": "Seminários de Conclusão de Português Intermediário",
        "qtd_avaliacoes": 1,
        "descricao_historico": "Seminários de Conclusão de Português Intermediário"
    },
    "professores": [
        {
            "id": 164804,
            "nome": "Samuel de Carvalho Lima",
            "tipo": "Principal",
            "email": "samuel.lima@ifrn.edu.br",
            "login": "1885301",
            "status": "ativo",
            "email_secundario": "samclima@gmail.com"
        },
        {
            "id": 164805,
            "nome": "Bruno Rafael Costa Venancio da Silva",
            "tipo": "Principal",
            "email": "bruno.venancio@ifrn.edu.br",
            "login": "1813277",
            "status": "ativo",
            "email_secundario": "eurobrunoespanhol@gmail.com"
        }
    ]
}
```

No menu lateral, vá em **Solicitações > Adicionar**.

**Campos a preencher:**

- **Campus:** Selecione o campus que você criou anteriormente
- **Status:** Pode ser qualquer valor
- **Status code:** Pode ser qualquer valor
- **JSON recebido:** Cole seu JSON aqui

> 💡 Altere no JSON os dados do campo `"campus"` para corresponder ao seu campi cadastrado.

Os campos **JSON enviado** e **respondido** podem ser deixados em branco.

Clique em **Salvar**.

---

### 3. Reenvie a solicitação

Após salvar, localize a solicitação na lista e clique em **Reenviar** no canto direito.

Se tudo estiver configurado corretamente, os diários serão criados automaticamente no seu Moodle local.

### 4. Enviar via locust

locust -f integrador/example/carga.json --host=http://integrador --users 300 --spawn-rate 50
