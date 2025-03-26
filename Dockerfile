########################
# Production build stage
########################################################################
FROM python:3.13.1-slim-bookworm AS production-build-stage

ENV PYTHONUNBUFFERED 1
WORKDIR /app

COPY requirements*.txt /app/
RUN    python3 -m venv /app/venv \
    && /app/venv/bin/pip install --upgrade --no-cache-dir --root-user-action ignore pip \
    && /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt -r /app/requirements-build.txt \
    && echo '__version__ = "unknown"' > /app/venv/lib/python3.13/site-packages/django_better_choices/version.py

COPY src /app/src
WORKDIR /app/src
RUN    mkdir -p /app/static \
    && /app/venv/bin/python3 manage.py compilescss \
    && /app/venv/bin/python3 manage.py collectstatic --noinput \
    && find /app -type d -name "__pycache__" -exec rm -rf {} + \
    && find /app -type f -name "*.py[co]" -exec rm -f {} + \
    && pip uninstall -y -r /app/requirements-build.txt


#########################
# Development build stage
########################################################################
FROM python:3.13.1-slim-bookworm AS development-build-stage

ENV PYTHONUNBUFFERED 1

ARG EXTRA_REQ="-r /app/requirements-dev.txt -r /app/requirements-lint.txt -r /app/requirements-build.txt"

COPY --chown=app:app --from=production-build-stage /app /app

RUN /app/venv/bin/pip install $EXTRA_REQ \
    && find /app -type d -name "__pycache__" -exec rm -rf {} + \
    && find /app -type f -name "*.py[co]" -exec rm -f {} +


########################
# Production final stage
########################################################################
FROM python:3.13.1-slim-bookworm AS production

RUN useradd -ms /usr/sbin/nologin app

COPY --chown=app:app --from=production-build-stage /app /app

USER app
EXPOSE 80
ENTRYPOINT [ "/app/src/django-entrypoint.sh" ]
WORKDIR /app/src
CMD  ["/app/venv/bin/gunicorn" ]


#########################
# Development final stage
########################################################################
FROM python:3.13.1-slim-bookworm

RUN useradd -ms /bin/bash app

COPY --chown=app:app --from=development-build-stage /app /app

USER app
EXPOSE 80
ENTRYPOINT [ "/app/src/django-entrypoint.sh" ]
WORKDIR /app/src
CMD  ["/app/venv/bin/python3", "manage.py", "runserver_plus" ]
