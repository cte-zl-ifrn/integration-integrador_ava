# Integrador integrador SUAP-Moodle

O Integrador é um Middleware que integra o SUAP ao Moodle.

> Neste projeto usamos Git, Python 3.12+, [Docker](https://docs.docker.com/engine/install/) e o [Docker Compose Plugin](https://docs.docker.com/compose/install/compose-plugin/#:~:text=%20Install%20the%20plugin%20manually%20%F0%9F%94%97%20%201,of%20Compose%20you%20want%20to%20use.%20More%20). O setup foi todo testado usando o Linux (inclusive WSL2) e Mac OS.

## Como funciona

...

As variáveis de ambiente no SUAP têm as seguintes definições:

-   `VARNAME` - ...

## Como implantar

...

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

## Screenshots

...

## Tipo de commits

-   `feat:` novas funcionalidades.
-   `fix:` correção de bugs.
-   `refactor:` refatoração ou performances (sem impacto em lógica).
-   `style:` estilo ou formatação de código (sem impacto em lógica).
-   `test:` testes.
-   `doc:` documentação no código ou do repositório.
-   `env:` CI/CD ou settings.
-   `build:` build ou dependências.
