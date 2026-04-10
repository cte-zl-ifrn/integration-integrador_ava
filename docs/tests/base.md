📋 Cobertura dos Testes

1. ActiveMixinTestCase
    - ✅ Ícone quando active=True
    - ✅ Ícone quando active=False
    - ✅ Verificação de que active_icon é uma property
2. BaseChangeListTestCase
    - ✅ URL de resultado usa a view URL customizada
3. BasicModelAdminTestCase
    - ✅ get_changelist retorna BaseChangeList
    - ✅ get_urls inclui URL de visualização
    - ✅ preview_view renderiza formulário readonly
    - ✅ preview_view requer permissão
    - ✅ preview_view define request.in_view_mode
    - ✅ get_inline_formsets desabilita edição em modo visualização
    - ✅ get_inline_formsets permite edição fora do modo visualização
4. BaseModelAdminTestCase
    - ✅ Herança de BasicModelAdmin
    - ✅ Inclusão de ImportExportMixin
    - ✅ Inclusão de ExportActionMixin
5. DateTimeWidgetTestCase
    - ✅ Formato de data/hora padrão
    - ✅ Widget de data/hora criado
6. IntegrationTestCase
    - ✅ Fluxo completo do BasicModelAdmin
    - ✅ Integração do ActiveMixin com admin
7. EdgeCasesTestCase
    - ✅ preview_view com objeto inexistente
    - ✅ get_inline_formsets com listas vazias
    - ✅ active_icon com valores não-booleanos
