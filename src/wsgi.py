import os

from sc4py.env import env_as_bool

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

application = WhiteNoise(get_wsgi_application()) if not env_as_bool("DJANGO_DEBUG", True) else get_wsgi_application()
