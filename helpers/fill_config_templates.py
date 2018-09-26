'''
This script guides users to answer questions and fills in the
details in config and settings files as appropriate.
'''

import os
import sys
import re
from jinja2 import Environment, FileSystemLoader
from Crypto.Cipher import DES

def take_inputs():

    params = {}

    print('Please enter inputs as prompted\n')

    domain = input('Enter your domain.  Note that callbacks will often not work with raw IPs : ')
    params['domain'] = domain

    cloud_environment = input('Which cloud provider? (google, aws): ')
    cloud_environment = cloud_environment.lower()
    if cloud_environment == 'google':
        google_project = input('Enter the project ID: ')
        google_zone = input('Enter the desired zone (e.g. "us-east1-b"): ')

        params['cloud_environment'] = cloud_environment
        params['google_project'] = google_project 
        params['google_zone'] = google_zone

    elif cloud_environment == 'aws':
        print('Have not implemented AWS config')
    else:
        sys.exit(1)

    use_at_least_one_service = False
    use_dropbox = input('Are you connecting to Dropbox?: (y/n) ')[0].lower()
    if use_dropbox == 'y':
        use_at_least_one_service = True
        dropbox_client_id = input('Enter the Dropbox client ID: ')
        dropbox_secret = input('Enter the Dropbox secret: ')

        params['dropbox_client_id'] = dropbox_client_id
        params['dropbox_secret'] = dropbox_secret

    use_drive = input('Are you connecting to Google Drive?: (y/n) ')[0].lower()
    if use_drive == 'y':
        use_at_least_one_service = True
        drive_client_id = input('Enter the Drive client ID: ')
        drive_secret = input('Enter the Drive secret: ')

        params['drive_client_id'] = drive_client_id
        params['drive_secret'] = drive_secret

    if not use_at_least_one_service:
        print('You need to select at least one storage provider.')
        sys.exit(1)

    accepted = False
    while not accepted:
        storage_bucket_prefix = input('Enter a prefix for storage buckets that will be created (lowercase letters, numbers, and dashes are accepted): ')
        m = re.match('[a-z0-9-]+', storage_bucket_prefix)
        if m.group() != storage_bucket_prefix:
            print('We enforce stricter guidelines than the storage providers and only allow lowercase letters, numbers, and dashes.  Try again.')
        else:
            params['storage_bucket_prefix'] = storage_bucket_prefix
            accepted = True

    accepted = False
    while not accepted:
        app_token = input('''Enter a series of characters (letters/numbers) that is a multiple of 8.  
                              This should be relatively long, and allows worker machines to communicate with the main machine.  Enter:  ''')
        if (len(app_token.encode('utf-8')) % 8)  != 0:
            print('The token needs to be a multiple of 8 in length (when cast as a byte string).  Try again')
        else:
            params['app_token'] = app_token
            accepted = True

    accepted = False
    while not accepted:
        app_token_key = input('Enter a series of 8 characters (letters/numbers) to be used for encryptping the token: ')
        if len(app_token_key.encode('utf-8')) != 8:
            print('The key needs to be 8 bytes long.  Try again.')
        else:
            params['app_token_key'] = app_token_key
            accepted = True

    return params


def fill_template(config_dir, params):
    env = Environment(loader=FileSystemLoader(config_dir))
    template = env.get_template('general.template.cfg')
    with open(os.path.join(config_dir, 'general.cfg'), 'w') as outfile:
        outfile.write(template.render(params))

def fill_settings(params):
    pattern = os.path.join(os.environ['APP_ROOT'], '*', 'settings.template.py')
    matches = glob.glob(pattern)
    if len(matches) == 1:
        template_path = matches[0]
        settings_dir = os.path.dirname(template_path)
        env = Environment(loader=FileSystemLoader(settings_dir))
        template = env.get_template(os.path.basename(template_path))
        with open(os.path.join(settings_dir, 'settings.py'), 'w') as outfile:
            outfile.write(template.render(params))
    else:
        print('Found multiple files matching the pattern %s.  This should not be the case' % pattern)
        sys.exit(1)

if __name__ == '__main__':
    config_dir = os.path.join(os.environ['APP_ROOT'], 'config')
    params = take_inputs()
    fill_template(config_dir, params)

    fill_settings(params)
