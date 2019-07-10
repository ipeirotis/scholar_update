# Create a JSON file with my Google Scholar data

A small script that scrapes Google Scholar using the [Python scholarly library](https://github.com/OrganicIrradiation/scholarly)
and creates a JSON file with my publications and their statistics.

The Travis script then does the following:
* Installs Tor and PySocks, to allow scholarly to connect using Tor.
* Runs the script and fetches the latest data from Google Scholar.
* Builds a Dockerfile, that takes the two json files and puts them in a web server: [ipeirotis.json](http://scholar.ipeirotis.org/ipeirotis.json) [ipeirotis_pubs.json](http://scholar.ipeirotis.org/ipeirotis_pubs.json). The Dockerfile is stored on the (hub.docker.com registry)[https://cloud.docker.com/u/ipeirotis/repository/docker/ipeirotis/scholar_update]. The Travis script runs daily to update the JSON files. We add DOCKER_USERNAME and DOCKER_PASSWORD as environmental variables setup on Travis. The web server is running as an f1-micro (free) running on Google Cloud.
* The Travis script also copies the two JSON files on a Google Bucket, [ipeirotis.json](https://storage.googleapis.com/publications_scholar/ipeirotis.json) [ipeirotis_pubs.json](hthttps://storage.googleapis.com/publications_scholar/ipeirotis_pubs.json). To enable the upload:

  * We follow the instructions at https://cloud.google.com/storage/docs/reference/libraries to fetch the client-secrets.json file
  * We encrypt the client-secrets.json file as described in https://docs.travis-ci.com/user/encrypting-files/
  * We use the script `upload_to_google_storage.py` (adapted from https://cloud.google.com/storage/docs/uploading-objects) to upload the generated files and make them public. The service account needs to be a "Storage Object Admin" (and not "Project Owner" as outlined in the documentation), and the bucket needs to have object level permissions, and not "bucket policy only"


TODO: 
* As part of the deployment, we should reboot the Google Cloud machine that runs the docker image, to get the latest version of the docker image
