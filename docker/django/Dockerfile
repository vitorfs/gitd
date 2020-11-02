FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DJANGO_SETTINGS_MODULE 'gitd.settings.production'

WORKDIR /code
COPY . /code/
RUN pip install -r requirements/production.txt --no-cache-dir
