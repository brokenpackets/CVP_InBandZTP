FROM python:3.8-slim-buster

LABEL maintainer="et@arista.com"

# install dependencies
RUN apt-get update && apt-get install -y iputils-ping
RUN pip3 install docker requests ruamel.yaml

# install app
COPY app /app

ADD entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
