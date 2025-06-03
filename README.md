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

## Como configurar o Integrador com o Moodle Local

### 1. Crie o ambiente no Integrador

Acesse **Ambientes > Adicionar**.

**Identificação**
- **Nome do ambiente:** Escolha um nome à sua escolha

**Integração**
- **Ativo?:** Marque este campo  
- **URL:** `http://moodle`  
- **Token:** `changeme`

**CAMPI**
- **ID do campus no SUAP:** Escolha um número (apenas identificador interno)  
- **Sigla do campus:** Defina uma sigla para identificação  
- **Ativo?:** Marque este campo  

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

```css
/* add ao css do admin */
.submit-row [type="submit"], .submit-row a {
    border: 1px solid rgb(var(--color-base-200));
    padding: 4px 8px;
    border-radius: 8px;
    line-height: 100%;
    margin: 0;
    height: auto !important;
}
```