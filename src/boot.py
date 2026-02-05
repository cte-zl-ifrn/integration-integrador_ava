import os
import sys
from settings import DATABASES
import psycopg
import time
import logging
from sc4py.env import env_as_bool


def _wait_db(db):
    connected = False
    connection = None
    while not connected:
        try:
            connection = psycopg.connect(
                dbname=db["NAME"],
                user=db["USER"],
                password=db["PASSWORD"],
                host=db["HOST"],
                port=db["PORT"],
            )
            connected = not connection.closed
            logging.info(f"ERROR: Aguardando por 3s o banco {db['HOST']:db['PORT']/db['NAME']} subir")
            time.sleep(3)
        except Exception: # pragma: no cover
            pass
        finally:
            if connection and not connection.closed:
                connection.close()
    logging.info(f"SUCCESS: Banco {db['HOST']}:{db['PORT']}/{db['NAME']} está disponível")


def start_debug():
    if env_as_bool("DJANGO_DEBUG", False):
        try:
            import debugpy
            from django.core.management import execute_from_command_line

            execute_from_command_line([sys.argv[0], "show_urls"])
            debugpy.listen(("0.0.0.0", 12345))
        except Exception as e: # pragma: no cover
            pass


def boot():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc: # pragma: no cover
        raise ImportError("ops!") from exc

    _wait_db(DATABASES["default"])
    execute_from_command_line([sys.argv[0], "migrate"])
