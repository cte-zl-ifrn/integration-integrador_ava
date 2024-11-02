FROM python:3.13.0-alpine

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
CMD ["python", "manage.py", "runserver_plus", "0.0.0.0:80"]
