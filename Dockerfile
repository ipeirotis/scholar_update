FROM ubuntu


MAINTAINER Panos Ipeirotis

# Update the repository sources list
RUN apt-get update

# Install and run apache
RUN apt-get install -y apache2 
RUN apt-get install -y python3-pip
RUN apt-get install -y tor 
RUN apt-get clean

RUN pip3 install -U git+https://github.com/OrganicIrradiation/scholarly.git
RUN pip3 install -U tqdm 
RUN pip3 install -U PySocks

RUN ln -s ipeirotis.json /var/www/html/ipeirotis.json

RUN  ln -s ipeirotis_pubs.json /var/www/html/ipeirotis_pubs.json

EXPOSE 80
CMD ["apachectl", "-D", "FOREGROUND"]
