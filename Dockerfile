FROM ubuntu:18.04


MAINTAINER Panos Ipeirotis

# Update the repository sources list
RUN apt-get update

# Install and run apache
RUN apt-get install -y apache2 && apt-get clean

COPY ipeirotis.json /var/www/html/
COPY ipeirotis.json /var/www/html/
COPY provost.json /var/www/html/
COPY provost_pubs.json /var/www/html/

EXPOSE 80
CMD ["apachectl", "-D", "FOREGROUND"]
