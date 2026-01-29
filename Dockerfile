ARG PYTHON_VERSION=3.14.2-slim-trixie

FROM python:$PYTHON_VERSION AS build

ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements-build.txt /
RUN pip install -r /requirements.txt  -r /requirements-build.txt


#########################
# Development build stage
########################################################################
FROM build AS development

COPY requirements-dev.txt requirements-lint.txt /
COPY src/dsgovbr /app/src/dsgovbr
RUN useradd -ms /usr/sbin/nologin app \
    && pip install -r /requirements-dev.txt -r /requirements-lint.txt

USER app
EXPOSE 8000
ENTRYPOINT [ "/app/src/django-entrypoint.sh" ]
WORKDIR /app/src
CMD  ["runserver_plus"]


#########################
# Production build stage
########################################################################
FROM build AS production

COPY src /app/src
WORKDIR /app/src
RUN    useradd -ms /usr/sbin/nologin app \
    && mkdir -p /app/static \
    && python manage.py compilescss \
    && python manage.py collectstatic --noinput \
    && ls -l /app/static \
    && find /app -type d -name "__pycache__" -exec rm -rf {} + \
    && find /usr/local/lib/python3.14/site-packages/ -type d -name "__pycache__" -exec rm -rf {} +

USER app
EXPOSE 8000
ENTRYPOINT [ "/app/src/django-entrypoint.sh" ]
WORKDIR /app/src
CMD  ["gunicorn" ]
