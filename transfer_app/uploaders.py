import os
import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
#django.contrib.auth.models
#from django.contrib.auth.models import DoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.contrib.sites.models import Site

from transfer_app.base import GoogleBase, AWSBase
import transfer_app.utils as utils
from transfer_app.models import Resource, Transfer, TransferCoordinator
import transfer_app.serializers as serializers
import transfer_app.exceptions as exceptions
from transfer_app.launchers import GoogleLauncher, AWSLauncher

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
                raise exceptions.ExceptionWithMessage('''
                    Cannot assign ownership of an upload to someone other than yourself.''')
        except KeyError as ex:
            data_dict['owner'] = requesting_user.pk

    @classmethod
    def _check_keys(cls, data_dict):
        for key in cls.required_keys:
            try:
                data_dict[key]
            except KeyError as ex:
                raise exceptions.ExceptionWithMessage('The request payload did not contain the required key: %s' % key)

    @classmethod
    def _check_format(cls, upload_data, uploader_pk):

        try:
            requesting_user = get_user_model().objects.get(pk=uploader_pk)
        except ObjectDoesNotExist as ex:
            raise exceptions.ExceptionWithMessage(ex)

        # for consistent handling, take any single upload requests and
        # put inside a list
        if isinstance(upload_data, dict):
            upload_data = [upload_data,]

        for item in upload_data:
            cls._validate_ownership(item, requesting_user)
            cls._check_keys(item)

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

    source = settings.DROPBOX

    # the only required keys:
    required_keys = ['path', 'name']

    @classmethod
    def check_format(cls, upload_data, uploader_pk):
        '''
        This class method checks that the data is in the expected format

        For Dropbox data, the front-end sends a list of direct links, which we can
        directly access (e.g. via a wget request to the URL).  No other information
        is required, although one may include ownership info as well.

        If a list is sent, then it is a list of json-objects, like:
        upload_data = [{'path':'<some dropbox url>'},{'path':'<some dropbox url>'},{'path':'<some dropbox url>'}]
    
        Check each one for the required keys isted above

        If only a single item is being transferred, an object can be sent:
        upload_data = {'path':'<some dropbox url>'}
        (this object will ultimately be placed inside a list of length 1 for consistent handling)

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
    
    source = settings.GOOGLE_DRIVE
    required_keys = ['file_id', 'token', 'name']

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

    config_key_list = []
    config_file = settings.UPLOADER_CONFIG['CONFIG_PATH']

    def __init__(self, upload_data):
        #instantiate the wrapped classes:
        self.uploader = self.uploader_cls(upload_data)
        self.launcher = self.launcher_cls()
        self.config_params = utils.load_config(self.config_file, self.config_key_list)

    @classmethod
    def check_format(cls, upload_info, uploader_pk):
        return cls.uploader_cls.check_format(upload_info, uploader_pk)

    def upload(self):

        transfer_coordinator = self.uploader._transfer_setup()
        self.config_and_start_uploads(transfer_coordinator)     


class GoogleEnvironmentUploader(EnvironmentSpecificUploader, GoogleBase):

    @classmethod
    def check_format(cls, upload_info, uploader_pk):
        '''
        Check the upload request for formatting issues, etc. that are Google-specific here
        More general issues, such as those related to the uploader itself can be handled via
        the parent

        This happens before any asynchronous upload behavior, so this is a good place
        to check things like filename length, etc. that are specific to google 
        '''

        # first run the format check that is dependent on the uploader:
        # This returns a list of dicts
        upload_info = cls.uploader_cls.check_format(upload_info, uploader_pk)

        # the following section determines the final location in Google Storage for each file.
        # It places a 'destination' key in the dictionary for later use.
        # If the filenames are invalid, it throws an exception.
        for item_dict in upload_info:
            bucket_name = os.path.join(settings.CONFIG_PARAMS['storage_bucket_prefix'], str(item_dict['owner']))
            item_name = item_dict['name']
            full_item_name = os.path.join(bucket_name, item_name)
        
            # check the validity.  GoogleStorage requires that objects are 1-1024 bytes when UTF-8 encoded
            # more info: https://cloud.google.com/storage/docs/naming
            min_length = 1
            max_length = 1024
            bytes = len(full_item_name.encode('utf-8'))
            if bytes < min_length:
                error_msg = 'The file with name %s is too short.  Please change it and try again.' % item_name
                raise exceptions.FilenameException(error_msg)
            elif bytes > max_length:
                error_msg = 'The file with name %s is too long for our storage system.  Please change and try again.' % item_name
                raise exceptions.FilenameException(error_msg)
            else:
                item_dict['destination'] = full_item_name

        return upload_info

    def __init__(self, upload_data):
        self.config_key_list.extend(GoogleBase.config_keys)
        super().__init__(upload_data)

    def config_and_start_uploads(self, transfer_coordinator):    

        for item in self.uploader.upload_data:
            owner = get_user_model().objects.get(pk=item['owner'])
            try:
                filesize_in_bytes = item['size_in_bytes']
            except KeyError as e:
                filesize_in_bytes =  0
                item['size_in_bytes'] = 0

            r = Resource(
                source = self.uploader.source,
                path = item['path'],
                owner = owner,
                size = filesize_in_bytes
            )
            r.save()

            t = Transfer(
                 download=False,
                 resource=r,
                 destination=item['destination'],
                 coordinator=transfer_coordinator
            )
            t.save()

            # finally add the transfer primary key to the dictionary so we will
            # be able to track the transfers
            item['transfer_pk'] = t.pk        


class GoogleDropboxUploader(GoogleEnvironmentUploader):
    uploader_cls = DropboxUploader
    config_keys = ['dropbox_in_google',]

    def __init__(self, upload_data):
        self.config_key_list.extend(GoogleDropboxUploader.config_keys)
        super().__init__(upload_data)

    def config_and_start_uploads(self, transfer_coordinator):

        # use the parent class to setup the other database components
        super().config_and_start_uploads(transfer_coordinator)

        custom_config = self.config_params.copy()
        disk_size_factor = float(custom_config['disk_size_factor'])
        min_disk_size = int(float(custom_config['min_disk_size']))

        # construct a callback so the worker can communicate back to the application server:
        callback_url = reverse('transfer-complete')
        current_site = Site.objects.get_current()
        domain = current_site.domain
        full_callback_url = 'https://%s/%s' % (domain, callback_url)

        # need to specify the full path to the startup script
        startup_script_url = os.path.join(settings.CONFIG_PARAMS['storage_base'], custom_config['startup_script_path'])

        for i, item in enumerate(self.uploader.upload_data):

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
            metadata_list = []
            metadata_list.append({'key':'startup-script-url', 'value':startup_script_url})
            metadata_list.append({'key':'transfer_pk', 'value':item['transfer_pk']})
            metadata_list.append({'key':'token', 'value':settings.CONFIG_PARAMS['token']})
            metadata_list.append({'key':'enc_key', 'value':settings.CONFIG_PARAMS['enc_key']})
            metadata_list.append({'key':'resource_url', 'value':item['path']}) # the special Dropbox link
            metadata_list.append({'key':'google_zone', 'value': settings.CONFIG_PARAMS['google_zone']})
            metadata_list.append({'key':'google_project', 'value':settings.CONFIG_PARAMS['google_project_id']})
            metadata_list.append({'key': 'destination', 'value': item['destination']})

            config['metadata']['items'] = metadata_list
            self.launcher.go(config)
 

class GoogleDriveUploader(GoogleEnvironmentUploader):
    uploader_cls = DriveUploader
    config_keys = ['drive_in_google',]

    def __init__(self, upload_data):
        self.config_key_list.extend(GoogleDriveUploader.config_keys)
        super().__init__(upload_data)

    def config_and_start_uploads(self, transfer_coordinator):

        # use the parent class to setup the other database components
        super().config_and_start_uploads(transfer_coordinator)

        custom_config = self.config_params.copy()
        disk_size_factor = float(custom_config['disk_size_factor'])
        min_disk_size = int(float(custom_config['min_disk_size']))

        # construct a callback so the worker can communicate back to the application server:
        callback_url = reverse('transfer-complete')
        current_site = Site.objects.get_current()
        domain = current_site.domain
        full_callback_url = 'https://%s/%s' % (domain, callback_url)

        # need to specify the full path to the startup script
        startup_script_url = os.path.join(settings.CONFIG_PARAMS['storage_base'], custom_config['startup_script_path'])

        for i, item in enumerate(self.uploader.upload_data):

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
            metadata_list = []
            metadata_list.append({'key':'startup-script-url', 'value':startup_script_url})
            metadata_list.append({'key':'transfer_pk', 'value':item['transfer_pk']})
            metadata_list.append({'key':'token', 'value':settings.CONFIG_PARAMS['token']})
            metadata_list.append({'key':'enc_key', 'value':settings.CONFIG_PARAMS['enc_key']})
            metadata_list.append({'key':'drive_file_id', 'value':item['path']}) # the file ID provided by google
            metadata_list.append({'key':'drive_token', 'value':item['token']}) # the oauth2 access token provided by google
            metadata_list.append({'key':'google_zone', 'value': settings.CONFIG_PARAMS['google_zone']})
            metadata_list.append({'key':'google_project', 'value':settings.CONFIG_PARAMS['google_project_id']})
            metadata_list.append({'key': 'destination', 'value': item['destination']})

            config['metadata']['items'] = metadata_list
            self.launcher.go(config)


class AWSEnvironmentUploader(EnvironmentSpecificUploader):
    launcher_cls = AWSLauncher


class AWSDropboxUploader(AWSEnvironmentUploader):
    uploader_cls = DropboxUploader
    config_key = 'dropbox_in_aws'


class AWSDriveUploader(AWSEnvironmentUploader):
    uploader_cls = DriveUploader
    config_key = 'drive_in_aws'


def get_uploader(source):
    '''
    Based on the compute environment and the source of the upload
    choose the appropriate class to use.
    '''

    # This defines a two-level dictionary from which we can choose
    # a class.  Additional sub-classes of EnvironmentSpecificUploader
    # need to be in this if they are to be used.  Otherwise, the application
    # will 'not know' about the class
    class_mapping = {
        settings.GOOGLE : {
            settings.GOOGLE_DRIVE : GoogleDriveUploader,
            settings.DROPBOX : GoogleDropboxUploader,
        },
        settings.AWS : {
            settings.GOOGLE_DRIVE : AWSDriveUploader,
            settings.DROPBOX : AWSDropboxUploader,
        }
    }
    environment = settings.CONFIG_PARAMS['compute_environment']
    try:
        return class_mapping[environment][source]
    except KeyError as ex:
        raise exceptions.ExceptionWithMessage('''
            You did not specify an uploader implementation for:
                Compute environment: %s
                Upload source: %s
        ''' % (environment, source))

