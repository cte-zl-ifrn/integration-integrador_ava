#!/usr/bin/env python
"""
Script de teste do RuleField.

Execute com:
    python manage.py shell < base/fields/test_rule_field.py

Ou no shell do Django:
    from django_rule_engine.fields.test_rule_field import test_all
    test_all()
"""

import json


def test_rule_compilation():
    """Testa compilação básica de regras."""
    import rule_engine
    
    print("=" * 60)
    print("TESTE 1: Compilação de Regras")
    print("=" * 60)
    
    regras = [
        "age >= 18",
        'status == "active"',
        "age >= 18 and status == 'active'",
        '(price > 100 or quantity >= 5) and customer_type == "premium"',
        '"@ifrn.edu.br" in email',
        "len(name) > 3",
    ]
    
    for regra in regras:
        try:
            rule = rule_engine.Rule(regra)
            print(f"✓ OK: {regra}")
        except Exception as e:
            print(f"✗ ERRO: {regra}")
            print(f"  Mensagem: {e}")
    
    print()


def test_rule_evaluation():
    """Testa avaliação de regras com dados."""
    import rule_engine
    
    print("=" * 60)
    print("TESTE 2: Avaliação de Regras")
    print("=" * 60)
    
    casos = [
        {
            "regra": "age >= 18",
            "dados": {"age": 25},
            "esperado": True
        },
        {
            "regra": "age >= 18",
            "dados": {"age": 15},
            "esperado": False
        },
        {
            "regra": 'status == "active"',
            "dados": {"status": "active"},
            "esperado": True
        },
        {
            "regra": 'age >= 18 and status == "active"',
            "dados": {"age": 25, "status": "active"},
            "esperado": True
        },
        {
            "regra": 'age >= 18 and status == "active"',
            "dados": {"age": 15, "status": "active"},
            "esperado": False
        },
        {
            "regra": '"@ifrn.edu.br" in email',
            "dados": {"email": "usuario@ifrn.edu.br"},
            "esperado": True
        },
        {
            "regra": "len(name) > 3",
            "dados": {"name": "João Silva"},
            "esperado": True
        },
        {
            "regra": "(price * quantity) > 1000",
            "dados": {"price": 100, "quantity": 12},
            "esperado": True
        },
    ]
    
    for i, caso in enumerate(casos, 1):
        regra = rule_engine.Rule(caso["regra"])
        resultado = regra.matches(caso["dados"])
        
        status = "✓" if resultado == caso["esperado"] else "✗"
        print(f"{status} Caso {i}:")
        print(f"  Regra: {caso['regra']}")
        print(f"  Dados: {caso['dados']}")
        print(f"  Resultado: {resultado} (esperado: {caso['esperado']})")
        print()


def test_field_validation():
    """Testa validação do campo Django."""
    from django_rule_engine.fields import RuleField
    from django.core.exceptions import ValidationError
    
    print("=" * 60)
    print("TESTE 3: Validação do Campo Django")
    print("=" * 60)
    
    field = RuleField()
    
    # Regras válidas
    regras_validas = [
        "age >= 18",
        'status == "active"',
        "age >= 18 and status == 'active'",
    ]
    
    print("Testando regras VÁLIDAS:")
    for regra in regras_validas:
        try:
            field.validate(regra, None)
            print(f"✓ OK: {regra}")
        except ValidationError as e:
            print(f"✗ ERRO (inesperado): {regra}")
            print(f"  Mensagem: {e}")
    
    print()
    
    # Regras inválidas
    regras_invalidas = [
        "age >>= 18",  # Operador inválido
        "age == ",  # Incompleta
        "status = 'active'",  # Usa = ao invés de ==
    ]
    
    print("Testando regras INVÁLIDAS:")
    for regra in regras_invalidas:
        try:
            field.validate(regra, None)
            print(f"✗ ERRO (deveria falhar): {regra}")
        except ValidationError as e:
            print(f"✓ OK (erro esperado): {regra}")
            print(f"  Mensagem: {e}")
    
    print()


def test_api_simulation():
    """Simula chamada à API de validação."""
    import rule_engine
    
    print("=" * 60)
    print("TESTE 4: Simulação da API")
    print("=" * 60)
    
    request_body = {
        "rule": "age >= 18 and status == 'active'",
        "data": {
            "age": 25,
            "status": "active"
        }
    }
    
    print(f"Request Body:")
    print(json.dumps(request_body, indent=2))
    print()
    
    try:
        rule = rule_engine.Rule(request_body["rule"])
        result = rule.matches(request_body["data"])
        
        response = {
            "valid": True,
            "result": result,
            "matches": result,
            "rule": request_body["rule"],
            "data": request_body["data"]
        }
        
        print("Response:")
        print(json.dumps(response, indent=2))
        print()
        print("✓ API simulada com sucesso!")
    
    except Exception as e:
        response = {
            "valid": False,
            "error": str(e)
        }
        print("Response (ERRO):")
        print(json.dumps(response, indent=2))
        print()
        print("✗ Erro na simulação da API")
    
    print()


def test_real_world_examples():
    """Testa exemplos do mundo real."""
    import rule_engine
    
    print("=" * 60)
    print("TESTE 5: Exemplos do Mundo Real")
    print("=" * 60)
    
    exemplos = [
        {
            "nome": "Validação de Matrícula",
            "regra": 'idade >= 16 and nivel_ensino == "medio" and aprovado == true',
            "dados": {
                "idade": 18,
                "nivel_ensino": "medio",
                "aprovado": True
            },
            "esperado": True
        },
        {
            "nome": "Desconto para Cliente Premium",
            "regra": '(quantidade >= 10 or valor_total > 1000) and tipo_cliente == "premium"',
            "dados": {
                "quantidade": 12,
                "valor_total": 500,
                "tipo_cliente": "premium"
            },
            "esperado": True
        },
        {
            "nome": "Email Institucional",
            "regra": '"@ifrn.edu.br" in email and ativo == true',
            "dados": {
                "email": "joao.silva@ifrn.edu.br",
                "ativo": True
            },
            "esperado": True
        },
        {
            "nome": "Acesso de Administrador",
            "regra": 'is_admin == true or (departamento == "TI" and nivel_acesso >= 5)',
            "dados": {
                "is_admin": False,
                "departamento": "TI",
                "nivel_acesso": 7
            },
            "esperado": True
        },
    ]
    
    for exemplo in exemplos:
        print(f"\n{exemplo['nome']}:")
        print(f"  Regra: {exemplo['regra']}")
        print(f"  Dados: {json.dumps(exemplo['dados'], indent=4)}")
        
        try:
            rule = rule_engine.Rule(exemplo["regra"])
            resultado = rule.matches(exemplo["dados"])
            
            status = "✓" if resultado == exemplo["esperado"] else "✗"
            print(f"  {status} Resultado: {resultado} (esperado: {exemplo['esperado']})")
        
        except Exception as e:
            print(f"  ✗ ERRO: {e}")
    
    print()


def test_all():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("INICIANDO TESTES DO RULEFIELD")
    print("=" * 60 + "\n")
    
    try:
        test_rule_compilation()
        test_rule_evaluation()
        test_field_validation()
        test_api_simulation()
        test_real_world_examples()
        
        print("=" * 60)
        print("TODOS OS TESTES CONCLUÍDOS!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_all()
