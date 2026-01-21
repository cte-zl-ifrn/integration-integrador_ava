"""Widget Django para edição de regras do rule-engine."""

import json
from django import forms
from django.utils.safestring import mark_safe
from django.conf import settings
from django_json_widget.widgets import JSONEditorWidget


class RuleWidget(forms.Textarea):
    """
    Widget customizado para editar regras do rule-engine.
    
    Fornece:
    - Editor de código com syntax highlighting (CodeMirror)
    - Campo para JSON de exemplo (editável pelo usuário)
    - Validação dinâmica no frontend
    - Feedback visual do resultado da regra
    """
    
    template_name = 'widgets/rule_widget.html'
    
    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css',
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/material.min.css',
                'rule_widget/rule_widget.css',
                'rule_widget/rule_widget_highlighting.css',  # Estilos customizados de highlighting
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js',
            'rule_widget/codemirror-rule-engine.js',  # Modo customizado para rule-engine
            'rule_widget/rule_widget.js',
        )
    
    def __init__(self, example_data=None, attrs=None):
        """
        Inicializa o widget.
        
        Args:
            example_data: JSON string com dados de exemplo
            attrs: Atributos HTML adicionais
        """
        self.example_data = example_data or '{}'
        super().__init__(attrs)
    
    def get_context(self, name, value, attrs):
        """Adiciona contexto extra para o template."""
        context = super().get_context(name, value, attrs)
        
        # Formata o example_data para exibição
        try:
            if isinstance(self.example_data, str):
                example_obj = json.loads(self.example_data)
            else:
                example_obj = self.example_data
            formatted_example = json.dumps(example_obj, indent=2)
        except (json.JSONDecodeError, TypeError):
            formatted_example = self.example_data
        
        # Cria um JSONEditorWidget para o campo de exemplo
        json_widget = JSONEditorWidget(height='120px')  # ~5 linhas
        json_widget_name = f"{name}_example_data"
        json_widget_attrs = {
            'id': f"{attrs.get('id', name)}_example_data",
            'class': 'example-data-json-editor',
        }
        json_widget_html = json_widget.render(json_widget_name, formatted_example, json_widget_attrs)
        
        context['widget'].update({
            'example_data': formatted_example,
            'field_id': attrs.get('id', name),
            'json_widget_html': mark_safe(json_widget_html),
            'json_widget_media': json_widget.media,
        })
        
        return context
    
    def format_value(self, value):
        """Formata o valor para exibição no widget."""
        if value is None:
            return ''
        return str(value)
