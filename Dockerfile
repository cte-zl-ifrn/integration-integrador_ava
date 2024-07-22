FROM python:3.12.4-slim-bookworm

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get -y install curl vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ADD requirements.txt /

RUN pip install --upgrade pip && \
    pip install -r /requirements.txt


ADD requirements-dev.txt /apps/req/requirements-dev.txt
WORKDIR /apps/req
# COPY --from=django-adminlte3 / /apps/django-adminlte3
RUN pip install -r requirements-dev.txt

# FIX: bug on corsheaders
# RUN echo 'import django.dispatch;check_request_enabled = django.dispatch.Signal()' > /usr/local/lib/python3.10/site-packages/corsheaders/signals.py

ADD src /apps/app

EXPOSE 8000
# ENTRYPOINT [ "executable" ]
WORKDIR /apps/app
CMD ["python", "manage.py", "runserver_plus", "0.0.0.0:80"]
