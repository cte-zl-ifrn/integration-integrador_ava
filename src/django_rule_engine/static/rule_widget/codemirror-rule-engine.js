/**
 * CodeMirror mode for rule-engine syntax
 * Based on: https://zerosteiner.github.io/rule-engine/syntax.html
 */

(function(mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
        mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
        define(["../../lib/codemirror"], mod);
    else // Plain browser env
        mod(CodeMirror);
})(function(CodeMirror) {
    "use strict";

    CodeMirror.defineMode("rule-engine", function() {
        // Keywords
        var keywords = {
            "and": true,
            "or": true,
            "not": true,
            "in": true,
            "true": true,
            "false": true,
            "null": true
        };

        // Built-in functions
        var builtinFunctions = {
            "float": true,
            "int": true,
            "str": true,
            "len": true,
            "abs": true,
            "all": true,
            "any": true,
            "bool": true,
            "dir": true,
            "max": true,
            "min": true,
            "pow": true,
            "round": true,
            "sum": true
        };

        // Operators
        var operators = /[+\-*\/%&|^~<>=!]/;

        function tokenBase(stream, state) {
            // Whitespace
            if (stream.eatSpace()) return null;

            var ch = stream.peek();

            // Comments (se houver suporte futuro)
            if (ch === "#") {
                stream.skipToEnd();
                return "comment";
            }

            // Strings - prioridade alta
            if (ch === '"' || ch === "'") {
                var quote = ch;
                stream.next(); // Consome a aspas inicial
                var escaped = false;
                
                while (!stream.eol()) {
                    var next = stream.next();
                    if (next === quote && !escaped) {
                        // Encontrou a aspas final
                        return "string";
                    }
                    escaped = !escaped && next === "\\";
                }
                
                // String não fechada (fim da linha)
                return "string";
            }

            // Numbers
            if (/\d/.test(ch)) {
                stream.match(/^[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?/);
                return "number";
            }

            // Operators multi-char (devem vir antes de single-char)
            if (stream.match(/^(==|!=|<=|>=|=~|!~|<<|>>|\/\/|\*\*)/)) {
                return "operator";
            }

            // Operador '=' sozinho é ERRO (não existe no rule-engine)
            if (ch === '=' && stream.peek() === '=') {
                // Já foi tratado acima
            } else if (ch === '=') {
                stream.next();
                return "error";
            }

            // Outros operators válidos
            if (/[+\-*\/%&|^~<>!]/.test(ch)) {
                stream.next();
                return "operator";
            }

            // Identifiers (palavras-chave, funções, variáveis)
            if (/[a-zA-Z_]/.test(ch)) {
                stream.eatWhile(/[\w_]/);
                var word = stream.current();
                
                if (keywords.hasOwnProperty(word)) {
                    return "keyword";
                }
                
                if (builtinFunctions.hasOwnProperty(word)) {
                    return "builtin";
                }
                
                // Variáveis e atributos
                return "variable";
            }

            // Parênteses, colchetes, etc.
            if (/[(){}\[\]]/.test(ch)) {
                stream.next();
                return "bracket";
            }

            // Ponto para acessos de atributos
            if (ch === ".") {
                stream.next();
                return "property";
            }

            // Vírgula
            if (ch === ",") {
                stream.next();
                return null;
            }

            stream.next();
            return null;
        }

        return {
            startState: function() {
                return {};
            },
            token: function(stream, state) {
                return tokenBase(stream, state);
            },
            lineComment: "#"
        };
    });

    CodeMirror.defineMIME("text/x-rule-engine", "rule-engine");
});
