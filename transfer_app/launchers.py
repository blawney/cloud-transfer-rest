import datetime

class Launcher(object):
    def __init__(self, config):
        '''
        config is a dictionary with all the necessary parameters necessary
        for launching a worker.
        '''
        self.config = config


class GoogleLauncher(Launcher):
    pass

class AWSLauncher(Launcher):
    pass
