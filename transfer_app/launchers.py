import subprocess as sb

from django.conf import settings


class Launcher(object):
    def __init__(self):
        pass

class GoogleLauncher(Launcher):   
    def go(self, cmd):
        p = sb.Popen(cmd, shell=True, stdout=sb.PIPE, stderr=sb.STDOUT)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print('problem')
        else:
            print('ok')


class AWSLauncher(Launcher):
    pass
