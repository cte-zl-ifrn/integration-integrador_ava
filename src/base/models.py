class ActiveMixin:
    @property
    def active_icon(self):
        return "✅" if self.active else "⛔"
