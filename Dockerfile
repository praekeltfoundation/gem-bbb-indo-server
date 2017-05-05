FROM ubuntu:14.04
MAINTAINER Colin Alston <colin@praekelt.com>
RUN apt-get update && apt-get -y --force-yes install libjpeg-dev zlib1g-dev libxslt1-dev libpq-dev
RUN apt-get -y --force-yes install nginx redis-server supervisor
RUN apt-get -y --force-yes install python3 python3-dev python3-pip
RUN apt-get -y install python-virtualenv
RUN apt-get -y install libffi-dev gettext
RUN apt-get -y --force-yes install p7zip-full

RUN rm /bin/sh && ln -s /bin/bash /bin/sh
ENV PROJECT_ROOT /deploy/
ENV DJANGO_SETTINGS_MODULE bimbingbung.settings.docker
ENV PYTHON_VERSION ${PYTHON_VERSION:-python3}
ENV PYTHON = $PROJECT_ROOT/ve/bin/python
ENV PIP = $PROJECT_ROOT/ve/bin/pip
WORKDIR /deploy/

RUN pip install --upgrade virtualenv
RUN virtualenv -p ${PYTHON_VERSION} ${PROJECT_ROOT}/ve
RUN source ${PROJECT_ROOT}/ve/bin/activate && pip install --upgrade pip
ADD requirements.txt /deploy/
RUN source ${PROJECT_ROOT}/ve/bin/activate && pip install -r requirements.txt

COPY bimbingbung /deploy/bimbingbung
COPY users /deploy/users
COPY search /deploy/search
COPY content /deploy/content
COPY core /deploy/core
COPY home /deploy/home
COPY locale /deploy/locale
COPY survey /deploy/survey
ADD setup.py /deploy/
ADD manage.py /deploy/
ADD README.md /deploy/
ADD VERSION /deploy/

RUN mkdir -p /etc/supervisor/conf.d/
RUN mkdir -p /var/log/supervisor
RUN rm /etc/nginx/sites-enabled/default

ADD docker/nginx.conf /etc/nginx/sites-enabled/bimbingbung.conf
ADD docker/supervisor.conf /etc/supervisor/conf.d/bimbingbung.conf
ADD docker/supervisord.conf /etc/supervisord.conf
ADD docker/docker-start.sh /deploy/
ADD docker/settings.py /deploy/bimbingbung/settings/docker.py

RUN chmod a+x /deploy/docker-start.sh

EXPOSE 80

ENTRYPOINT ["/deploy/docker-start.sh"]
