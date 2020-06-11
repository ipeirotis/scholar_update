import os
import pprint

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials-scholarAPI.json"
credentials = GoogleCredentials.get_application_default()
service = discovery.build("compute", "v1", credentials=credentials)

# Project ID for this request.
project = "scholarapi"
# The name of the zone for this request.
zone = "us-east1-b"
# Name of the instance resource to start.
instance = "web"

# Reset the instance
request = service.instances().reset(project=project, zone=zone, instance=instance)
response = request.execute()
pprint.pprint(response)
