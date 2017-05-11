FROM praekeltfoundation/django-bootstrap:py3

# Install gettext for translations
RUN apt-get-install.sh libjpeg-dev zlib1g-dev libxslt1-dev libpq-dev libffi-dev gettext p7zip-full

# Not sure why we're removing sh, but I guess we're making bash the default
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

ENV PROJECT_ROOT /app/ \
    DJANGO_SETTINGS_MODULE bimbingbung.settings.docker

# adding custom nginx.conf (inherited from django-bootstrap)
COPY docker.nginx.conf /etc/nginx/conf.d/django.conf

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN LANGUAGE_CODE=en django-admin compilemessages -l id && \
    django-admin collectstatic --noinput

CMD ["bimbingbung.wsgi:application", "--timeout", "1800"]
