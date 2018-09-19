import unittest.mock as mock

from django.test import TestCase
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import transfer_app.downloaders as downloaders

@login_required
def live_test(request):
    return render(request, 'transfer_app/live_oauth2_test.html', {})

@login_required
def dropbox_code_exchange_test(request):
    test = LiveTest()
    return test.dropbox_code_exchange_test(request)

def dropbox_token_exchange_test(request):
    test = LiveTest()
    return test.dropbox_token_exchange_test(request)

@login_required
def drive_code_exchange_test(request):
    test = LiveTest()
    return test.drive_code_exchange_test(request)

def drive_token_exchange_test(request):
    test = LiveTest()
    return test.drive_token_exchange_test(request)

class LiveTest(TestCase):

    def dropbox_code_exchange_test(self, request):
        downloader_cls = downloaders.get_downloader(settings.DROPBOX)
        request.session['download_info'] = []
        request.session['download_destination'] = settings.DROPBOX
        with mock.patch.dict(downloaders.settings.CONFIG_PARAMS, {'dropbox_callback':settings.LIVE_TEST_CONFIG_PARAMS['dropbox_callback']}):
            return downloader_cls.authenticate(request)

    @mock.patch('transfer_app.downloaders.transfer_tasks')
    def dropbox_token_exchange_test(self, request, mock_tasks):
        downloader_cls = downloaders.get_downloader(settings.DROPBOX)
        with mock.patch.dict(downloaders.settings.CONFIG_PARAMS, {'dropbox_callback':settings.LIVE_TEST_CONFIG_PARAMS['dropbox_callback']}):
            response = downloader_cls.finish_authentication_and_start_download(request)
            self.assertEqual(response.status_code, 200)
            return response

    def drive_code_exchange_test(self, request):
        downloader_cls = downloaders.get_downloader(settings.GOOGLE_DRIVE)
        request.session['download_info'] = []
        request.session['download_destination'] = settings.DROPBOX
        with mock.patch.dict(downloaders.settings.CONFIG_PARAMS, {'drive_callback':settings.LIVE_TEST_CONFIG_PARAMS['drive_callback']}):
            return downloader_cls.authenticate(request)

    @mock.patch('transfer_app.downloaders.transfer_tasks')
    def drive_token_exchange_test(self, request, mock_tasks):
        downloader_cls = downloaders.get_downloader(settings.GOOGLE_DRIVE)
        with mock.patch.dict(downloaders.settings.CONFIG_PARAMS, {'drive_callback':settings.LIVE_TEST_CONFIG_PARAMS['drive_callback']}):
            response = downloader_cls.finish_authentication_and_start_download(request)
            self.assertEqual(response.status_code, 200)
            return response
