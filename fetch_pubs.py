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

# Set up scholarly to use the Tor proxy
# proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
# scholarly.use_proxy(**proxies)

# Query for author and fill in the details
try:
    search_query = scholarly.search_author(author_name)
    author = next(search_query).fill()
except Exception as e:
    quit()

# Convert Author object to a dictionary, to allow JSON serialization
author_dict = dict(author.__dict__)
# Add last-updated information in the dictionary
author_dict['last_updated_ts'] = timestamp
author_dict['last_updated'] = date_str
# Remove the publications and co-author entries, which are not needed in the JSON
del author_dict['publications']
del author_dict['coauthors']
del author_dict['nav']

# Save the author profile in a JSON file
with open(author_name + ".json", "w") as f:
    json.dump(author_dict, f)

# Go through the publicationw now, and fill them in with their details
# tqdm just to know where we are and how long it will take (often 15-20 mins for ~100 pubs)
for pub in tqdm.tqdm(author.publications):
    try:
        if not pub._filled:
            pub.fill()
    except Exception as e:
        pass

# Once we have the fully complete publications, we convert them to dictionaries to
# be able to serialize them in JSON
publications = []
for pub in author.publications:
    publications.append(dict(pub.__dict__))

# Bookkeeping with publications, ensuring that everything is serializable
for p in publications:
    # The "abstract" is often a BS4.Tag, so we need to convert to string
    if 'abstract' in p['bib']:
        p['bib']['abstract'] = str(p['bib']['abstract'])

    # Add entries for cites_per_year and citedby, if they are not in the response
    if 'cites_per_year' in p:
        p['cites_per_year'] = json.loads(json.dumps(dict(p['cites_per_year'])))
    else:
        p['cites_per_year'] = dict()
    p['citedby'] = p['citedby'] if 'citedby' in p else 0
    p['last_updated_ts'] = timestamp
    p['last_updated'] = date_str

# Save the publications in a JSON file
with open(author_name + "_pubs.json", "w") as f:
    json.dump(publications, f)
