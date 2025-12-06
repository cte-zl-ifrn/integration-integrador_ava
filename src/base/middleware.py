# middleware.py
from django.http import HttpResponseForbidden
from django.db import connection

class PublicAdminOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        if request.path.startswith("/api/admin/gestao/") and connection.schema_name != "public":
            return HttpResponseForbidden("Admin disponível somente no schema público.")
        return self.get_response(request)
