from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns

from transfer_app import views
from transfer_app.downloaders import *

from transfer_app import live_oauth2_tests
'''
For all the endpoints given here, consult the specific view for
details about the actual methods they support, and what sorts of 
info they provide back
'''
urlpatterns = [

    # The API root gives a browsable view of the endpoints
    re_path(r'^$', views.api_root),
   
    # endpoints related to querying User info:
    re_path(r'^users/$', views.UserList.as_view(), name='user-list'),
    re_path(r'^users/(?P<pk>[0-9]+)/$', views.UserDetail.as_view(), name='user-detail'),

    # endpoints related to querying Resources:
    re_path(r'^resources/$', views.ResourceList.as_view(), name='resource-list'),
    re_path(r'^resources/(?P<pk>[0-9]+)/$', views.ResourceDetail.as_view(), name='resource-detail'),
    re_path(r'^resources/user/(?P<user_pk>[0-9]+)/$', views.UserResourceList.as_view(), name='user-resource-list'),

    # endpoints related to querying Transfers:
    re_path(r'^transfers/$', views.TransferList.as_view(), name='transfer-list'),
    re_path(r'^transfers/upload/init/$', views.InitUpload.as_view(), name='upload-transfer-initiation'),
    re_path(r'^transfers/download/init/$', views.InitDownload.as_view(), name='download-transfer-initiation'),
    re_path(r'^transfers/(?P<pk>[0-9]+)/$', views.TransferDetail.as_view(), name='transfer-detail'),
    re_path(r'^transfers/user/(?P<user_pk>[0-9]+)/$', views.UserTransferList.as_view(), name='user-transfer-list'),

    # endpoints related to querying TransferCoordinators, so we can group the Transfer instances
    re_path(r'^transfers/batch/$', views.BatchList.as_view(), name='batch-list'),
    re_path(r'^transfers/batch/(?P<pk>[0-9]+)/$', views.BatchDetail.as_view(), name='batch-detail'),
    re_path(r'^transfers/batch/user/(?P<user_pk>[0-9]+)/$', views.UserBatchList.as_view(), name='user-batch-list'),

    # endpoints for communicating from worker machines:
    re_path(r'^transfers/complete/$', views.TransferComplete.as_view(), name='transfer-complete'),

    # endpoints for callbacks:
    re_path(r'^dropbox/callback/$', DropboxDownloader.finish_authentication_and_start_download, name='dropbox_token_callback'),
    re_path(r'^oauth-dev/dropbox/$', views.test_dropbox, name='dropbox_oauth-test'),
    re_path(r'^oauth-dev/dropbox-callback/$', DropboxDownloader.finish_authentication_and_start_download, name='drive_token_callback_test'),
    re_path(r'^oauth-dev/drive/$', views.test_drive, name='drive_oauth-test'),
    re_path(r'^oauth-dev/drive-callback/$', DriveDownloader.finish_authentication_and_start_download, name='drive_token_callback_test'),
    re_path(r'^oauth-dev/test/dummy/$', live_oauth2_tests.dropbox_code_exchange_test),
    re_path(r'^oauth-dev/test/dropbox-callback/$', live_oauth2_tests.dropbox_token_exchange_test)
]

urlpatterns = format_suffix_patterns(urlpatterns)

