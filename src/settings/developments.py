# -*- coding: utf-8 -*-
import importlib.util
import logging
import os
import sys

from sc4py.env import env_as_bool

from .apps import INSTALLED_APPS
from .middlewares import MIDDLEWARE

logger = logging.getLogger(__name__)

DEBUG = env_as_bool("DJANGO_DEBUG", True)
TESTING = "test" in sys.argv or "PYTEST_VERSION" in os.environ
DEVELOPMENT = DEBUG and not TESTING

# Check if running tests
INTERNAL_IPS = ["127.0.0.1", "localhost"]
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    "TESTING": False,
    "DISABLE_PANELS": {
        "debug_toolbar.panels.history.HistoryPanel",
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    },
    "SHOW_COLLAPSED": True,
}

extra_middleware = []
extra_apps = []
if DEVELOPMENT:
    try:
        if importlib.util.find_spec("debug_toolbar") is not None:
            extra_middleware += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
            extra_apps += ["debug_toolbar"]
    except ModuleNotFoundError:
        logger.info("Não foi possível carregar o debug_toolbar")

MIDDLEWARE += extra_middleware
INSTALLED_APPS += extra_apps
