/**
 * Rule Widget - Editor de regras do rule-engine com validação dinâmica
 */

(function() {
    'use strict';
    
    // Inicializa quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRuleWidgets);
    } else {
        initRuleWidgets();
    }
    
    function initRuleWidgets() {
        const containers = document.querySelectorAll('.rule-widget-container');
        containers.forEach(container => {
            new RuleWidget(container);
        });
    }
    
    class RuleWidget {
        constructor(container) {
            this.container = container;
            this.fieldId = container.dataset.fieldId;
            this.ruleTextarea = container.querySelector('.rule-editor-textarea');
            // O JSONEditorWidget cria um textarea com sufixo _textarea
            this.exampleDataTextarea = container.querySelector(`#${this.fieldId}_example_data_textarea`);
            this.validateBtn = container.querySelector('.btn-validate');
            this.resultDiv = container.querySelector('.validation-result');
            this.resultContent = container.querySelector('.result-content');
            this.closeResultBtn = container.querySelector('.btn-close-result');
            
            this.validationTimeout = null;
            this.validationDelay = 300; // 0.3 segundos
            
            this.initCodeMirror();
            this.initJSONEditor();
            this.attachEventListeners();
        }
        
        initCodeMirror() {
            // Inicializa CodeMirror para o editor de regras
            if (typeof CodeMirror !== 'undefined') {
                this.ruleEditor = CodeMirror.fromTextArea(this.ruleTextarea, {
                    mode: 'rule-engine', // Modo customizado para sintaxe do rule-engine
                    theme: 'material',
                    lineNumbers: true,
                    lineWrapping: true,
                    indentUnit: 4,
                    tabSize: 4,
                    extraKeys: {
                        'Ctrl-Enter': () => this.validateRule(),
                        'Cmd-Enter': () => this.validateRule()
                    }
                });
                
                // Validação automática ao digitar (com debounce)
                this.ruleEditor.on('change', () => {
                    this.scheduleValidation();
                });
                
                // Validação ao perder foco
                this.ruleEditor.on('blur', () => {
                    this.validateRule();
                });
            }
        }
        
        initJSONEditor() {
            // O JSONEditorWidget já inicializa o editor automaticamente
            // Apenas precisamos adicionar listeners para validação
            if (!this.exampleDataTextarea) {
                console.warn('RuleWidget: textarea do JSONEditor não encontrado');
                return;
            }
            
            // Aguarda o JSONEditorWidget ser inicializado
            setTimeout(() => {
                // Tenta encontrar o editor JSONEditor
                const jsonEditorContainer = this.exampleDataTextarea.parentElement;
                
                // Observa mudanças no textarea (o JSONEditorWidget atualiza o textarea)
                const observer = new MutationObserver(() => {
                    this.scheduleValidation();
                });
                
                observer.observe(this.exampleDataTextarea, {
                    attributes: true,
                    characterData: true,
                    subtree: true
                });
                
                // Listener direto no textarea também
                this.exampleDataTextarea.addEventListener('change', () => {
                    this.scheduleValidation();
                });
                
                this.exampleDataTextarea.addEventListener('blur', () => {
                    this.validateRule();
                });
                
                // Se o textarea estiver vazio, inicializa com {}
                if (!this.exampleDataTextarea.value || this.exampleDataTextarea.value.trim() === '') {
                    this.exampleDataTextarea.value = '{}';
                }
            }, 500);
        }
        
        scheduleValidation() {
            // Cancela validação anterior se existir
            if (this.validationTimeout) {
                clearTimeout(this.validationTimeout);
            }
            
            // Agenda nova validação após o delay
            this.validationTimeout = setTimeout(() => {
                this.validateRule();
            }, this.validationDelay);
        }
        
        attachEventListeners() {
            this.validateBtn.addEventListener('click', () => this.validateRule());
            this.closeResultBtn.addEventListener('click', () => this.hideResult());
        }
        
        async validateRule() {
            const rule = this.getRuleValue();
            const exampleData = this.getExampleDataValue();
            
            // Se a regra estiver vazia, limpa o resultado
            if (!rule.trim()) {
                this.hideResult();
                return;
            }
            
            let parsedData;
            try {
                parsedData = JSON.parse(exampleData);
            } catch (e) {
                this.showResult('error', `Erro ao parsear JSON de exemplo:\n${e.message}`);
                return;
            }
            
            this.setLoading(true);
            
            try {
                const response = await fetch('/api/validate-rule/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({
                        rule: rule,
                        data: parsedData
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    if (result.valid) {
                        const output = this.formatValidationSuccess(result);
                        // Se a condição for falsa, usa warning (amarelo), senão success (verde)
                        const resultType = result.matches === false ? 'warning' : 'success';
                        this.showResult(resultType, output);
                    } else {
                        this.showResult('error', `Erro de validação:\n${result.error}`);
                    }
                } else {
                    this.showResult('error', `Erro do servidor:\n${result.error || 'Erro desconhecido'}`);
                }
            } catch (error) {
                // Não mostra erro de rede se for apenas timeout/cancelamento
                if (error.name !== 'AbortError') {
                    this.showResult('error', `Erro de rede:\n${error.message}`);
                }
            } finally {
                this.setLoading(false);
            }
        }
        
        formatValidationSuccess(result) {
            let output = `✓ Regra válida e compilada com sucesso!\n\n`;
            output += `Resultado da avaliação: ${result.result}\n\n`;
            
            if (result.matches !== undefined) {
                output += `Condição: ${result.matches ? 'VERDADEIRA' : 'FALSA'}`;
            }
            
            return output;
        }
        
        getRuleValue() {
            return this.ruleEditor ? this.ruleEditor.getValue() : this.ruleTextarea.value;
        }
        
        getExampleDataValue() {
            // O JSONEditorWidget armazena o valor no textarea hidden
            if (!this.exampleDataTextarea) {
                return '{}';
            }
            
            const value = this.exampleDataTextarea.value;
            
            // Se o valor estiver vazio, undefined, ou null, retorna {}
            if (!value || value.trim() === '') {
                return '{}';
            }
            
            return value;
        }
        
        showResult(type, message) {
            this.resultDiv.className = `validation-result ${type}`;
            this.resultContent.textContent = message;
            this.resultDiv.style.display = 'block';
        }
        
        hideResult() {
            this.resultDiv.style.display = 'none';
        }
        
        setLoading(loading) {
            if (loading) {
                this.container.classList.add('loading');
                this.validateBtn.disabled = true;
            } else {
                this.container.classList.remove('loading');
                this.validateBtn.disabled = false;
            }
        }
        
        getCsrfToken() {
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];
            return cookieValue || '';
        }
    }
    
    // Exporta para uso global se necessário
    window.RuleWidget = RuleWidget;
})();
