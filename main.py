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
    request_json = request.get_json(silent=True) or {}
    request_args = request.args

    scholar_id = request_json.get("scholar_id", request_args.get("scholar_id"))
    author_name = request_json.get("author_name", request_args.get("author_name"))
    filename = request_json.get("filename", request_args.get("filename"))
    if not (scholar_id or author_name) or not filename:
        return "Missing scholar_id/author_name or filename", 400

    author, publications = get_scholar_data(author_name, scholar_id)
    if author is None or publications is None:
        return "Error getting data from Google Scholar", 500

    result = store_data_on_bucket(filename, author, publications)
    if result is None:
        return "Error storing data on Google Bucket", 500

    return f"Updated entry for author {scholar_id or author_name} with filename {filename}", 200

def get_scholar_data(author_name, scholar_id=None):
    try:
        # Look up the profile by ID when we have one. Google Scholar's author
        # search now redirects to a sign-in page, so search by name fails.
        if scholar_id:
            author = scholarly.search_author_id(scholar_id)
        else:
            author = next(scholarly.search_author(author_name))
        author = scholarly.fill(author)
    except Exception:
        logging.exception("Error getting data from Google Scholar")
        return None, None

    # We want to keep track of the last time we updated the file
    now = datetime.now()
    timestamp = int(datetime.timestamp(now))
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

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

    return author, publications

def store_data_on_bucket(filename, author, publications):
    try:
        client = storage.Client()
        bucket_name = "publications_scholar"
        bucket = client.bucket(bucket_name)

        # Save the author profile in a JSON file
        author_filename = f"{filename}.json"
        blob = bucket.blob(str(author_filename))
        blob.upload_from_string(json.dumps(author), content_type="application/json")
        
        # Save the publications in a JSON file
        publications_filename = f"{filename}_pubs.json"
        blob = bucket.blob(str(publications_filename))
        blob.upload_from_string(json.dumps(publications), content_type="application/json")
    except Exception:
        logging.exception("Error storing data on Google Bucket")
        return None

    return True
