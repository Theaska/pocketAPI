FROM python:3.8-alpine

WORKDIR /app
COPY . /app/

ENV DJANGO_SETTINGS_MODULE=project.api_settings

RUN apk update && \
    apk add --virtual build-deps gcc musl-dev && \
    apk add postgresql-dev postgresql

RUN pip install --upgrade -r requirements.txt
RUN apk update && apk add bash

CMD ["postgres", "python"]