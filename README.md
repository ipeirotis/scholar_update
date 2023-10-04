[![GitHub: Build Status](https://github.com/ipeirotis/scholar_update/workflows/Python%20application/badge.svg)](https://github.com/ipeirotis/scholar_update/actions?query=workflow%3A%22Python+application%22+branch%3Amaster)    

# How to create a JSON file with your Google Scholar data

With a small Python script that uses the [scholarly library](https://github.com/OrganicIrradiation/scholarly), you can easily scrape your Google Scholar profile and generate a JSON file containing information about your publications and their statistics. Once you have this file, you can store it in a publicly accessible Google Bucket, which will allow others to view your data.

To set this up, follow these steps:

* Create a new Google Bucket and set it to be publicly readable.
* Create a Google Function that runs the `main.py` script to scrape your Google Scholar profile and generate the JSON file.
* Schedule the function to run automatically each day using a Cloud Scheduler task.

The instructions in the [Github actions file](https://github.com/ipeirotis/scholar_update/blob/master/.github/workflows/pythonapp.yml) show how to authenticate your script and how to schedule the function using the Cloud Scheduler (aka cron).

Once you have completed these steps, you should be able to access your Google Scholar data in JSON format from the publicly accessible Google Bucket. 

My two files are [ipeirotis.json](https://storage.googleapis.com/publications_scholar/ipeirotis.json) and [ipeirotis_pubs.json](https://storage.googleapis.com/publications_scholar/ipeirotis_pubs.json).
