# Como funciona

O **Integrador AVA** recebe dados de um SGA e os sincroniza com o Moodle usando 2 padrões de payload (Suap e SGA genérico) e 3 estratégias de integração (brokers).

| Payload recebido | Broker de integração | Plugin Moodle | Status         |
|------------------|----------------------|---------------|----------------|
| Suap             | `suap2local_suap`    | `local_suap`  | Implementado   |
| Suap             | `suap2tool_sga`      | `tool_sga`    | Em elaboração  |
| SGA (genérico)   | `sga2tool_sga`       | `tool_sga`    | Em elaboração  |
