from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase

from sga.db.fields import (
    ObfuscatedCharField,
    PermissiveURLField,
    default_obfuscation,
    permissive_url_validator,
)
from sga.db.obfuscators import email, first4, last4, mask_all, middle


class ObfuscatorsTestCase(TestCase):
    def test_last4(self):
        self.assertEqual(last4("hello"), "****ello")

    def test_first4(self):
        self.assertEqual(first4("hello"), "hell****")

    def test_mask_all(self):
        self.assertEqual(mask_all("hello"), "*****")

    def test_middle_short(self):
        self.assertEqual(middle("abc"), "***")
        self.assertEqual(middle("abcd"), "****")

    def test_middle_long(self):
        self.assertEqual(middle("hello"), "he*lo")
        self.assertEqual(middle("abcdef"), "ab**ef")

    def test_email_with_at(self):
        self.assertEqual(email("user@example.com"), "us**@example.com")
        self.assertEqual(email("us@example.com"), "**@example.com")
        self.assertEqual(email("a@example.com"), "*@example.com")

    def test_email_without_at(self):
        self.assertEqual(email("notanemail"), "****mail")


class FieldsTestCase(TestCase):
    def test_default_obfuscation(self):
        self.assertEqual(default_obfuscation("abc"), "****")
        self.assertEqual(default_obfuscation("abcd"), "****abcd")
        self.assertEqual(default_obfuscation("abcde"), "****bcde")

    def test_permissive_url_validator(self):
        self.assertIsNone(permissive_url_validator(None))
        self.assertIsNone(permissive_url_validator("http://example.com"))
        with self.assertRaises(ValidationError):
            permissive_url_validator("invalid-url")

    def test_permissive_url_field_formfield(self):
        field = PermissiveURLField()
        form_field = field.formfield()
        self.assertIsInstance(form_field, forms.CharField)

    def test_obfuscated_char_field_get_obfuscated_value(self):
        # obfuscator is mask_all by default
        field = ObfuscatedCharField(max_length=100)
        self.assertIsNone(field.get_obfuscated_value(None))
        self.assertEqual(field.get_obfuscated_value("hello"), "*****")

        # obfuscator=None should fallback to default_obfuscation
        field_none = ObfuscatedCharField(max_length=100, obfuscator=None)
        self.assertEqual(field_none.get_obfuscated_value("hello"), "****ello")

    def test_obfuscated_char_field_deconstruct(self):
        field = ObfuscatedCharField(max_length=100)
        name, path, args, kwargs = field.deconstruct()
        self.assertNotIn("obfuscator", kwargs)

        field_custom = ObfuscatedCharField(max_length=100, obfuscator=last4)
        name, path, args, kwargs = field_custom.deconstruct()
        self.assertEqual(kwargs["obfuscator"], last4)
