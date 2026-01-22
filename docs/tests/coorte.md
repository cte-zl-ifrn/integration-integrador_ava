- IntegradorConfigTestCase: Configuração da app
- PapelModelTestCase: Modelo Papel com contextos (CURSO, POLO, PROGRAMA), propriedade exemplo, histórico
- CohortModelTestCase: Modelo Cohort com RuleField, campos name/idnumber únicos, relacionamento com Papel
- EnrolmentModelTestCase: Vínculos entre colaboradores e cohorts
- CoorteCursoModelTestCase: Modelo polimórfico para cursos, propriedades codigo/instancia, validação de unicidade
- CoortePoloModelTestCase: Modelo polimórfico para pólos, codigo_integracao com regex
- CoorteProgramaModelTestCase: Modelo polimórfico para programas
- VinculoModelTestCase: Vínculos com coortes polimórficas
- PapelAdminTestCase: Configuração do admin (list_display, filters, resources, import/export)
- CohortAdminTestCase: Configuração do admin com fieldsets e inline
- PapelFilterTestCase: Filtro customizado por contexto
- IntegrationTestCase: Fluxos completos de criação (Papel → Cohort → Enrolment e Papel → CoorteCurso → Vinculo)
- EdgeCasesTestCase: Casos extremos (sem pk, sigla vazia, propriedades através de polimorfismo)

Os testes cobrem todos os aspectos dos modelos polimórficos Coorte (CoorteCurso, CoortePolo, CoortePrograma), o novo modelo Cohort com RuleField para validação de regras, e as configurações do admin com import/export.
