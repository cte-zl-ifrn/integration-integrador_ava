from django.utils.translation import gettext as _
import json
import urllib
import requests
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.timezone import now
from django.http import HttpRequest, HttpResponse
from django.core.exceptions import ValidationError

OAUTH = settings.OAUTH

def login(request: HttpRequest) -> HttpResponse:
    request.session["next"] = request.GET.get('next', '/')
    redirect_uri = f"{OAUTH["REDIRECT_URI"]}"
    suap_url = f"{OAUTH["BASE_URL"]}/o/authorize/?response_type=code&client_id={OAUTH["CLIENT_ID"]}&redirect_uri={redirect_uri}"
    return redirect(suap_url)


def authenticate(request: HttpRequest) -> HttpResponse:

    if request.GET.get("error") == "access_denied":
        return render(request, "security/not_authorized.html")
    
    try:
        def _get_tokens(request):
            if "code" not in request.GET:
                raise Exception(_("O código de autenticação não foi informado."))
            token_response = requests.post(
                f"{OAUTH['BASE_URL']}/o/token/",
                data={
                    "grant_type": "authorization_code",
                    "code": request.GET.get("code"),
                    "redirect_uri": OAUTH["REDIRECT_URI"],
                    "client_id": OAUTH["CLIENT_ID"],
                    "client_secret": OAUTH["CLIENT_SECRET"],
                }
            )
            data = json.loads(token_response.text)
            if data.get("error_description") == "Mismatching redirect URI.":
                raise ValueError("O administrador do sistema configurou errado o 'Redirect uris' no SUAP-Login ou no OAUTH_REDIRECT_URI.")
            return data

        def _get_userinfo(request_data):
            response = requests.get(
                f"{OAUTH['BASE_URL']}/api/v1/userinfo/?scope={request_data.get('scope')}",
                headers={
                    "Authorization": "Bearer {}".format(request_data.get("access_token")),
                    "x-api-key": OAUTH["CLIENT_SECRET"],
                }
            )
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
            
        request_data = _get_tokens(request)
        userinfo = _get_userinfo(request_data)
        user = _save_user(userinfo)
        auth.login(request, user)
        return redirect(request.session.pop("next", "/"))
    except Exception as e:
        return render(request, "security/authorization_error.html", context={"error_cause": str(e)})


def logout(request: HttpRequest) -> HttpResponse:
    logout_token = request.session.get("logout_token")
    auth.logout(request)
    return redirect(f"{OAUTH['BASE_URL']}/logout/?token={logout_token}")
