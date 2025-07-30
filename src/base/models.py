from django.utils.translation import gettext as _


class ActiveMixin:
    @property
    def active_icon(self):
        return "✅" if self.active else "⛔"
