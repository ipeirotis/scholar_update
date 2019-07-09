# Create a JSON file with my Google Scholar data

A small script that scrapes Google Scholar using the [Python scholarly library](https://github.com/OrganicIrradiation/scholarly)
and creates a JSON file with my publications.

The Dockerfile takes the two json files and puts them in a web server, to be accessible online at
http://scholar.ipeirotis.org/ipeirotis.json
and
http://scholar.ipeirotis.org/ipeirotis_pubs.json

The Dockerfile is stored on the hub.docker.com registry, under ipeirotis/scholar_update. The Travis script runs daily to update the JSON files. We add DOCKER_USERNAME and DOCKER_PASSWORD as environmental variables setup on Travis.

TODO: 
* Publish on a Google Storage Bucket instead
* Reboot the Google Cloud machine that runs the docker image
