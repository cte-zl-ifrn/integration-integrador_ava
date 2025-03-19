import os
import sys
from settings import DATABASES
import psycopg
import time
import logging
from sc4py.env import env_as_bool


def _wait_db(db):
    connection = psycopg.connect(
        dbname=db["NAME"],
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
    )
    while connection.closed:
        logging.info(f"ERROR: Aguardando o banco {db['HOST']:db['PORT']/db['NAME']} subir")
        time.sleep(3)


def start_debug():
    if env_as_bool("DJANGO_DEBUG", False):
        try:
            import debugpy
            from django.core.management import execute_from_command_line

            debugpy.listen(("0.0.0.0", 5678))
            execute_from_command_line([sys.argv[0], "show_urls"])
        except Exception:
            pass


def boot():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("ops!") from exc

    _wait_db(DATABASES["default"])
    execute_from_command_line([sys.argv[0], "migrate"])
