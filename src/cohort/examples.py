JSON_DE_EXEMPLO = {
    "polo": {
        "id": 3,
        "descricao": "Nome do polo (RN)"
    },
    "curso": {
        "id": 123,
        "nome": "Curso de Formação Inicial e Continuada (FIC) ou Qualificação Profissional em Alguma Coisa Aí",
        "codigo": "132456",
        "descricao": "FIC+ em Alguma Coisa Aí"
    },
    "turma": {
        "id": 1234,
        "codigo": "20261.1.132456.123.1M"
    },
    "alunos": [
        {
        "id": 1,
        "nome": "Aluno um",
        "polo": {
            "id": 3,
            "descricao": "Nome do polo (RN)"
        },
        "email": "",
        "programa": "UAB",
        "situacao": "ativo",
        "matricula": "20261132456RN0001",
        "situacao_diario": "ativo",
        "email_secundario": "aluno1@teste.local"
        }            
    ],
    "campus": {
        "id": 1,
        "sigla": "CENTRAL",
        "descricao": "CAMPUS CENTRAL"
    },
    "diario": {
        "id": 123456,
        "tipo": "regular",
        "sigla": "FIC.1234",
        "situacao": "Aberto",
        "descricao": "Matemática",
        "descricao_historico": "Matemática"
    },
    "componente": {
        "id": 4321,
        "tipo": 1,
        "sigla": "FIC.1234",
        "periodo": 1,
        "optativo": False,
        "descricao": "Matemática",
        "qtd_avaliacoes": 1,
        "descricao_historico": "Matemática"
    },
    "professores": [
        {
            "id": 11,
            "nome": "Professor onze",
            "tipo": "Principal",
            "email": "professor.onze@email.local",
            "login": "12345611",
            "status": "ativo",
            "email_secundario": "professor.onze@email.local"
        },
        {
            "id": 12,
            "nome": "Professor doze",
            "tipo": "Formador",
            "email": "professor.doze@email.local",
            "login": "12345612",
            "status": "ativo",
            "email_secundario": "professor.doze@email.local"
        },
        {
            "id": 13,
            "nome": "Professor treze",
            "tipo": "Tutor",
            "email": "professor.treze@email.local",
            "login": "12345613",
            "status": "ativo",
            "email_secundario": "professor.treze@email.local"
        },
        {
            "id": 14,
            "nome": "Professor quatorze",
            "tipo": "Mediador",
            "email": "professor.quatorze@email.local",
            "login": "12345614",
            "status": "inativo",
            "email_secundario": "professor.quatorze@email.local"
        }
    ]
}
