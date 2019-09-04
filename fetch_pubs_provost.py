import scholarly
import json
import tqdm
from datetime import datetime

# We want to keep track of the last time we updated the file
now = datetime.now()
timestamp = int(datetime.timestamp(now))
date_str = now.strftime("%Y-%m-%d %H:%M:%S")

# hack for travis: Only  execute on even days
if now.day%2!=0:
    quit()

# Set up scholarly to use the Tor proxy
proxies = {'http' : 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
scholarly.scholarly.use_proxy(**proxies)

# Query for Ipeirotis and fill in the details
search_query = scholarly.search_author('Foster Provost')
author = next(search_query).fill()

# Convert Author object to a dictionary, to allow JSON serialization
author_dict = dict(author.__dict__)
# Add last-updated information in the dictionary
author_dict['last_updated_ts'] = timestamp
author_dict['last_updated'] = date_str
# Remove the publications and co-author entries, which are not needed in the JSON
del author_dict['publications']
del author_dict['coauthors']

# Save the author profile in a JSON file
with open("provost.json", "w") as f:
     json.dump(author_dict, f)
        
# Go through the publicationw now, and fill them in with their details
# tqdm just to know where we are and how long it will take (often 15-20 mins for ~100 pubs)
for pub in tqdm.tqdm(author.publications):
    if not pub._filled:
        pub.fill()
        
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
with open("provost_pubs.json", "w") as f:
    json.dump(publications, f)
