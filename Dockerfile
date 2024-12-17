FROM python:3.13.1-slim-bookworm

ARG EXTRA_REQ="-r /requirements-dev.txt -r /requirements-lint.txt"

COPY requirements*.txt /
COPY src /apps/app

WORKDIR /apps/app
RUN pip install -r /requirements.txt $EXTRA_REQ \
    && mkdir -p /var/static \
    && python manage.py collectstatic --noinput

EXPOSE 80
# ENTRYPOINT [ "executable" ]
WORKDIR /apps/app
CMD  ["gunicorn"]
