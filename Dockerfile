FROM ubuntu


MAINTAINER Panos Ipeirotis

# Update the repository sources list
RUN apt-get update

# Install and run apache
RUN apt-get install -y apache2 && apt-get clean

COPY ipeirotis.json /var/www/html/ipeirotis.json
COPY ipeirotis_pubs.json /var/www/html/ipeirotis_pubs.json

EXPOSE 80
CMD ["apachectl", "-D", "FOREGROUND"]
