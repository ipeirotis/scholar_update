import functions_framework

import json
import logging
from datetime import datetime

from google.cloud import storage
from scholarly import scholarly

@functions_framework.http
def api_call(request):
    """HTTP Cloud Function.
    Args:
       request (flask.Request): The request object.
       <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
       The response text, or any set of values that can be turned into a
       Response object using `make_response`
       <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and "author_name" in request_json:
        author_name = request_json["author_name"]
    elif request_args and "author_name" in request_args:
        author_name = request_args["author_name"]
    else:
        return "Missing author name"

    msg = scholar_update(author_name)

    return msg
    

def scholar_update(author_name):
    # We want to keep track of the last time we updated the file
    now = datetime.now()
    timestamp = int(datetime.timestamp(now))
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Query for author and fill in the details
    try:
        search_query = scholarly.search_author(author_name)
        author = scholarly.fill(next(search_query))
    except Exception:
        logging.exception("Something went wrong when searching Google Scholar")
        return "Something went wrong when searching Google Scholar"

    # Bookkeeping with publications
    publications = []
    for pub in author["publications"]:
        pub["citedby"] = pub.pop("num_citations")
        pub["last_updated_ts"] = timestamp
        pub["last_updated"] = date_str
        publications.append(pub)

    # Add last-updated information in the dictionary
    author["last_updated_ts"] = timestamp
    author["last_updated"] = date_str
    # Remove the publications entries, which are not needed in the JSON
    del author["publications"]

    try:
        # Setup access to the Google Cloud Storage bucket
        client = storage.Client()
        bucket_name = "publications_scholar"
        bucket = client.bucket(bucket_name)

        # Save the author profile in a JSON file
        filename = f"{author_name}.json"
        blob = bucket.blob(str(filename))
        blob.upload_from_string(json.dumps(author), content_type="application/json")

        # Save the publications in a JSON file
        filename = f"{author_name}_pubs.json"
        blob = bucket.blob(str(filename))
        blob.upload_from_string(json.dumps(publications), content_type="application/json")
    except Exception:
        logging.exception("Something went wrong when writing to the bucket")
        return "Something went wrong when writing to the bucket"

    return f"Updated entry for author {author_name}"
