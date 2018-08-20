import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

import transfer_app.utils as utils
from transfer_app.models import Resource, Transfer, TransferCoordinator
import transfer_app.serializers as serializers


class Uploader(object):

    def __init__(self, upload_data):
        self.upload_data = upload_data

    #@classmethod
    #def _add_source(cls, data_dict):
    #    data_dict['source'] = cls.source

    @classmethod
    def _validate_ownership(cls, data_dict, requesting_user):
        try:
            # if 'owner' was included in the object, check that the owner PK matches theirs
            # unless the requet was issued by an admin
            intended_owner = data_dict['owner']
            if (not requesting_user.is_staff) and (requesting_user.pk != intended_owner):
                raise exceptions.RequestError('''
                    Cannot assign ownership of an upload to someone other than yourself.''')
        except KeyError as ex:
            data_dict['owner'] = requesting_user.pk

    @classmethod
    def _check_keys(cls, data_dict):
                for key in cls.required_keys:
                    try:
                        data_dict[key]
                    except KeyError as ex:
                        raise exceptions.RequestError('The request payload did not contain the required key: %s ' % key)

    @classmethod
    def _check_format(cls, upload_data, uploader_pk):

        requesting_user = get_user_model().objects.get(pk=uploader_pk)

        # for consistent handling, take any single upload requests and
        # put inside a list
        if isinstance(upload_data, dict):
            upload_data = [upload_data,]

        for item in upload_data:
            cls._validate_ownership(item, requesting_user)
            cls._check_keys(item)
            #cls._add_source(item)

        return upload_data

    def _transfer_setup(self):
        '''
        This creates the proper database instances for the uploads- it creates
        the proper Resource, Transfer, and TransferCoordinator instances

        This function expects that self.upload_data is a list and each
        item in the list is a dict.  Each dict NEEDS to have 'owner' and
        'path' among the keys
        '''
        tc = TransferCoordinator()
        tc.save()

        for item in self.upload_data:
            owner = get_user_model().objects.get(pk=item['owner'])
            try:
                filesize_in_bytes = item['size_in_bytes']
            except KeyError as e:
                filesize_in_bytes =  0
            r = Resource(
                source = self.source,
                path = item['path'],
                owner = owner,
                size = filesize_in_bytes
            )
            r.save()

            destination = utils.get_or_create_upload_location(owner)
            t = Transfer(
                 download=False,
                 resource=r,
                 destination=destination,
                 coordinator=tc 
            )
            t.save()
       
        return tc


class DropboxUploader(Uploader):
    '''
    The Dropbox upload works by using Dropbox's browser-based chooser (javascript based).
    The front-end will send a POST request containing URLs for the files to transfer (and
    other information like file size).  From there, we can parallelize the upload to our 
    storage system.

    The wrapped launcher attribute is specific to the service being used (GCP, AWS)
    so the logic of starting a VM to do the transfer is contained there
    '''

    source = settings.UPLOAD_SOURCES['DROPBOX']

    # the only required keys:
    required_keys = ['path',]

    @classmethod
    def check_format(cls, upload_data, uploader_pk):
        '''
        This class method checks that the data is in the expected format

        For Dropbox data, the front-end sends a list of direct links, which we can
        directly access (e.g. via a wget request to the URL).  No other information
        is required, although one may include ownership info as well.

        If a list is sent, then it is a list of json-objects, like:
        upload_data = [{'path':'<some dropbox url>'},{'path':'<some dropbox url>'},{'path':'<some dropbox url>'}]
    
        Check each one for the 'path' key

        If only a single item is being transferred, an object can be sent:
        upload_data = {'path':'<some dropbox url>'}

        uploader_pk is the primary key for the User requesting the upload.  In the case that
        the transfers specify an intended owner, we have to verify that the requesting user has permissions.
        For example, an admin may initiate an upload on someone else's behalf, and hence the request would
        contain someone other user's PK.  However, if a non-admin user tries to do the same, we need to
        reject the request
        '''
        return cls._check_format(upload_data, uploader_pk)
        

    def _transfer_setup(self):
        '''
        For the case of a Dropbox upload, self.upload_data is already 
        in the correct format for using in the parent method since it has 'path'
        and 'owner' keys
        '''
        return super()._transfer_setup()

        

class DriveUploader(Uploader):
    '''
    The Google Drive upload works by using Google Picker, which is a javascript based
    tool that handles the oauth2 flow.  The client-side UI (provided by Google) allows
    the user to select files.  After selecting files, a callback function will send an 
    access token and the "primary keys" (a unique identifier on Google Drive's end) 
    of the files the user has selected. 
    '''
    
    source = settings.UPLOAD_SOURCES['GOOGLE_DRIVE']
    required_keys = ['file_id', 'token',]

    @classmethod
    def check_format(cls, upload_data, uploader_pk):
        '''
        This class method checks that the data is in the expected format

        For Drive data, the front-end sends a list of json-objects.  Each has an oauth2
        token and a file ID.  The token is needed to access the user's content and the file ID
        uniquely identifies the file when we use the Drive API.

        If a list is sent, then it is a list of json-objects, like:
        upload_data = [{'file_id':'<some ID string>', 'token': '<some access token>'},
                       {'file_id':'<some ID string>', 'token': '<some access token>'}, ...]
   

        If only a single item is being transferred, an object can be sent:
        upload_data = {'file_id':'<some ID string>', 'token': '<some access token>'}

        uploader_pk is the primary key for the User requesting the upload.  In the case that
        the transfers specify an intended owner, we have to verify that the requesting user has permissions.
        For example, an admin may initiate an upload on someone else's behalf, and hence the request would
        contain someone other user's PK.  However, if a non-admin user tries to do the same, we need to
        reject the request
        '''
        return cls._check_format(upload_data, uploader_pk)

    def _reformat_data(self):
        '''
        For GoogleDrive uploads, we receive the required keys as given in the 'required_keys' variable above
        In the process of validating the request info (already performed- and looks good), we added the 'owner' 
        primary key.  Hence, self.upload_data looks like:
            [
                {'file_id':'<some ID string>', 'token': '<some access token>' , 'owner': <pk>},
                {'file_id':'<some ID string>', 'token': '<some access token>', 'owner': <pk>},
                ...
            ] 
        To properly work with Uploader._transfer_setup, we need to massage the keys in each dict of that list
        In this case, we need to add a 'path' key.  Since the file_id is an analog of a path (in the sense that
        it uniquely identifies something), we just use that.
        '''
        for item in self.upload_data:
            item['path'] = item['file_id']

    def _transfer_setup(self):
        self._reformat_data()
        return super()._transfer_setup()



class EnvironmentSpecificUploader(object):

    config_file = settings.UPLOADER_CONFIG['CONFIG_PATH']

    def __init__(self, upload_data):
        #instantiate the wrapped classes:
        self.uploader = self.uploader_cls(upload_data)
        self.launcher = self.launcher_cls()
        self.config_params = utils.load_config(self.config_file, self.config_key)

    @classmethod
    def check_format(cls, upload_info, uploader_pk):
        return cls.uploader_cls.check_format(upload_info, uploader_pk)

    def upload(self):

        # creates the necessary database objects and returns a TransferCoordinator:
        transfer_coordinator = self.uploader._transfer_setup()
        self.config_and_start_uploads(transfer_coordinator)     


class GoogleDropboxUploader(EnvironmentSpecificUploader):
    uploader_cls = DropboxUploader
    launcher_cls = GoogleLauncher
    config_key = 'dropbox_in_google'

    # A dictionary used to configure the machine at startup.
    # Parameters specific to each job will be added for each upload task
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

    def config_and_start_uploads(self, transfer_coordinator):

        custom_config = self.config_params.copy()
        disk_size_factor = float(custom_config['disk_size_factor'])
        min_disk_size = int(float(custom_config['min_disk_size']))
        callback_url = reverse('transfer-complete')

        for i, item in enumerate(self.upload_data):

            config = self.base_config.copy()

            instance_name = '%s-%s-%s' % (custom_config['instance_name_prefix'], \
                datetime.datetime.now().strftime('%m%d%y%H%M%S'), \
                i                
            )
            config['name'] =  instance_name

            config['machineType'] = custom_config['machine_type']

            # approx size in Gb so we can size the VM appropriately
            size_in_gb = item['size_in_bytes']/1e9
            target_disk_size = int(disk_size_factor*size_in_gb)
            if target_disk_size < min_disk_size:
                target_disk_size = min_disk_size
            disk_config = {
                'boot': True,
                'autoDelete': True,
                'initializeParams':{
                    'sourceImage': custom_config['source_disk_image'],
                    'diskSizeGb': target_disk_size
                }
            }
            config['disks'].append(disk_config)

            # now do the other metadata commands
            
            


class AWSDropboxUploader(EnvironmentSpecificUploader):
    uploader_cls = DropboxUploader
    launcher_cls = AWSLauncher
    config_key = 'dropbox_in_aws'

class GoogleDriveUploader(EnvironmentSpecificUploader):
    uploader_cls = DriveUploader
    launcher_cls = GoogleLauncher
    config_key = 'drive_in_google'

class AWSDriveUploader(EnvironmentSpecificUploader):
    uploader_cls = DriveUploader
    launcher_cls = AWSLauncher
    config_key = 'drive_in_aws'


def get_uploader(source):
    environment = settings.COMPUTE_ENVIRONMENT
    upload_source_dict = settings.UPLOADER_CONFIG['UPLOAD_SOURCES']
    if source == upload_source_dict['DROPBOX']:
        if environment == settings.GOOGLE:
            return GoogleDropboxUploader
        elif environment == settings.AWS:
            return AWSDropboxUploader
        else:
            raise NotImplemented
    elif source == upload_source_dict['GOOGLE_DRIVE']:
        if environment == settings.GOOGLE:
            return GoogleDriveUploader
        elif environment == settings.AWS:
            return AWSDriveUploader
        else:
            raise NotImplemented
    else:
        raise NotImplemented
