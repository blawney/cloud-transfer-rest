import sys
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cccb_transfers.settings')

import django
from django.conf import settings
django.setup()

from django.contrib.auth import get_user_model

import cccb_transfers.utils as utils
from transfer_app.models import Resource


def populate():
    # read the live test config to create our dummy user and resource for live testing:
    params = settings.LIVE_TEST_CONFIG_PARAMS
    user_model = get_user_model()
    try:
        test_user = user_model.objects.create_user(username=params['test_username'], 
            email=params['test_email'],
            password=params['test_password']
        )
    except django.db.utils.IntegrityError as ex:
        print('Could not create user.  Likely already exists.')
        sys.exit(0)

    r = Resource(path=params['file_to_transfer'],
            size=params['file_size_in_bytes'],
            owner=test_user
    )
    r.save()

    print('Done populating.')

if __name__ == '__main__':
    print('Starting database population...')
    populate()
