import sys
from scholarly import scholarly
import json
import tqdm
from datetime import datetime

if len(sys.argv) == 2:
    author_name = sys.argv[1]
else:
    quit()

# We want to keep track of the last time we updated the file
now = datetime.now()
timestamp = int(datetime.timestamp(now))
date_str = now.strftime("%Y-%m-%d %H:%M:%S")

# Query for author and fill in the details
try:
    search_query = scholarly.search_author(author_name)
    author = scholarly.fill(next(search_query))
except Exception as e:
    quit()
    
    
# Bookkeeping with publications
publications = []
for pub in author["publications"]:
    # del pub["source"]
    # del pub["filled"]
    # del pub["container_type"]
    pub["citedby"] = pub.pop("num_citations")
    pub["last_updated_ts"] = timestamp
    pub["last_updated"] = date_str    
    publications.append(pub)
    
# Add last-updated information in the dictionary
author["last_updated_ts"] = timestamp
author["last_updated"] = date_str
# Remove the publications entries, which are not needed in the JSON
del author["publications"]
# del author["coauthors"]
# del author["filled"]
# del author["container_type"]
# del author["source"]

    

# Save the author profile in a JSON file
with open(author_name + ".json", "w") as f:
    json.dump(author, f, indent=4)

# Save the publications in a JSON file
with open(author_name + "_pubs.json", "w") as f:
    json.dump(publications, f, indent=4)

