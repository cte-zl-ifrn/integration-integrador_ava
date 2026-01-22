from django.utils.translation import gettext as _
import json
import urllib
import requests
import logging
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.timezone import now
from django.http import HttpRequest, HttpResponse
from django.core.exceptions import ValidationError
from sentry_sdk import capture_exception


logger = logging.getLogger(__name__)


OAUTH = settings.OAUTH


def _get_tokens(request):
    if "code" not in request.GET:
        raise Exception(_("O SUAP não informou o código de autenticação."))
    response = requests.post(
        OAUTH.get('TOKEN_URL', ""),
        data={
            "grant_type": "authorization_code",
            "code": request.GET.get("code"),
            "redirect_uri": f"http://{request.get_host()}/authenticate/",
            "client_id": OAUTH["CLIENT_ID"],
            "client_secret": OAUTH["CLIENT_SECRET"],
        },
    )
    print("_get_tokens", response.text)
    data = json.loads(response.text)
    if data.get("error_description") == "Mismatching redirect URI.":
        raise ValueError(
            "O administrador do sistema configurou errado o 'Redirect uris' no SUAP-Login ou no OAUTH_REDIRECT_URI."
        )
    return data

def _get_userinfo(request_data):
    response = requests.get(
        f"{OAUTH['USERINFO_URL']}?scope={request_data.get('scope')}",
        headers={
            "Authorization": f"Bearer {request_data.get('access_token')}",
            "x-api-key": OAUTH["CLIENT_SECRET"],
        },
    )
    print("_get_userinfo", response.text)
    return json.loads(response.text)

def _save_user(userinfo):
    username = userinfo["identificacao"]
    user = User.objects.filter(username=username).first()

    defaults = {
        "first_name": userinfo.get("primeiro_nome"),
        "last_name": userinfo.get("ultimo_nome"),
        "email": userinfo.get("email_preferencial") or userinfo.get("identificacao") + "@ifrn.edu.br",
    }

    if user is None:
        is_superuser = User.objects.count() == 0
        user = User.objects.create(
            username=username,
            is_superuser=is_superuser,
            is_staff=is_superuser,
            **defaults,
        )
    else:
        user = User.objects.filter(username=username).first()
        User.objects.filter(username=username).update(**defaults)
    return user


def login(request: HttpRequest) -> HttpResponse:
    request.session["next"] = request.GET.get("next", "/")

    suap_url = f"{OAUTH["BASE_URL"]}/o/authorize/?response_type=code&client_id={OAUTH["CLIENT_ID"]}&redirect_uri=http://{request.get_host()}/authenticate/"
    return redirect(suap_url)


def authenticate(request: HttpRequest) -> HttpResponse:

    if request.GET.get("error") == "access_denied":
        return render(request, "security/not_authorized.html")

    try:

        request_data = _get_tokens(request)
        userinfo = _get_userinfo(request_data)
        user = _save_user(userinfo)
        auth.login(request, user)
        return redirect(request.session.pop("next", "/"))
    except Exception as e:
        capture_exception(e)
        return render(request, "security/authorization_error.html", context={"error_cause": str(e)})


def logout(request: HttpRequest) -> HttpResponse:
    auth.logout(request)

    logout_token = request.session.get("logout_token", "")
    next = urllib.parse.quote_plus(settings.LOGIN_REDIRECT_URL)
    return redirect(f"{settings.LOGOUT_REDIRECT_URL}?token={logout_token}&next={next}")
