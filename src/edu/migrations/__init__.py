def migrate_cursos_forwards(apps, schema_editor):
    Antigo = apps.get_model("integrador", "Curso")
    Novo = apps.get_model("integrador", "Curso")
    for a in Antigo.objects.all():
        Novo.objects.create(
            suap_id=a.suap_id,
            codigo=a.codigo,
            nome=a.nome,
            descricao=a.descricao,
        )


def migrate_cursos_reverse(apps, schema_editor):
    pass


def migrate_polos_forwards(apps, schema_editor):
    Antigo = apps.get_model("integrador", "Polo")
    Novo = apps.get_model("integrador", "Polo")
    for a in Antigo.objects.all():
        Novo.objects.create(
            suap_id=a.suap_id,
            codigo=a.nome,
            nome=a.nome,
        )


def migrate_polos_reverse(apps, schema_editor):
    pass


def migrate_programas_forwards(apps, schema_editor):
    Antigo = apps.get_model("integrador", "Programa")
    Novo = apps.get_model("integrador", "Programa")
    for a in Antigo.objects.all():
        Novo.objects.create(
            suap_id=a.suap_id,
            nome=a.nome,
            sigla=a.sigla,
        )


def migrate_programas_reverse(apps, schema_editor):
    pass
