from django.conf import settings

import googleapiclient.discovery as discovery

class Launcher(object):
    def __init__(self):
        self.setup()


class GoogleLauncher(Launcher):

    def setup(self):
        pass
        #self.compute_client = discovery.build('compute', 'v1')
   
    def go(self, config):
        pass
    
        """
        self.compute_client.instances().insert(
            project=settings.CONFIG_PARAMS['google_project_id'],
            zone=settings.CONFIG_PARAMS['google_zone'],
            body=config
        ).execute()
        """


class AWSLauncher(Launcher):
    pass
