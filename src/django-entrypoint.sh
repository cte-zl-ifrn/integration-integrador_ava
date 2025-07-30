#!/usr/bin/env bash

case "${1#-}" in
    /app/venv/bin/gunicorn|/app/venv/bin/python3|/app/venv/bin/python|gunicorn|python3|python)
        /app/venv/bin/python3 manage.py migrate_schemas --shared
        /app/venv/bin/python3 manage.py create_public_cliente
        ;;
        
esac


exec "$@"
