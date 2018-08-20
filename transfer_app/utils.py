import configparser

from django.conf import settings

from transfer_app.models import Resource, Transfer, TransferCoordinator
import transfer_app.launchers as _launchers


def load_config(config_filepath, config_key=None):
    '''
    config_filepath is the path to a config/ini file
    config_key is the name of a section in that file
    if None, then just return the [DEFAULT] section
    '''
    config = configparser.ConfigParser()
    config.read(config_filepath)
    if config_key in config:
        d = {}
        for key in config[config_key]:
            d[key] =  config[config_key][key]
        return d
    else:
        raise configparser.NoSectionError()


def post_completion(transfer_coordinator):
    print('completed the transfers')


def get_or_create_upload_location(user):
    '''
    user is an instance of User
    TODO: write this
    '''
    return 'users-bucket'


def create_resource(serializer, user):
    '''
    This function is used to get around making API calls
    between different endpoints.  Namely, when a user requests
    the "upload" endpoint, we have to create Resource objects.
    To keep Resource creation in a central location, we extracted the logic
    out of the API view and put it here.  Then, any API endpoint needing to
    create one or more Resource instances can use this function.

    serializer is an instance of rest_framework.serializers.ModelSerializer
    user is a basic Django User (or subclass)
    '''
    serializer.is_valid(raise_exception=True)

    # if the user is NOT staff, we only let them
    # create a Resource for themself.
    if not user.is_staff:
        # if the owner specified in the request is the requesting user
        # then we approve
        try:
            many = serializer.many
        except AttributeError as ex:
            many = False
        if many:
            owner_status = []
            for item in serializer.validated_data:
                try:
                    properly_owned = item['owner'] == user
                    owner_status.append(properly_owned)
                except KeyError as ex:
                    item['owner'] = user
                    owner_status.append(True)
            if all(owner_status):
                return serializer.save()
            else:
                raise exceptions.RequestError('Tried to create a Resource attributed to someone else.')  
        else:
            try:
                if serializer.validated_data['owner'] == user:
                    return serializer.save()
                # here we block any effort to create a Resource for anyone else.
                #Raise 404 so we do not give anything away
                else:
                    raise Http404
            except KeyError as ex:
                return serializer.save(owner=user)

    # Otherwsie (if the user IS staff), we trust them to create
    # Resources for themselves or others.
    else:
        return serializer.save()

