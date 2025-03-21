########################
# Production build stage
########################################################################
FROM python:3.13.1-slim-bookworm AS production-build-stage

ENV PYTHONUNBUFFERED 1

COPY requirements*.txt /
RUN python3 -m venv /app/venv \
    && /app/venv/bin/pip install --upgrade --no-cache-dir --root-user-action ignore pip \
    && /app/venv/bin/pip install -r /requirements.txt \
    && echo '__version__ = "unknown"' > /app/venv/lib/python3.13/site-packages/django_better_choices/version.py

RUN mkdir -p /app/static
RUN ls -lh /app/venv/bin
COPY src /app/src
WORKDIR /app/src
RUN /app/venv/bin/python3 manage.py compilescss
RUN /app/venv/bin/python3 manage.py collectstatic --noinput
RUN du -h --max-depth=1  /app/venv/lib/python3.13/site-packages
RUN find /app | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf

RUN du -h --max-depth=1  /app/venv/lib/python3.13/site-packages


#########################
# Development build stage
########################################################################
FROM python:3.13.1-slim-bookworm AS development-build-stage

ARG EXTRA_REQ="-r /requirements-dev.txt -r /requirements-lint.txt"

COPY --chown=app:app --from=production-build-stage /app /app

ENV PYTHONUNBUFFERED 1

COPY requirements*.txt /
RUN /app/venv/bin/pip install $EXTRA_REQ

RUN du -h --max-depth=1  /app/venv/lib/python3.13/site-packages
RUN find /app | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
RUN du -h --max-depth=1  /app/venv/lib/python3.13/site-packages


########################
# Production final stage
########################################################################
FROM python:3.13.1-slim-bookworm AS production

RUN useradd -ms /usr/sbin/nologin app
USER app
COPY --chown=app:app --from=production-build-stage /app/venv /app/venv
COPY --chown=app:app --from=production-build-stage /app/static /app/static
COPY --chown=app:app --from=production-build-stage /app/src /app/src

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
COPY --chown=app:app --from=production-build-stage /app/static /app/static
COPY --chown=app:app --from=production-build-stage /app/src /app/src
COPY --chown=app:app --from=development-build-stage /app/venv /app/venv

USER app
EXPOSE 80
ENTRYPOINT [ "/app/src/django-entrypoint.sh" ]
WORKDIR /app/src
CMD  ["/app/venv/bin/python3", "manage.py", "runserver_plus" ]
