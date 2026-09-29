import functions_framework
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from google.cloud import storage
from scholarly import scholarly

# Output names become object names in the public bucket, so keep them simple
FILENAME_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")

BUCKET_NAME = "publications_scholar"

# Single failed runs are routine (Google Scholar blocks some Cloud Run IPs), so
# alerting keys off this: a failed run whose output is older than STALE_AFTER
# logs STALE_MARKER, and the "stale output" alert policy matches on it.
STALE_AFTER = timedelta(days=7)
STALE_MARKER = "SCHOLAR_UPDATE_STALE"

# scholarly reports why a fetch failed (status code, captcha, 403) only at
# INFO, and httpx logs each request's status at INFO. Keep both so a
# MaxTriesExceededException in the logs comes with Google Scholar's response.
logging.basicConfig(level=logging.WARNING)
logging.getLogger("scholarly").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)


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
    filename = request_json.get("filename", request_args.get("filename"))
    if not scholar_id or not filename:
        return "Missing scholar_id or filename", 400
    if not isinstance(filename, str) or not FILENAME_RE.fullmatch(filename):
        return "Invalid filename: use 1-64 letters, digits, '-' or '_'", 400

    author, publications = get_scholar_data(scholar_id)
    if author is None or publications is None:
        log_if_stale(filename)
        return "Error getting data from Google Scholar", 500

    result = store_data_on_bucket(filename, author, publications)
    if result is None:
        log_if_stale(filename)
        return "Error storing data on Google Bucket", 500

    return f"Updated entry for author {scholar_id} with filename {filename}", 200


def get_scholar_data(scholar_id):
    try:
        # Look up the profile by ID only: Google Scholar's author search
        # redirects to a sign-in page, so searching by name fails.
        author = scholarly.search_author_id(scholar_id)
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
        bucket = client.bucket(BUCKET_NAME)

        # Write the publications first: <filename>.json is written only when
        # both uploads succeed, so its timestamp (which log_if_stale checks)
        # never claims an update whose publications list failed to upload.
        blob = bucket.blob(f"{filename}_pubs.json")
        blob.upload_from_string(json.dumps(publications), content_type="application/json")

        blob = bucket.blob(f"{filename}.json")
        blob.upload_from_string(json.dumps(author), content_type="application/json")
    except Exception:
        logging.exception("Error storing data on Google Bucket")
        return None

    return True


def log_if_stale(filename):
    """After a failed run, log STALE_MARKER if <filename>.json is older than STALE_AFTER (or missing)."""
    try:
        blob = storage.Client().bucket(BUCKET_NAME).get_blob(f"{filename}.json")
    except Exception:
        logging.exception("Could not check the age of %s.json", filename)
        return
    if blob is None:
        logging.error("%s: %s.json does not exist in gs://%s", STALE_MARKER, filename, BUCKET_NAME)
        return
    age = datetime.now(timezone.utc) - blob.updated
    if age > STALE_AFTER:
        logging.error("%s: %s.json was last updated %s (%d days ago)",
                      STALE_MARKER, filename, blob.updated.isoformat(), age.days)
