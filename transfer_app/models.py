from django.db import models

from django.contrib.auth.models import User


class ResourceManager(models.Manager):
     '''
     This class provides a nice way to filter Resource objects for a particular user
     '''
     def user_resources(self, user):
         return super(ResourceManager, self).get_queryset().filter(owner=user)


class Resource(models.Model):
    '''
    This model respresents a general resource/file.  See individual fields for interpretation
    '''
    # the location (e.g. URL) where the Resource is 
    source = models.CharField(max_length=100, null=False)

    # the location (e.g. URL) where the Resource lives, relative to source 
    path = models.CharField(max_length=1000, null=False)
    
    # the file size in bytes.  For display, this will be converted
    # to human-readable form  
    size = models.BigIntegerField(default=0)

    # each Resource can only be associated with a single User instance
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # this boolean controls whether a Resource is active and able to be transferred
    is_active = models.BooleanField(null=False, default=True)

    # The date the resource was added:
    # auto_now_add sets the timestamp when an instance of created
    date_added = models.DateTimeField(null=False, auto_now_add=True)

    # when does this Resource expire?  When we expire a Resource, it will
    # be set to inactive.  Can be null, which would allow it to be permanent
    expiration_date = models.DateTimeField(null=True)

    objects = ResourceManager()
    
    def __str__(self):
        return '%s' % self.source

    def get_owner(self):
        return self.owner


class TransferCoordinatorObjectManager(models.Manager):
     '''
     This class provides a way to filter TransferCoordinator objects for a particular user
     Could perhaps be optimized.
     '''
     def user_transfer_coordinators(self, user):
         all_tc = super(TransferCoordinatorObjectManager, self).get_queryset()
         all_user_transfers = Transfer.objects.user_transfers(user)
         user_tc_pk = list(set([t.coordinator.pk for t in all_user_transfers]))
         q = all_tc.filter(pk__in = user_tc_pk)
         return q



class TransferCoordinator(models.Model):
    '''
    This model serves as a way to track a "batch" of Transfer instances (which can be of size >= 1), which allows
    for messaging once actions are completed.  Note that the Transfer model references this class, which 
    gives us the link between the two entities.
    '''

    # Having the owner field allows us to know who started batch transfers.
    # Could also get this by diving down to the actual Resources, but ease of
    # access trumps other concerns here.
    #owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # If all the Transfers have completed
    completed = models.BooleanField(null=False, default=False)

    # When the batch of Transfers was started- auto_now_add sets this when we create
    # the object
    start_time = models.DateTimeField(null=False, auto_now_add=True)

    # when all the Transfers completed. This does NOT imply success.
    finish_time = models.DateTimeField(null=True)

    objects = TransferCoordinatorObjectManager()


class TransferObjectManager(models.Manager):
     '''
     This class provides a nice way to filter Transfer objects for a particular user
     '''
     def user_transfers(self, user):
         return super(TransferObjectManager, self).get_queryset().filter(resource__owner=user)

     #def get_coordinator(self, tc):
     #    return super(TransferObjectManager, self).get_queryset().filter(coordinator__pk=tc.pk)


class Transfer(models.Model):
    '''
    This class gives info about the transfer of a Resource from one location to another
    '''

    # True if transferring AWAY from our system (e.g. out of our bucket into a Dropbox)
    # False is an upload, which means someone is placing a file in our filesystem
    # No default value, and require a value with null=False
    download = models.BooleanField(null=False)

    # the Resource instance we are moving, as a foreign key
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)

    # where the Resource is going (e.g. a URL)
    destination = models.CharField(null=False, max_length=1000)

    # has the Transfer completed?  This does NOT indicate success.  
    # A Transfer can be marked complete if it has tried and we have 
    # stopped trying to transfer it
    completed = models.BooleanField(null=False, default=False)

    # This marks whether the transfer was successful
    success = models.BooleanField(null=False, default=False)

    # When the transfer was started- auto_now_add sets this when we create
    # the Transfer
    start_time = models.DateTimeField(null=False, auto_now_add=True)

    # when the Transfer completed.  As above, a complete transfer
    # does NOT imply success.
    finish_time = models.DateTimeField(null=True)

    # each Transfer is "managed" by a TransferCoordinator, which monitors >=1 Transfers
    coordinator = models.ForeignKey(TransferCoordinator, on_delete=models.CASCADE)

    objects = TransferObjectManager()

    def __str__(self):
        return 'Transfer of %s, %s' % (self.resource, 'download' if self.download else 'upload')

    def get_owner(self):
        return self.resource.owner
