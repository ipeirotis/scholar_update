[![GitHub: Build Status](https://github.com/ipeirotis/scholar_update/workflows/Python%20application/badge.svg)](https://github.com/ipeirotis/scholar_update/actions?query=workflow%3A%22Python+application%22+branch%3Amaster)

# Create a JSON file with my Google Scholar data

A small script that scrapes Google Scholar using the [Python scholarly library](https://github.com/OrganicIrradiation/scholarly)
and creates a JSON file with my publications and their statistics.

The GitHub Action script then does the following:
* Installs Tor and PySocks, to allow scholarly to connect using Tor.
* Runs the script and fetches the latest data from Google Scholar.
* The script runs daily to update the JSON files.  
* The then copies the two JSON files on a Google Bucket, [ipeirotis.json](https://storage.googleapis.com/publications_scholar/ipeirotis.json) and [ipeirotis_pubs.json](https://storage.googleapis.com/publications_scholar/ipeirotis_pubs.json). To enable the upload:

  * We follow the [Google instructions](https://cloud.google.com/storage/docs/reference/libraries) to fetch the secrets json file
  * We encrypt the secrets json file using the [Travis instructions](https://docs.travis-ci.com/user/encrypting-files/)
  * We use the script `upload_to_google_storage.py`, adapted from [Google](https://cloud.google.com/storage/docs/uploading-objects), to upload the generated files and make them public. 
  * The service account needs to be a "Storage Object Admin" (and not "Project Owner" as outlined in the documentation), and the bucket needs to have object level permissions, and not "bucket policy only". The bucket needs to be public.


