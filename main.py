import functions_framework
import json
import logging
from datetime import datetime
from google.cloud import storage
from scholarly import scholarly

@functions_framework.http
def update_scholar_profile(request):
    """HTTP Cloud Function.
    Args:
       request (flask.Request): The request object.
    Returns:
       The response text, or any set of values that can be turned into a
       Response object using `make_response`.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    author_name = request_json.get("author_name", request_args.get("author_name"))
    filename = request_json.get("filename", request_args.get("filename"))
    if not author_name or not filename:
        return "Missing author name or filename", 400

    author, publications = get_scholar_data(author_name)
    if author is None or publications is None:
        return "Error getting data from Google Scholar", 500

    result = store_data_on_bucket(filename, author, publications)
    if result is None:
        return "Error storing data on Google Bucket", 500

    return f"Updated entry for author {author_name} with filename {filename}", 200

def get_scholar_data(author_name):
    try:
        search_query = scholarly.search_author(author_name)
        author = scholarly.fill(next(search_query))
    except Exception:
        logging.exception("Error getting data from Google Scholar")
        return None, None

    now = datetime.now()
    timestamp = int(datetime.timestamp(now))
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    publications = []
    for pub in author["publications"]:
        pub["citedby"] = pub.pop("num_citations")
        pub["last_updated_ts"] = timestamp
        pub["last_updated"] = date_str
        publications.append(pub)

    author["last_updated_ts"] = timestamp
    author["last_updated"] = date_str
    del author["publications"]

    return author, publications

def store_data_on_bucket(filename, author, publications):
    try:
        client = storage.Client()
        bucket_name = "publications_scholar"
        bucket = client.bucket(bucket_name)

        author_filename = f"{filename}.json"
        blob = bucket.blob(str(author_filename))
        blob.upload_from_string(json.dumps(author), content_type="application/json")

        publications_filename = f"{filename}_pubs.json"
        blob = bucket.blob(str(publications_filename))
        blob.upload_from_string(json.dumps(publications), content_type="application/json")
    except Exception:
        logging.exception("Error storing data on Google Bucket")
        return None

    return True
