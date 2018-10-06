#!/bin/bash
set -e

# This script is run upon entering the container.  It fills in various 
# templates and queries the user about configuration options, parameters.

cd $APP_ROOT

# Fill out the general config and copy the templates
# that do not need configuration
python3 helpers/fill_config_templates.py
cd config
cp downloaders.template.cfg downloaders.cfg 
cp uploaders.template.cfg uploaders.cfg 
cp live_tests.template.cfg live_tests.cfg 

cd $APP_ROOT

# Need to add parameters (e.g. api key) into javascript file:
python3 helpers/fill_javascript.py

# create log dir:
export LOGDIR="/var/log/transfer_app"
export CELERY=$(which celery)
mkdir -p $LOGDIR
touch $LOGDIR/redis.log
touch $LOGDIR/celery_beat.log
touch $LOGDIR/celery_worker.log

# Fill-out and copy files for supervisor-managed processes:
python3 helpers/fill_supervisor_templates.py \
    /etc/supervisor/conf.d \
    etc/celery_worker.conf \
    etc/celery_beat.conf \
    etc/redis.conf

# start supervisor:
supervisord --configuration /etc/supervisor/supervisord.conf
supervisorctl reread && supervisorctl update

# setup database:
python3 manage.py makemigrations
python3 manage.py migrate

# add some content for non-trivial views (using the test account)
python3 helpers/populate_and_prep_db.py

python3 manage.py createsuperuser
