import os
from google.cloud import storage
from os import listdir
from os.path import isfile, join, isdir


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    blob.make_public()

    print('File {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))

path = 'data'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'client-secret-ipeirotis-gc.json'
storage_client = storage.Client()

datafiles = sorted([f for f in listdir(path) if isfile(join(path, f))])
for d in datafiles:
    upload_blob('datasets_nyu', join(path, d), d)
