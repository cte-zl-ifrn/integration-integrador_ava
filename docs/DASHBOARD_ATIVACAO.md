# 🚀 Dashboard Integrado - Instruções de Ativação

## Status Atual

✅ **View personalizada criada** (`admin_views.py`)  
✅ **Template customizado** (`admin/index.html`)  
✅ **Cache de 5 minutos configurado**  
✅ **Arquivo de registro criado** (`admin.py`)

## Como Ativar

### Opção 1: Automática (Recomendado)
O arquivo `admin.py` já está criado. Você só precisa garantir que ele seja importado. Adicione ao arquivo `__init__.py` do app:

```python
# src/dsgovbr/__init__.py
default_app_config = 'dsgovbr.apps.DSGovBRConfig'

# Importar admin para registrar a view customizada
from . import admin  # noqa
```

### Opção 2: Manual (via URLs)
Se preferir registrar via URLs, edite o `urls.py` principal:

```python
from dsgovbr.admin_views import admin_index_dashboard

urlpatterns = [
    # ... suas urls
    path('admin/', admin.site.urls),
]

# ANTES do admin.site.urls, substitua a view padrão:
admin.site.index = admin_index_dashboard
```

### Opção 3: Via Settings
Adicione ao `settings.py`:

```python
# Usar dashboard customizado
ADMIN_DASHBOARD = True
```

E em `apps.py`:

```python
class DSGovBRConfig(AppConfig):
    name = "dsgovbr"
    verbose_name = "DSGovBR"
    icon = "fa fa-edit"
    
    def ready(self):
        # Registrar dashboard customizado
        from django.contrib import admin
        from .admin_views import admin_index_dashboard
        admin.site.index = admin_index_dashboard
```

## Dados Exibidos

### Cards
1. **Ambientes de Integração**
   - Total de ambientes
   - Ativos
   - Com erros (expressão seletora inválida)

2. **Solicitações de Integração**
   - Últimas 24 horas
   - Sucesso
   - Falhas
   - Processando

3. **Coortes**
   - Total de coortes
   - Ativas
   - Inativas
   - Vínculos de enrolment

4. **Papéis**
   - Total de papéis
   - Ativos
   - Inativos

5. **Usuários e Grupos**
   - Total de usuários
   - Usuários ativos
   - Total de grupos

6. **Taxa de Sucesso**
   - Percentual de integrações bem-sucedidas
   - Total de solicitações processadas

7. **Ações Rápidas**
   - Links diretos para administração

## Cache

- **Duração**: 5 minutos (300 segundos)
- **Implementação**: `@cache_page(60 * 5)`
- **Benefício**: Reduz carga no banco de dados durante picos

### Limpar Cache Manualmente
```bash
python manage.py shell
```

```python
from django.core.cache import cache
cache.clear()
```

## Verificar se está funcionando

1. Acesse `/admin/`
2. Você deverá ver o novo dashboard
3. Os dados serão cacheados por 5 minutos
4. Após 5 minutos, os dados são recarregados do banco

## Troubleshooting

### Dashboard não aparece?
- Verifique se `admin.py` está sendo importado
- Confira se a view está registrada: `print(admin.site.index)`

### Dados não atualizam?
- O cache está funcionando (aguarde 5 minutos ou limpe)
- Verifique se há erros no console Django

### Erro ao carregar modelos?
- Verifique se os apps `integrador` e `coorte` estão em `INSTALLED_APPS`
- Confira permissões de staff_member

## Arquivo de Referência

Estrutura criada:
```
dsgovbr/
├── admin.py          ← Novo (registra dashboard)
├── admin_views.py    ← Novo (lógica do dashboard)
├── apps.py           ← Existente
├── context_processors.py
├── templates/
│   └── admin/
│       └── index.html ← Atualizado (novo design)
└── __init__.py       ← Editar (importar admin)
```

---

Pronto! Seus dados estão sendo apresentados com cache de 5 minutos. 🎉
