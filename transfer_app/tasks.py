from celery.decorators import task

from transfer_app import uploaders 

@task(name='upload')
def upload(upload_info, upload_source):
    '''
    upload_info is a list, with each entry a dictionary.
    Each of those dictionaries has keys which are specific to the upload source
    '''
    uploader_cls = uploaders.get_uploader(upload_source)
    uploader = uploader_cls(upload_info)
    uploader.upload()
