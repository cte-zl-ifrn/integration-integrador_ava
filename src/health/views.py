from django.conf import settings
from django.http import JsonResponse
from django.db import connection


def health(request):
    try:
        connection.connect()
        connection_result = "OK"
    except Exception:
        connection_result = "FAIL"

    return JsonResponse(
        {
            "Debug": "FAIL (are active)" if settings.DEBUG else "OK",
            "Database": connection_result,
            "Redis": "Not tested",
            "Moodles": {
                "Ambiente 1": "Not tested",
                "Ambiente ...": "Not tested",
                "Ambiente N": "Not tested",
            },
        }
    )
