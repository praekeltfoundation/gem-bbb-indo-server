FROM ubuntu:14.04
MAINTAINER Colin Alston <colin@praekelt.com>
RUN apt-get update && apt-get -y --force-yes install libjpeg-dev zlib1g-dev libxslt1-dev libpq-dev nginx redis-server supervisor python3-dev python3-pip
RUN apt-get -y install libffi-dev gettext

RUN pip install --upgrade pip

ENV PROJECT_ROOT /deploy/
ENV DJANGO_SETTINGS_MODULE bimbingbung.settings.docker

WORKDIR /deploy/

COPY bimbingbung /deploy/bimbingbung
COPY locale /deploy/locale
ADD manage.py /deploy/
ADD requirements.txt /deploy/
ADD README.md /deploy/
ADD VERSION /deploy/

RUN pip3 install -e .

RUN mkdir -p /etc/supervisor/conf.d/
RUN mkdir -p /var/log/supervisor
RUN rm /etc/nginx/sites-enabled/default

ADD docker/nginx.conf /etc/nginx/sites-enabled/bimbingbung.conf
ADD docker/supervisor.conf /etc/supervisor/conf.d/bimbingbung.conf
ADD docker/supervisord.conf /etc/supervisord.conf
ADD docker/docker-start.sh /deploy/
ADD docker/settings.py /deploy/gem/settings/docker.py

RUN cd /usr/local/bin \
    && ln -s easy_install-3.4 easy_install \
    && ln -s idle3 idle \
    && ln -s pydoc3 pydoc \
    && ln -s python3 python \
    && ln -s python-config3 python-config

RUN chmod a+x /deploy/docker-start.sh

EXPOSE 80

ENTRYPOINT ["/deploy/docker-start.sh"]
