FROM python:3.13.0-alpine

COPY requirements*.txt /

ARG EXTRA_REQ="-r requirements-dev.txt -r requirements-lint.txt"

RUN pip install --upgrade pip && \
    pip install -r /requirements.txt $EXTRA_REQ

COPY src /apps/app
WORKDIR /apps/app
RUN mkdir -p /var/static && python manage.py collectstatic --noinput

EXPOSE 80
# ENTRYPOINT [ "executable" ]
WORKDIR /apps/app
CMD ["python", "manage.py", "runserver_plus", "0.0.0.0:80"]
