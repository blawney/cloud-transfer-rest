from transfer_app.launchers import GoogleLauncher, AWSLauncher

class GoogleBase(object):
    launcher_cls = GoogleLauncher
    config_keys = ['google',]

    # A dictionary used to configure the machine at startup.
    # Parameters specific to each job will be added for each upload task
    # This dictionary is consistent regardless of the upload file source
    base_config = {

        # Specify the boot disk and the image to use as a source.
        'disks': [],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/compute',
                'https://www.googleapis.com/auth/devstorage.full_control',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        'metadata': {}
    }

class AWSBase(object):
    pass
