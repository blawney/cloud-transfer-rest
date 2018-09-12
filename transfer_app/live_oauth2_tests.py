import unittest.mock as mock

from django.test import TestCase
from django.conf import settings

import transfer_app.downloaders as downloaders

def dropbox_code_exchange_test(request):
    test = DropboxLiveTest()
    return test.dropbox_code_exchange_test(request)

def dropbox_token_exchange_test(request):
    test = DropboxLiveTest()
    return test.dropbox_token_exchange_test(request)

class DropboxLiveTest(TestCase):

    def dropbox_code_exchange_test(self, request):
        downloader_cls = downloaders.get_downloader(settings.DROPBOX)
        request.session['download_info'] = []
        request.session['download_destination'] = settings.DROPBOX
        print(settings.LIVE_TEST_CONFIG_PARAMS)
        with mock.patch.dict(downloaders.settings.CONFIG_PARAMS, {'dropbox_callback':settings.LIVE_TEST_CONFIG_PARAMS['dropbox_callback']}):
            return downloader_cls.authenticate(request)

    @mock.patch('transfer_app.downloaders.transfer_tasks')
    def dropbox_token_exchange_test(self, request, mock_tasks):
        downloader_cls = downloaders.get_downloader(settings.DROPBOX)
        with mock.patch.dict(downloaders.settings.CONFIG_PARAMS, {'dropbox_callback':settings.LIVE_TEST_CONFIG_PARAMS['dropbox_callback']}):
            response = downloader_cls.finish_authentication_and_start_download(request)
            print(response)
            self.assertEqual(response.status_code, 200)
            return response
