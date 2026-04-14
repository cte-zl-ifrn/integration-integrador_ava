# Instalação e configuração

Instalação e configuração em 3 passos para o **Suap**, usando o plugin `local_suap`.

1. **No Moodle**: Em cada Moodle a ser integrado instale o plugin `local_suap`, acesse a página de configurações do plugin e copie o valor da configuração `sync_up_auth_token`.
2. **No Integrador AVA**: Para cada Moodle a ser integrado cadastre o **Ambiente** e informe: URL raiz do Moodle, valor copiado de `sync_up_auth_token` e regra de seleção, depois clique em testar. Cadastre um token de autenticação para o Suap.
3. **No SUAP**: Na interface de configurações informe o token cadastrado no **Integrador AVA** e a URL de integração, algo como https://ava.ifbr.edu.br/api/moodle_suap/.

> Mais dúvidas sobre instalação do **Moodle**, **local_suap**, **Suap** ou **Integrador AVA** leia as respectivas documentações.