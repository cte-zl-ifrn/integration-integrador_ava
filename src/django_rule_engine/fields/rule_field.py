"""Django field for rule-engine rules."""

import json
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import rule_engine

from .rule_widget import RuleWidget


class RuleField(models.TextField):
    """
    Campo Django para armazenar e validar regras do rule-engine.
    
    Args:
        example_data: Dicionário ou string JSON com dados de exemplo para validação.
                     Pode ser sobrescrito pelo usuário no admin.
        resolver: Opcional. Resolver customizado para rule-engine.
        **kwargs: Argumentos adicionais do TextField.
    
    Example:
        class MyModel(models.Model):
            rule = RuleField(
                verbose_name="Regra de validação",
                example_data={"age": 25, "status": "active"},
                help_text="Digite uma regra válida do rule-engine"
            )
    """
    
    description = _("Campo para regras do rule-engine")
    
    def __init__(self, *args, example_data=None, resolver=None, **kwargs):
        self.example_data = example_data
        self.resolver = resolver
        super().__init__(*args, **kwargs)
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.example_data is not None:
            kwargs['example_data'] = self.example_data
        if self.resolver is not None:
            kwargs['resolver'] = self.resolver
        return name, path, args, kwargs
    
    def formfield(self, **kwargs):
        """Retorna o formfield com o widget customizado."""
        # Prepara example_data para o widget
        example_data_json = None
        if self.example_data is not None:
            if isinstance(self.example_data, str):
                example_data_json = self.example_data
            else:
                example_data_json = json.dumps(self.example_data, indent=2)
        
        # Define o widget como padrão
        kwargs['widget'] = RuleWidget(example_data=example_data_json)
        
        return super().formfield(**kwargs)
    
    def validate(self, value, model_instance):
        """Valida se a regra é válida."""
        super().validate(value, model_instance)
        
        if not value:
            return
        
        try:
            # Tenta compilar a regra
            # O resolver deve ser passado no contexto, não no init do Rule
            rule_engine.Rule(value)
        except Exception as e:
            raise ValidationError(
                _('Regra inválida: %(error)s'),
                code='invalid_rule',
                params={'error': str(e)},
            )
    
    def to_python(self, value):
        """Converte o valor do banco para Python."""
        if value is None:
            return value
        return str(value)
    
    def get_prep_value(self, value):
        """Prepara o valor para salvar no banco."""
        if value is None:
            return value
        return str(value)
