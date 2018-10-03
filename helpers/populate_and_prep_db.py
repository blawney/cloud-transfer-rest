import sys
import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.realpath(os.pardir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cccb_transfers.settings')

import django
from django.conf import settings
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

import cccb_transfers.utils as utils
from transfer_app.models import Resource


def populate():
    # read the live test config to create our dummy user and resource for live testing:
    params = settings.LIVE_TEST_CONFIG_PARAMS
    user_model = get_user_model()
    try:
        test_user = user_model.objects.create_user(email=params['test_email'],
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

def edit_domain():
    expected_site_id = settings.SITE_ID
    site = Site.objects.get(pk=expected_site_id)
    site.name = settings.ALLOWED_HOSTS[0]
    site.domain = settings.ALLOWED_HOSTS[0]
    site.save()


if __name__ == '__main__':
    print('Starting database population for live testing...')
    populate()

    print('Editing database for your domain...')
    edit_domain()
