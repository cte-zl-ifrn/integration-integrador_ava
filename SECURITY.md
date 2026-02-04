# Política de Segurança

Obrigado por ajudar a manter este projeto e sua comunidade mais **segura**.

Este documento descreve como relatar vulnerabilidades de segurança, quais versões são suportadas e quais são as nossas práticas gerais de segurança.

## Versões suportadas

Versões deste projeto que estão atualmente recebendo atualizações de segurança.

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |

## Relato de vulnerabilidades

Se você encontrar uma possível vulnerabilidade de segurança no projeto, **não** abra um issue público.

Use um destes canais privados:

- E‑mail: dead.zl@ifrn.edu.br
- Título sugerido: "[SEGURANÇA] Descrição resumida da vulnerabilidade"

Ao relatar, inclua sempre:

- Link para o repositório/projeto afetado.
- Se o problema já foi discutido publicamente em algum lugar (issue, fórum, etc.).
- Passo a passo para reproduzir o problema.
- Qualquer código de prova de conceito (PoC).
- Versão do Django, versão do projeto e ambiente (SO, banco de dados, etc.).

Vamos acusar recebimento em até 3 dias úteis e manter você informado sobre o andamento da correção.

## Política de divulgação

Nossa política é seguir divulgação responsável:

1. Investigamos e confirmamos o problema.
2. Preparamos um patch e, se necessário, uma nova versão.
3. Comunicamos mantenedores de dependências relevantes, se aplicável.
4. Combinamos com você uma data de divulgação, levando em conta:
   - Gravidade do problema.
   - Tempo necessário para os usuários aplicarem correções.
5. Publicamos:
   - Release com correção.
   - Notas de versão destacando o impacto de segurança.
   - Aviso público (issue, página do projeto ou changelog).

Pedimos, se possível, um prazo de 14 a 30 dias entre o relato e a divulgação pública.

## Escopo

Esta política cobre:

- Código deste repositório (aplicação Django, APIs, comandos de gestão).
- Configuração de segurança padrão documentada aqui.
- Dependências diretamente gerenciadas pelo projeto (por exemplo, `requirements.txt` ou `pyproject.toml`).

Não estão incluídos:

- Erros em bibliotecas de terceiros (relate diretamente aos projetos originais).
- Problemas na infraestrutura onde o projeto é implantado (servidores, proxies, DNS, etc.).

## Versões suportadas

Seguindo a política oficial do Django de suporte de segurança para versões LTS e estáveis, priorizamos correções para: [web:14]

- A versão principal atual do projeto.
- Versão anterior major/minor, se ainda em uso ativo.
- Qualquer versão LTS explicitamente marcada na documentação do projeto.

Versões antigas ou descontinuadas podem não receber correções de segurança. Recomendamos sempre atualizar para uma versão suportada.

## Boas práticas específicas de Django

Recomendamos que deploys baseados neste projeto sigam práticas mínimas de segurança para Django: [web:14]

- Manter `DEBUG = False` em produção.
- Proteger o `SECRET_KEY` via variáveis de ambiente ou serviço de segredos.
- Usar HTTPS com `SECURE_SSL_REDIRECT`, `CSRF_COOKIE_SECURE` e `SESSION_COOKIE_SECURE`.
- Configurar `ALLOWED_HOSTS` adequadamente.
- Manter o Django e dependências atualizados com as últimas correções de segurança.

Se você identificar qualquer ponto da documentação ou configuração padrão deste projeto que possa induzir a práticas inseguras, considere isso como um problema de segurança e reporte pelos canais acima.

## Agradecimentos

Agradecemos a todos os pesquisadores e usuários que dedicam tempo para relatar vulnerabilidades de forma responsável. Seu esforço ajuda a manter o ecossistema de software livre mais **resiliente** e confiável.


## Reporting a Vulnerability

Use this section to tell people how to report a vulnerability.

Tell them where to go, how often they can expect to get an update on a
reported vulnerability, what to expect if the vulnerability is accepted or
declined, etc.
