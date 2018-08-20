import base64
import datetime
from Crypto.Cipher import DES

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.conf import settings

from rest_framework import generics, permissions, renderers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.exceptions import ParseError
from rest_framework.views import exception_handler, APIView

from django_filters.rest_framework import DjangoFilterBackend

from transfer_app.models import Resource, Transfer, TransferCoordinator
from transfer_app.serializers import ResourceSerializer, \
     TransferSerializer, \
     TransferCoordinatorSerializer, \
     UserSerializer
import transfer_app.utils as utils
import transfer_app.exceptions as exceptions
import transfer_app.tasks as transfer_tasks
import transfer_app.uploaders as _uploaders


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'resources': reverse('resource-list', request=request, format=format),
        'transfers': reverse('transfer-list', request=request, format=format)
    })


class UserList(generics.ListCreateAPIView):
    '''
    This allows:
        GET: listing of all Users
        POST: create new User

    This view is limited to users with elevated/admin privileges
    '''
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    '''
    This allows:
        GET: details of specific User
        PUT: edit details of the User
        DELETE: remove User

    This view is limited to users with elevated/admin privileges
    '''
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)
    

class ResourceList(generics.ListCreateAPIView):
    '''
    This endpoint allows us to list or create Resources
    See methods below regarding listing logic and creation logic
    Some filtering can be added at some point
    '''
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('is_active',)
    
    def get_queryset(self):
        '''
        This overrides the get_queryset method of rest_framework.generics.GenericAPIView
        This allows us to return only Resource instances belonging to the user.
        If an admin is requesting, then we return all
        '''
        queryset = super(ResourceList, self).get_queryset()
        if not self.request.user.is_staff:
            queryset = Resource.objects.user_resources(self.request.user)
        return queryset


    def create(self, request, *args, **kwargs):
        '''
        This override provides us with the ability to create multiple instances
        Pretty much a verbatim copy of the implementation from CreateMixin except
        that we add the many=... kwarg when we call get_serializer
        '''
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        utils.create_resource(serializer, self.request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ResourceDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        '''
        Custom behavior for object retrieval- admins can get anything
        Regular users can only get objects they own.  
        Instead of the default 403 (which exposes that a particular object
        does exist), return 404 if they are not allowed to access an object.
        '''
        obj = super(ResourceDetail, self).get_object()
        if (self.request.user.is_staff) or (obj.get_owner() == self.request.user):
            return obj
        else:
            raise Http404


class UserResourceList(generics.ListAPIView):
    '''
    This lists the Resource instances for a particular user
    This view is entirely protected-- only accessible by staff
    Since regular users can only see the Resources they own,
    they can just use the "vanilla" listing endpoint
    '''
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('is_active',)

    def get_queryset(self):
        user_pk = self.kwargs['user_pk']
        try:
            user = User.objects.get(pk=user_pk)
            return Resource.objects.user_resources(user)
        except ObjectDoesNotExist as ex:
            raise Http404


class TransferList(generics.ListAPIView):
    '''
    This only allows a listing.  Creation of Transfer objects
    is handled by a TransferCoordinator.  We cannot explicitly
    create Transfer instances via the API since they would be 
    "untracked"
    '''
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('completed', 'success', 'download')

    def get_queryset(self):
        '''
        This overrides the get_queryset method of rest_framework.generics.GenericAPIView
        This allows us to return only Transfer instances belonging to the user.
        If an admin is requesting, then we return all
        '''
        queryset = super(TransferList, self).get_queryset()
        if not self.request.user.is_staff:
            queryset = Transfer.objects.user_transfers(self.request.user)
        return queryset


class TransferDetail(generics.RetrieveAPIView):
    '''
    Here we allow only retrieval of objects.  We have no reason to edit or destroy
    info about the Transfers
    '''
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        '''
        Custom behavior for object retrieval- admins can get anything
        Regular users can only get objects they own.  
        Instead of the default 403 (which exposes that a particular object
        does exist), return 404 if they are not allowed to access an object.
        '''
        obj = super(TransferDetail, self).get_object()
        if (self.request.user.is_staff) or (obj.get_owner() == self.request.user):
            return obj
        else:
            raise Http404


class UserTransferList(generics.ListAPIView):
    '''
    This lists the Transfer instances for a particular user
    This view is entirely protected-- only accessible by staff
    Since regular users can only see the Resources they own,
    they can just use the "vanilla" listing endpoint
    '''
    serializer_class = TransferSerializer
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('completed', 'success', 'download')

    def get_queryset(self):
        user_pk = self.kwargs['user_pk']
        try:
            user = User.objects.get(pk=user_pk)
            # use Django's lookup syntax-- filters Transfers where the owner attribute
            # of the referenced Resource is our requested user.
            return Transfer.objects.user_transfers(user)
        except ObjectDoesNotExist as ex:
            raise Http404


class BatchList(generics.ListAPIView):
    '''
    This only allows a listing of the TransferCoordinators.  
    Creation of TransferCoordinator objects is handled 
    elsewhere.
    '''
    queryset = TransferCoordinator.objects.all()
    serializer_class = TransferCoordinatorSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('completed',)

    def get_queryset(self):
        '''
        This overrides the get_queryset method of rest_framework.generics.GenericAPIView
        This allows us to return only TransferCoordinator instances belonging to the user.
        If an admin is requesting, then we return all instances
        '''
        queryset = super(BatchList, self).get_queryset()
        if not self.request.user.is_staff:
            queryset = TransferCoordinator.objects.user_transfer_coordinators(self.request.user)
        return queryset


class BatchDetail(generics.RetrieveAPIView):
    '''
    Here we allow only retrieval of objects.  We have no reason to edit or destroy
    TransferCoordinators
    '''
    queryset = TransferCoordinator.objects.all()
    serializer_class = TransferCoordinatorSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        '''
        Custom behavior for object retrieval- admins can get anything
        Regular users can only get objects they own.  
        Instead of the default 403 (which exposes that a particular object
        does exist), return 404 if they are not allowed to access an object.
        '''
        obj = super(BatchDetail, self).get_object()
        obj_owners = list(set([x.resource.owner for x in Transfer.objects.filter(coordinator = obj)]))
        if len(obj_owners) == 1:            
            if (self.request.user.is_staff) or (obj_owners[0] == self.request.user):
                return obj
            else:
                raise Http404
        else:
            raise Http404


class UserBatchList(generics.ListAPIView):
    '''
    This lists the TransferCoordinator instances for a particular user
    This view is entirely protected-- only accessible by staff
    Since regular users can only see the Resources they own,
    they can just use the "vanilla" listing endpoint
    '''
    serializer_class = TransferCoordinatorSerializer
    permission_classes = (permissions.IsAdminUser,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('completed',)

    def get_queryset(self):
        user_pk = self.kwargs['user_pk']
        try:
            user = User.objects.get(pk=user_pk)
            return TransferCoordinator.objects.user_transfer_coordinators(user)
        except ObjectDoesNotExist as ex:
            raise Http404


class TransferComplete(APIView):

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):    
        data = request.data
        if 'token' in data:
            b64_enc_token = data['token']
            enc_token = base64.decodestring(b64_enc_token.encode('ascii'))
            expected_token = settings.TOKEN
            obj=DES.new(settings.ENC_KEY, DES.MODE_ECB)
            decrypted_token = obj.decrypt(enc_token)
            if decrypted_token == expected_token.encode('ascii'):

                # we can trust the content since it contained the proper token
                try:
                    transfer_pk = data['transfer_pk']
                    coordinator_pk = data['coordinator_pk']
                    success = data['success']
                except KeyError as ex:
                    raise exceptions.RequestError('The request did not have the correct formatting.')  
                try:
                    transfer_obj = Transfer.objects.get(pk=transfer_pk)
                    transfer_obj.completed = True
                    transfer_obj.success = success
                    transfer_obj.finish_time = datetime.datetime.now()
                    transfer_obj.save()

                    # now check if all the Transfers belonging to this TransferCoordinator are complete:
                    try:
                        tc = TransferCoordinator.objects.get(pk=coordinator_pk)
                    except ObjectDoesNotExist as ex:
                        raise exceptions.RequestError('TransferCoordinator with pk=%d did not exist' % coordinator_pk)
                    all_transfers = Transfer.objects.filter(coordinator = tc)
                    if all([x.completed for x in all_transfers]):
                        tc.completed = True
                        tc.finish_time = datetime.datetime.now()
                        tc.save()
                        utils.post_completion(tc)
                    return Response({'message': 'thanks'})
                except ObjectDoesNotExist as ex:
                    raise exceptions.RequestError('Transfer with pk=%d did not exist' % transfer_pk)
            else:
                raise Http404
        else:
            raise Http404


class InitDownload(generics.CreateAPIView):
    '''
    This endpoint is where we POST data for the creation of 
    download transfers (e.g. TO dropbox).
    In this case, we already have Resource objects in the database.  
    Users are transferring these known Resources out of our system
    '''

    def post(self, request, *args, **kwargs):

        # Parse the submitted data:
        data = request.data
        try:
            resource_pks = data['resource_pks']
            destination = data['destination']
        except KeyError as ex:                
            raise exceptions.RequestError('''
                Missing required information for initiating transfer.
            ''')

        try:
            resource_pks = [int(x) for x in resource_pks]

            # get Resource instances with those PKs.  Does NOT raise errors
            # if the primary keys do not exist!  Note that we have NOT yet
            # checked ownership
            resource_objs = Resource.objects.filter(pk__in=resource_pks)

            # check that they own them:
            if request.user.is_staff:
                user_resource_objs = resource_objs
            else:
                user_resource_objs = [x for x in resource_objs if x.get_owner() == request.user ]

            # if resources did not exist (i.e. pk was not valid) or they were not an owner of one or more
            if len(resource_pks) != len(user_resource_objs):
                raise exceptions.RequestError('''
                    One of more of the resources requested was not transferred.  
                    Aborting.''')

            # check that the Resource objects are active.  Ideally (if choosing from UI)
            # the user should not see expired Resource objects, but there is no such guarantee
            # that a POST request will not choose an expired Resource.
            user_resource_objs = [x for x in user_resource_objs if x.is_active]

            # We now have user-owned + active Resource objs.  Create a Transfer for each.
            # First, create a TransferCoordinator to monitor them
            tc = TransferCoordinator()
            tc.save()

            for resource in user_resource_objs:
                t = Transfer(
                     download=True,
                     resource=resource,
                     destination=destination,
                     coordinator=tc 
                )
                t.save()
 
            # actually do the transfers:
            utils.perform_transfers(tc)
            
        except ValueError as ex:
            raise ParseError

        return Response({'message': 'thanks'})


class InitUpload(generics.CreateAPIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            upload_source = data['upload_source']
            upload_info = data['upload_info']
        except KeyError as ex:
            raise exceptions.RequestError('The request JSON body did not contain the required data (%s).' % ex)

        try:
            # Here, we first do a spot-check on the data that was passed, BEFORE we invoke any asynchronous methods.
            # We prepare/massage the necessary data for the upload here, and then pass a simple dictionary to the asynchronous
            # method call.  We do this since it is easiest to pass a simple native dictionary to celery. 

            user_pk = request.user.pk

            # Depending on which upload method was requested (and which compute environment we are in), grab the proper class:
            uploader_cls = _uploaders.get_uploader(upload_source)

            # Check that the upload data has the required format to work with this uploader implementation:
            upload_info = uploader_cls.check_format(upload_info, user_pk)

            # call async method:
            tasks.upload.delay(upload_info, upload_source)

        except Exception as ex:
            return exception_handler(ex, None)

        return Response({'message': 'thanks'})



