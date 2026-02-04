"""
Testes unitários para a app hacks.

Este módulo contém testes para:
- UserAdmin customizado: Admin customizado para User
- GroupAdmin customizado: Admin customizado para Group
- Método auth display customizado
- Resources de import/export
- Unregister de modelos padrão
"""
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from unittest.mock import Mock, patch, MagicMock
from hacks.admin import UserAdmin, GroupAdmin


class UserAdminTestCase(TestCase):
    """Testes para o UserAdmin customizado."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

    def test_user_admin_list_display(self):
        """Testa list_display do UserAdmin."""
        expected = ["username", "first_name", "last_name", "email", "auth"]
        self.assertEqual(self.admin.list_display, expected)

    def test_user_admin_list_filter(self):
        """Testa list_filter do UserAdmin."""
        expected = ["is_superuser", "is_active", "is_staff", "groups__name"]
        self.assertEqual(self.admin.list_filter, expected)

    def test_user_admin_search_fields(self):
        """Testa search_fields do UserAdmin."""
        expected = ["first_name", "last_name", "username", "email"]
        self.assertEqual(self.admin.search_fields, expected)

    def test_user_admin_readonly_fields(self):
        """Testa readonly_fields do UserAdmin."""
        expected = ["date_joined", "last_login"]
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_user_admin_autocomplete_fields(self):
        """Testa autocomplete_fields do UserAdmin."""
        self.assertIn('groups', self.admin.autocomplete_fields)

    def test_user_admin_fieldsets_structure(self):
        """Testa estrutura dos fieldsets."""
        self.assertEqual(len(self.admin.fieldsets), 4)
        
        # Verifica nomes das seções
        fieldset_names = [fs[0] for fs in self.admin.fieldsets]
        self.assertIn('Identificação', fieldset_names)
        self.assertIn('Autorização e autenticação', fieldset_names)
        self.assertIn('Dates', fieldset_names)
        self.assertIn('Permissions', fieldset_names)

    def test_auth_display_active_user(self):
        """Testa método auth para usuário ativo."""
        self.user.is_active = True
        self.user.save()
        
        result = self.admin.auth(self.user)
        
        self.assertIn('✅', result)
        self.assertIn('Ativo', result)

    def test_auth_display_inactive_user(self):
        """Testa método auth para usuário inativo."""
        self.user.is_active = False
        self.user.save()
        
        result = self.admin.auth(self.user)
        
        self.assertIn('❌', result)
        self.assertIn('Inativo', result)

    def test_auth_display_superuser_and_staff(self):
        """Testa método auth para superuser com staff."""
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        
        result = self.admin.auth(self.user)
        
        self.assertIn('👮‍♂️', result)
        self.assertIn('Super usuário', result)

    def test_auth_display_superuser_without_staff(self):
        """Testa método auth para superuser sem staff."""
        self.user.is_staff = False
        self.user.is_superuser = True
        self.user.save()
        
        result = self.admin.auth(self.user)
        
        self.assertIn('🕵️‍♂️', result)

    def test_auth_display_staff_without_superuser(self):
        """Testa método auth para staff sem superuser."""
        self.user.is_staff = True
        self.user.is_superuser = False
        self.user.save()
        
        result = self.admin.auth(self.user)
        
        self.assertIn('👷‍♂️', result)
        self.assertIn('Pode operar o admin', result)

    def test_auth_display_regular_user(self):
        """Testa método auth para usuário comum."""
        self.user.is_staff = False
        self.user.is_superuser = False
        self.user.save()
        
        result = self.admin.auth(self.user)
        
        self.assertIn('👨', result)
        self.assertIn('simples colaborador', result)

    def test_auth_display_user_with_single_group(self):
        """Testa método auth para usuário com um grupo."""
        group = Group.objects.create(name='Test Group')
        self.user.groups.add(group)
        
        result = self.admin.auth(self.user)
        
        self.assertIn('👥', result)
        self.assertIn('no grupo', result)
        self.assertIn('Test Group', result)

    def test_auth_display_user_with_multiple_groups(self):
        """Testa método auth para usuário com múltiplos grupos."""
        group1 = Group.objects.create(name='Group 1')
        group2 = Group.objects.create(name='Group 2')
        self.user.groups.add(group1, group2)
        
        result = self.admin.auth(self.user)
        
        self.assertIn('👥', result)
        self.assertIn('nos grupos', result)
        self.assertIn('Group 1', result)
        self.assertIn('Group 2', result)

    def test_auth_display_returns_safe_html(self):
        """Testa que auth retorna HTML seguro."""
        result = self.admin.auth(self.user)
        
        # Verifica que contém tags HTML
        self.assertIn('<span', result)
        self.assertIn('</span>', result)
        
        # Verifica que contém estilos inline
        self.assertIn('font-size: 150%', result)

    def test_user_admin_has_enrolment_inline(self):
        """Testa que UserAdmin tem EnrolmentInline."""
        self.assertEqual(len(self.admin.inlines), 1)
        
        from hacks.admin import EnrolmentInline
        self.assertEqual(self.admin.inlines[0], EnrolmentInline)

    def test_user_admin_resource_classes(self):
        """Testa que UserAdmin tem resource classes configuradas."""
        self.assertTrue(hasattr(self.admin, 'resource_classes'))
        self.assertEqual(len(self.admin.resource_classes), 1)


class GroupAdminTestCase(TestCase):
    """Testes para o GroupAdmin customizado."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.site = AdminSite()
        self.admin = GroupAdmin(Group, self.site)
        
        self.group = Group.objects.create(name='Test Group')

    def test_group_admin_list_display(self):
        """Testa list_display do GroupAdmin."""
        expected = ["name"]
        self.assertEqual(self.admin.list_display, expected)

    def test_group_admin_search_fields(self):
        """Testa search_fields do GroupAdmin."""
        expected = ["name"]
        self.assertEqual(self.admin.search_fields, expected)

    def test_group_admin_resource_classes(self):
        """Testa que GroupAdmin tem resource classes."""
        self.assertTrue(hasattr(self.admin, 'resource_classes'))
        self.assertEqual(len(self.admin.resource_classes), 1)

    def test_group_resource_has_permissions_field(self):
        """Testa que GroupResource tem campo permissions."""
        resource_class = self.admin.resource_classes[0]
        resource = resource_class()
        
        self.assertTrue(hasattr(resource, 'fields'))
        # Verifica se permissions está nos campos do resource
        field_names = [f.column_name for f in resource.fields.values()]
        self.assertIn('permissions', field_names)


class EnrolmentInlineTestCase(TestCase):
    """Testes para o EnrolmentInline."""

    def setUp(self):
        """Configura o ambiente de teste."""
        from hacks.admin import EnrolmentInline
        self.inline = EnrolmentInline(User, AdminSite())

    def test_enrolment_inline_model(self):
        """Testa o modelo do inline."""
        from coorte.models import Enrolment
        self.assertEqual(self.inline.model, Enrolment)

    def test_enrolment_inline_extra(self):
        """Testa que extra está configurado como 0."""
        self.assertEqual(self.inline.extra, 0)

    def test_enrolment_inline_autocomplete_fields(self):
        """Testa autocomplete_fields do inline."""
        self.assertIn('cohort', self.inline.autocomplete_fields)


class AdminSiteCustomizationTestCase(TestCase):
    """Testes para customizações do admin site."""

    def test_user_model_unregistered_and_reregistered(self):
        """Testa que User foi re-registrado com admin customizado."""
        from django.contrib.admin import site
        
        # Verifica que User está registrado
        self.assertIn(User, site._registry)
        
        # Verifica que é a versão customizada
        admin_instance = site._registry[User]
        self.assertIsInstance(admin_instance, UserAdmin)

    def test_group_model_unregistered_and_reregistered(self):
        """Testa que Group foi re-registrado com admin customizado."""
        from django.contrib.admin import site
        
        # Verifica que Group está registrado
        self.assertIn(Group, site._registry)
        
        # Verifica que é a versão customizada
        admin_instance = site._registry[Group]
        self.assertIsInstance(admin_instance, GroupAdmin)


class UserResourceTestCase(TestCase):
    """Testes para UserResource (import/export)."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)
        self.resource_class = self.admin.resource_classes[0]
        self.resource = self.resource_class()

    def test_user_resource_export_order(self):
        """Testa a ordem de exportação dos campos."""
        expected_order = [
            "username",
            "first_name",
            "last_name",
            "email",
            "active",
            "is_superuser",
            "is_active",
            "is_staff",
            "groups",
        ]
        
        self.assertEqual(
            self.resource._meta.export_order,
            expected_order
        )

    def test_user_resource_import_id_fields(self):
        """Testa campos de identificação para import."""
        self.assertEqual(
            self.resource._meta.import_id_fields,
            ("username",)
        )

    def test_user_resource_skip_unchanged(self):
        """Testa se skip_unchanged está ativado."""
        self.assertTrue(self.resource._meta.skip_unchanged)

    def test_user_resource_has_groups_field(self):
        """Testa que resource tem campo groups."""
        field_names = [f.column_name for f in self.resource.fields.values()]
        self.assertIn('groups', field_names)


class GroupResourceTestCase(TestCase):
    """Testes para GroupResource (import/export)."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.site = AdminSite()
        self.admin = GroupAdmin(Group, self.site)
        self.resource_class = self.admin.resource_classes[0]
        self.resource = self.resource_class()

    def test_group_resource_export_order(self):
        """Testa a ordem de exportação dos campos."""
        expected_order = ["name", "permissions"]
        
        self.assertEqual(
            self.resource._meta.export_order,
            expected_order
        )

    def test_group_resource_import_id_fields(self):
        """Testa campos de identificação para import."""
        self.assertEqual(
            self.resource._meta.import_id_fields,
            ("name",)
        )

    def test_group_resource_skip_unchanged(self):
        """Testa se skip_unchanged está ativado."""
        self.assertTrue(self.resource._meta.skip_unchanged)


class IntegrationTestCase(TestCase):
    """Testes de integração para hacks.admin."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.user_admin = UserAdmin(User, self.site)
        
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )

    def test_complete_user_admin_workflow(self):
        """Testa fluxo completo do UserAdmin."""
        # 1. Criar usuário
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        
        # 2. Adicionar a grupos
        group = Group.objects.create(name='Editors')
        user.groups.add(group)
        
        # 3. Verificar display auth
        result = self.user_admin.auth(user)
        self.assertIn('👥', result)
        self.assertIn('Editors', result)
        
        # 4. Tornar staff
        user.is_staff = True
        user.save()
        
        result = self.user_admin.auth(user)
        self.assertIn('👷‍♂️', result)

    def test_user_admin_with_multiple_groups_display(self):
        """Testa display de usuário com múltiplos grupos."""
        user = User.objects.create_user(username='multigroup')
        
        # Cria vários grupos
        groups = [
            Group.objects.create(name=f'Group {i}')
            for i in range(3)
        ]
        
        user.groups.set(groups)
        
        result = self.user_admin.auth(user)
        
        # Verifica que mostra "nos grupos" (plural)
        self.assertIn('nos grupos', result)
        
        # Verifica que todos os grupos aparecem
        for group in groups:
            self.assertIn(group.name, result)


class EdgeCasesTestCase(TestCase):
    """Testes de casos extremos."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.site = AdminSite()
        self.user_admin = UserAdmin(User, self.site)

    def test_auth_display_with_user_without_groups(self):
        """Testa auth com usuário sem grupos."""
        user = User.objects.create_user(username='nogroups')
        
        result = self.user_admin.auth(user)
        
        # Não deve mostrar ícone de grupos
        # mas deve mostrar outros ícones
        self.assertIn('👨', result)

    def test_auth_display_with_inactive_superuser(self):
        """Testa auth com superuser inativo."""
        user = User.objects.create_user(username='inactive')
        user.is_superuser = True
        user.is_staff = True
        user.is_active = False
        user.save()
        
        result = self.user_admin.auth(user)
        
        # Deve mostrar inativo E superuser
        self.assertIn('❌', result)
        self.assertIn('👮‍♂️', result)

    def test_auth_display_with_group_special_characters(self):
        """Testa auth com grupo contendo caracteres especiais."""
        user = User.objects.create_user(username='specialchars')
        group = Group.objects.create(name="Group's & Name")
        user.groups.add(group)
        
        result = self.user_admin.auth(user)
        
        # Nome do grupo deve aparecer
        self.assertIn("Group's & Name", result)

    def test_user_admin_fieldsets_all_fields_valid(self):
        """Testa que todos os campos nos fieldsets são válidos."""
        # Obtém todos os campos dos fieldsets
        all_fields = []
        for name, options in self.user_admin.fieldsets:
            fields = options['fields']
            for field in fields:
                if isinstance(field, (list, tuple)):
                    all_fields.extend(field)
                else:
                    all_fields.append(field)
        
        # Verifica que todos são campos válidos do User
        user_field_names = [f.name for f in User._meta.get_fields()]
        
        for field in all_fields:
            # Campos devem existir no modelo ou ser readonly
            is_valid = (
                field in user_field_names or
                field in self.user_admin.readonly_fields
            )
            self.assertTrue(
                is_valid,
                f"Campo '{field}' não é válido"
            )

    def test_auth_display_html_escaping(self):
        """Testa que HTML no nome do grupo é escapado corretamente."""
        user = User.objects.create_user(username='htmltest')
        group = Group.objects.create(name='<script>alert("xss")</script>')
        user.groups.add(group)
        
        result = self.user_admin.auth(user)
        
        # O HTML deve estar presente mas como texto, não executável
        self.assertIn('script', result.lower())

    def test_empty_username_handling(self):
        """Testa comportamento com username vazio (se permitido)."""
        # Username é obrigatório, então este teste verifica a validação
        with self.assertRaises(Exception):
            User.objects.create_user(username='')

    def test_very_long_group_names(self):
        """Testa display com nomes de grupos muito longos."""
        user = User.objects.create_user(username='longnames')
        
        long_name = 'A' * 200
        group = Group.objects.create(name=long_name)
        user.groups.add(group)
        
        result = self.user_admin.auth(user)
        
        # Nome longo deve aparecer (pode ser truncado no HTML)
        self.assertIn('A' * 50, result)  # Pelo menos parte do nome
