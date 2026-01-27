#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar a funcionalidade de captura de erros CSRF no Sentry.

Este script simula diferentes cenários de falha CSRF para validar que:
1. Os erros são capturados e enviados para o Sentry
2. As respostas apropriadas são retornadas (JSON ou HTML)
3. As informações corretas são capturadas

Uso:
    python test_csrf_monitoring.py [URL_BASE]

Exemplos:
    python test_csrf_monitoring.py http://localhost:8091
    python test_csrf_monitoring.py https://integrador.dev.ifrn.edu.br
"""

import sys
import requests
import json
from typing import Dict, Any


def test_csrf_error_api_endpoint(base_url: str) -> None:
    """
    Testa erro CSRF em endpoint de API.
    
    Args:
        base_url: URL base do servidor
    """
    print("\n" + "="*70)
    print("Teste 1: Erro CSRF em endpoint de API")
    print("="*70)
    
    url = f"{base_url}/api/enviar_diarios/"
    data = {
        "campus": {"sigla": "CNAT"},
        "turma": {"codigo": "20241.1.123456.1M"},
        "diario": {"id": 999, "tipo": "regular"}
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "TestScript/1.0 (CSRF Test)"
    }
    
    print(f"URL: {url}")
    print(f"Dados: {json.dumps(data, indent=2)}")
    
    try:
        # Força erro CSRF não incluindo o token CSRF
        # O endpoint /api/enviar_diarios/ está na lista de isentos, 
        # então vamos testar um endpoint diferente
        url_protected = f"{base_url}/admin/login/"
        response = requests.post(
            url_protected,
            json=data,
            headers=headers,
            allow_redirects=False
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 403:
            print("✓ Erro CSRF capturado com sucesso!")
            try:
                response_data = response.json()
                print(f"Resposta JSON: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Resposta HTML (primeiros 500 chars):\n{response.text[:500]}")
        else:
            print(f"⚠ Status inesperado: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Erro na requisição: {e}")


def test_csrf_error_form_submission(base_url: str) -> None:
    """
    Testa erro CSRF em submissão de formulário.
    
    Args:
        base_url: URL base do servidor
    """
    print("\n" + "="*70)
    print("Teste 2: Erro CSRF em submissão de formulário")
    print("="*70)
    
    url = f"{base_url}/admin/login/"
    data = {
        "username": "admin",
        "password": "test123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html",
        "User-Agent": "Mozilla/5.0 (Test Browser)",
        "Referer": "https://external-site.com"
    }
    
    print(f"URL: {url}")
    print(f"Dados: {data}")
    
    try:
        # Tenta submeter sem token CSRF
        response = requests.post(
            url,
            data=data,
            headers=headers,
            allow_redirects=False
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✓ Erro CSRF capturado com sucesso!")
            print(f"Resposta HTML (primeiros 500 chars):\n{response.text[:500]}")
            
            # Verifica se o template customizado está sendo usado
            if "403" in response.text and "CSRF" in response.text:
                print("✓ Template customizado de erro CSRF detectado!")
        else:
            print(f"⚠ Status inesperado: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Erro na requisição: {e}")


def test_csrf_with_invalid_token(base_url: str) -> None:
    """
    Testa erro CSRF com token inválido.
    
    Args:
        base_url: URL base do servidor
    """
    print("\n" + "="*70)
    print("Teste 3: Erro CSRF com token inválido")
    print("="*70)
    
    url = f"{base_url}/admin/login/"
    data = {
        "username": "admin",
        "password": "test123",
        "csrfmiddlewaretoken": "INVALID_TOKEN_12345"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": "INVALID_TOKEN_12345",
        "User-Agent": "TestScript/1.0",
        "Referer": base_url
    }
    
    print(f"URL: {url}")
    print(f"Token CSRF: {data['csrfmiddlewaretoken']}")
    
    try:
        response = requests.post(
            url,
            data=data,
            headers=headers,
            allow_redirects=False
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✓ Erro CSRF com token inválido capturado!")
        else:
            print(f"⚠ Status inesperado: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Erro na requisição: {e}")


def test_csrf_with_missing_referer(base_url: str) -> None:
    """
    Testa erro CSRF com referer ausente.
    
    Args:
        base_url: URL base do servidor
    """
    print("\n" + "="*70)
    print("Teste 4: Erro CSRF com referer ausente")
    print("="*70)
    
    url = f"{base_url}/admin/login/"
    data = {"username": "admin", "password": "test"}
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "TestScript/1.0",
        # Intencionalmente não incluindo Referer
    }
    
    print(f"URL: {url}")
    print("Referer: (ausente)")
    
    try:
        response = requests.post(
            url,
            data=data,
            headers=headers,
            allow_redirects=False
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✓ Erro CSRF com referer ausente capturado!")
        else:
            print(f"⚠ Status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Erro na requisição: {e}")


def print_summary() -> None:
    """Imprime resumo das instruções."""
    print("\n" + "="*70)
    print("RESUMO E PRÓXIMOS PASSOS")
    print("="*70)
    print("""
Os testes acima simulam diferentes cenários de erro CSRF.

Para verificar se os erros foram capturados no Sentry:

1. Acesse o dashboard do Sentry: https://sentry.ifrn.edu.br/organizations/sentry/issues/?project=20&statsPeriod=24h
2. Navegue até o projeto configurado
3. Filtre por tag: error_type:csrf_failure
4. Verifique os detalhes de cada erro capturado

Informações que devem aparecer no Sentry:
- Path da requisição
- Método HTTP
- User Agent
- IP do cliente
- Referer (se presente)
- Razão da falha CSRF
- Informações do usuário (se autenticado)

Tags configuradas:
- error_type: csrf_failure
- csrf_reason: <razão específica>

Nível: warning
    """)


def main():
    """Função principal."""
    if len(sys.argv) < 2:
        print("Uso: python test_csrf_monitoring.py <URL_BASE>")
        print("Exemplo: python test_csrf_monitoring.py http://localhost:8000")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("="*70)
    print("TESTES DE MONITORAMENTO DE ERROS CSRF")
    print("="*70)
    print(f"URL Base: {base_url}")
    print(f"Certifique-se de que:")
    print(f"  1. O servidor está rodando em {base_url}")
    print(f"  2. O Sentry está configurado (SENTRY_DNS definido)")
    print(f"  3. Você tem acesso ao dashboard do Sentry")
    
    input("\nPressione ENTER para iniciar os testes...")
    
    # Executa os testes
    test_csrf_error_api_endpoint(base_url)
    test_csrf_error_form_submission(base_url)
    test_csrf_with_invalid_token(base_url)
    test_csrf_with_missing_referer(base_url)
    
    # Imprime resumo
    print_summary()
    
    print("\n✓ Testes concluídos!")
    print("Verifique o Sentry para confirmar que os erros foram capturados.")


if __name__ == "__main__":
    main()
