FROM python:3.12-slim-bookworm

LABEL maintainer="Felipe Bañados Schwerter <banadoss@ualberta.ca>"

ARG OAHPA_UID_GID=60006

RUN apt-get update && apt-get install -y curl sqlite3 gettext

RUN curl https://apertium.projectjj.com/apt/install-nightly.sh | bash

RUN apt-get update && apt-get install -y --no-install-recommends hfst supervisor nginx

RUN python -m ensurepip

# Install pipenv
RUN pip install pipenv

# Create the non-root user/group that will own the application code
RUN groupadd --gid ${OAHPA_UID_GID} oahpa \
 && useradd --no-log-init --gid oahpa \
    --uid ${OAHPA_UID_GID} oahpa --create-home

# Install and build dependencies,
# then remove build-time dependencies to keep the image slim!
RUN  mkdir /app/ \
 && chown oahpa /app

# As the non-root user...
USER oahpa

# Set working directory
WORKDIR /app

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Import database
COPY containerized_deploy/crk_oahpa_sqlite.sql.gz /tmp/crk_oahpa_sqlite.sql.gz
COPY containerized_deploy/init_db.sh /tmp/init_db.sh
RUN mkdir /app/crk_oahpa_project
RUN bash /tmp/init_db.sh

# Configuration files
COPY containerized_deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY containerized_deploy/uwsgi.ini /etc/uwsgi/uwsgi.ini
COPY containerized_deploy/nginx.conf /etc/nginx/nginx.conf
COPY containerized_deploy/my.cnf /etc/mysql/my.cnf

# numra needs this
COPY containerized_deploy/lookup /usr/local/bin/lookup

# media is served statically directly from the root by nginx
# TODO I believe this is the same folder for every instance, but unsure
#      (It should be!)
# TODO Call instead to collectstatic
COPY media /var/www/html

COPY containerized_deploy/uwsgi_vassals /etc/uwsgi/vassals

# Copy in files we need to run the project vessels
COPY --chown=oahpa crk_oahpa_project /app/crk_oahpa_project

# Copy settings_not_in_svn.py to where it needs to be.
RUN cp /app/crk_oahpa_project/settings_not_in_svn.py /app/crk_oahpa_project/crk_oahpa/settings_not_in_svn.py

# Update the paths in these settings_not_in_svn.py files
RUN find . -name settings_not_in_svn.py -exec sed --in-place -e 's,/home/oahpa/,/app/,g' {} \;

# This replaces the SECRET_KEY = '...' with a new secret key for each lang
COPY containerized_deploy/roll_keys.sh /tmp/roll_keys.sh
RUN /tmp/roll_keys.sh

# Compile translations for all instances
RUN cd /app && pipenv run django-admin compilemessages
RUN cd /app/crk_oahpa_project && pipenv run python manage.py migrate

CMD [ "/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf" ]

