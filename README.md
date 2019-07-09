# Create a JSON file with my Google Scholar data

A small script that scrapes Google Scholar using the [Python scholarly library](https://github.com/OrganicIrradiation/scholarly)
and creates a JSON file with my publications.

The Dockerfile takes the two json files and puts them in a web server, to be accessible online. The Dockerfile is stored on the hub.docker.com registry, under ipeirotis/scholar_update.

We also have a CI/CD Travis script built, that runs weekly to update the JSON files. We add DOCKER_USERNAME (ipeirotis) and DOCKER_PASSWORD as environmental variables, and the we used the docker_push script to push the image 
