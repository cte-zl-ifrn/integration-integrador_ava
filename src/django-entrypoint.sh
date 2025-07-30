#!/usr/bin/env bash

case "${1#-}" in
    /app/venv/bin/gunicorn|/app/venv/bin/python3|/app/venv/bin/python)
        /app/venv/bin/python3 manage.py migrate_schemas --shared
        /app/venv/bin/python3 manage.py migrate --schema=public
        # /app/venv/bin/python3 manage.py migrate_schemas --shared
        ;;
        
esac


exec "$@"
