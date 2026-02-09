ARG BASEIMAGE=1.0.1


#########################
# Development build stage
########################################################################
FROM ctezlifrn/avaintegrationbase:$BASEIMAGE AS development

COPY requirements-dev.txt /
RUN    useradd -ms /usr/sbin/nologin app \
    && pip uninstall dsgovbr \
    && pip install -r /requirements-dev.txt

USER app
EXPOSE 8000
WORKDIR /app/src
CMD  ["runserver_plus"]


#########################
# Production build stage
########################################################################
FROM ctezlifrn/avaintegrationbase:$BASEIMAGE AS production

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
WORKDIR /app/src
CMD  ["gunicorn" ]
