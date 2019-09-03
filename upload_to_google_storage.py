import os
from google.cloud import storage

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

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials-scholarAPI.json'
storage_client = storage.Client()

upload_blob('publications_scholar', 'ipeirotis.json', 'ipeirotis.json')
upload_blob('publications_scholar', 'provost.json', 'provost.json')
upload_blob('publications_scholar', 'ipeirotis_pubs.json', 'ipeirotis_pubs.json')
upload_blob('publications_scholar', 'provost_pubs.json', 'provost_pubs.json')
