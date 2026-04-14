# O que é enviado do Suap para o Integrador AVA

Cada sincronização envia um diário, nesta vem as informações:

| Objeto      | Atributos |
| ----------- | --------- |
| Campus      | id, sigla, descricao |
| Curso       | id, nome, codigo, descricao |
| Turma       | id, codigo |
| Componente  | id, tipo, sigla, periodo, optativo, descricao, qtd_avaliacoes, descricao_historico |
| Diário      | id, sigla, situacao, descricao, descricao_historico |
| Professores | id, nome, tipo, email, login, status, email_secundario |
| Alunos      | id, nome, polo, email, programa, situacao, matricula, situacao_diario, ativo, email_secundario |

> Adicionalmente, para cada curso do diário é sincronizada a **Sala de coordenação de curso**
