FROM python:3.12.4-slim-bookworm

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get -y install curl vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD requirements*.txt /

RUN pip install --upgrade pip && \
    pip install -r /requirements.txt -r requirements-dev.txt -r requirements-lint.txt

ADD src /apps/app
WORKDIR /apps/app
RUN mkdir -p /var/static && python manage.py collectstatic --noinput

EXPOSE 80
# ENTRYPOINT [ "executable" ]
WORKDIR /apps/app
CMD ["python", "manage.py", "runserver_plus", "0.0.0.0:80"]
