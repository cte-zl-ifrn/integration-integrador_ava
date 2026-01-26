from django.urls import path, include, re_path
from django.contrib import admin
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

admin.site.site_title = f"{settings.PROJECT_TITLE} (v{settings.PROJECT_VERSION})"
admin.site.index_title = settings.PROJECT_TITLE
admin.site.site_header = admin.site.site_title

urlpatterns = []

# Debug toolbar deve vir PRIMEIRO em modo DEBUG
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
    except ModuleNotFoundError:
        pass

urlpatterns += [
    path("api/", include("django_rule_engine.api.urls")),  # API precisa vir ANTES do admin
    path("", include("integrador.urls")),  # URLs do integrador ANTES do admin
    path("", include("health.urls")),
    path("", include("security.urls")),
    path("", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            f"{settings.ROOT_URL_PATH}media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
        re_path(
            f"{settings.ROOT_URL_PATH}static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATIC_ROOT},
        ),
    ]
