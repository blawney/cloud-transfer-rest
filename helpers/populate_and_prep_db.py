import sys
import os
import datetime
import random

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.realpath(os.pardir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cccb_transfers.settings')

import django
from django.conf import settings
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

import cccb_transfers.utils as utils
from transfer_app.models import Resource, Transfer, TransferCoordinator

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
        #sys.exit(0)

    file_list = [x.strip() for x in params['files_to_transfer'].split(',')]
    size_list = [x.strip() for x in params['file_sizes_in_bytes'].split(',')]
    if len(file_list) != len(size_list):
        print('''Check your live test configuration template-- 
                 you need the same number of items in both the list of files and the file sizes''')
        sys.exit(1)
 
    for f,s in zip(file_list, size_list):
        print('Creating resource for path=%s' % f)
        r = Resource(path=f,
            size=s,
            owner=test_user
        )
        r.save()

    print('Done populating for live test.  Moving onto population for UI')

    # Here we populate some items for populating the UI for a dummy user
    # We have some downloads above (Which will actually exist for a real transfer)
    # We add a couple of "inactive" Resources here (since they have been "downloaded").
    # The history needs to reference Transfers, which, in turn, reference Resources
    inactive_resource_sources = [
        settings.GOOGLE,
        settings.GOOGLE,
        settings.DROPBOX,
        settings.GOOGLE_DRIVE
    ]
    inactive_resource_paths = [
        'xyz://dummy-bucket/file_1.txt', 
        'xyz://dummy-bucket/file_2.txt',
        'https://dropbox-link/file_3.txt', # an upload from dropbox
        'abcd1234', #mock the ID we get from Drive, which is effectively a path
    ]
    inactive_resource_sizes = [1200, 2900000000, 550, 7801]
    inactive_resource_dates = [
        datetime.datetime(year=2017, month=3, day=22), 
        datetime.datetime(year=2018, month=4, day=19),
        datetime.datetime(year=2018, month=5, day=19),
        datetime.datetime(year=2018, month=5, day=20),
    ]
    inactive_resources = []
    for src,p,s,d in zip(inactive_resource_sources, 
            inactive_resource_paths, 
            inactive_resource_sizes, 
            inactive_resource_dates
        ):
        r = Resource(path=p,
            source=src,
            size=s,
            owner=test_user, 
            date_added = d,
            is_active = False
        )
        r.save()
        inactive_resources.append(r)
        

    # We populate a history here, so there is content in that view.
    for r in inactive_resources:

        # Make up some random time offsets so we can mock "real"
        # transfer start and finish times (relative to the date
        # the mock resource was "added")
        dt1 = datetime.timedelta(days=random.randint(0,5),
                 hours=random.randint(1,12),
                 minutes=random.randint(0,59),
                 seconds=random.randint(0,59)
             )
        dt2 = datetime.timedelta(days=random.randint(0,5),
                 hours=random.randint(1,12),
                 minutes=random.randint(0,59),
                 seconds=random.randint(0,59)
             )
        start_time = r.date_added + dt1
        finish_time = start_time + dt2
        if (r.source == settings.GOOGLE):
            download_state = True
             # just take all of the downloads to dropbox, does not matter
            destination = settings.DROPBOX
        else: # mocked upload
            download_state = False
            # if it was an upload, then the destination is a bucket, so make up a name
            destination = 'xyz://mock-bucket/%s' % os.path.basename(r.path)

        # since we are creating Transfer objects below, we need
        # them to refer to a TransferCoordinator.  Just make 
        # a single TransferCoordinator for each Transfer, rather 
        # than grouping them as would happen when a user transfers >1 files
        tc = TransferCoordinator(completed=True, 
                 start_time=start_time, 
                 finish_time=finish_time
        )
        tc.save()

        t = Transfer(download=download_state, 
                resource=r, 
                completed=True,
                success=True,
                start_time = start_time,
                finish_time = finish_time,
                destination = destination,
                # just make the originator same as the resource owner (does not have to be)
                originator=r.owner, 
                coordinator=tc
            )
        t.save()


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
