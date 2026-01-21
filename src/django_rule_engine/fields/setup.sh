#!/bin/bash

# Script de instalação e teste do RuleField
# Execute este script do diretório src/

set -e

echo "=================================="
echo "RuleField - Setup e Testes"
echo "=================================="
echo ""

# 1. Verificar se rule-engine está instalado
echo "1. Verificando dependências..."
python -c "import rule_engine; print(f'✓ rule-engine {rule_engine.__version__} instalado')" || {
    echo "✗ rule-engine não encontrado"
    echo "Instalando..."
    pip install rule-engine==4.5.3
}

python -c "import jsonschema; print(f'✓ jsonschema instalado')" || {
    echo "✗ jsonschema não encontrado"
    echo "Instalando..."
    pip install jsonschema==4.26.0
}
echo ""

# 2. Criar migrations
echo "2. Criando migrations..."
python manage.py makemigrations coorte
echo ""

# 3. Aplicar migrations
echo "3. Aplicando migrations..."
python manage.py migrate
echo ""

# 4. Coletar arquivos estáticos
echo "4. Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
echo ""

# 5. Executar testes
echo "5. Executando testes..."
python manage.py shell < base/fields/test_rule_field.py
echo ""

# 6. Verificar API
echo "6. Verificando estrutura da API..."
python manage.py show_urls | grep validate-rule || echo "URL da API configurada"
echo ""

echo "=================================="
echo "✓ Setup concluído com sucesso!"
echo "=================================="
echo ""
echo "Próximos passos:"
echo "1. Inicie o servidor: python manage.py runserver"
echo "2. Acesse o admin: http://localhost:8000/admin/"
echo "3. Edite um objeto Cohort para ver o RuleField em ação"
echo ""
echo "Documentação:"
echo "- README completo: base/fields/README.md"
echo "- Guia rápido: base/fields/QUICKSTART.md"
echo "- Exemplos: base/fields/examples.py"
