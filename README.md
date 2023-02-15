[![GitHub: Build Status](https://github.com/ipeirotis/scholar_update/workflows/Python%20application/badge.svg)](https://github.com/ipeirotis/scholar_update/actions?query=workflow%3A%22Python+application%22+branch%3Amaster)    

# Create a JSON file with my Google Scholar data

A small script that scrapes Google Scholar using the [Python scholarly library](https://github.com/OrganicIrradiation/scholarly), creates a JSON file with my publications and their statistics, and then posts the resulting JSON files on a publicly accessible Google Bucket ([ipeirotis.json](https://storage.googleapis.com/publications_scholar/ipeirotis.json) and [ipeirotis_pubs.json](https://storage.googleapis.com/publications_scholar/ipeirotis_pubs.json)).

Structure:
* Create a Google Bucket, publicly readable
* Create a Google Function with the `main.py` script.
* Create a Cloud Scheduler tasks (aka cron) that triggers the function every day.

The Github actions file contains the instructions for deployment.
