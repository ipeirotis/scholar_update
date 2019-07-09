import scholarly
import json
import tqdm
from datetime import datetime

now = datetime.now()
timestamp = int(datetime.timestamp(now))
date_str = now.strftime("%Y-%m-%d %H:%M:%S")

# Set up scholarly to use the Tor proxy
proxies = {'http' : 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
scholarly.scholarly.use_proxy(**proxies)

search_query = scholarly.search_author('Ipeirotis')
author = next(search_query).fill()

author_dict = dict(author.__dict__)

author_dict['last_updated_ts'] = timestamp
author_dict['last_updated'] = date_str

del author_dict['publications']
del author_dict['coauthors']

with open("ipeirotis.json", "w") as f:
     json.dump(author_dict, f)
        
for pub in tqdm.tqdm(author.publications):
    if not pub._filled:
        pub.fill()
        
publications = []
for pub in author.publications:
    publications.append(dict(pub.__dict__))

for p in publications:
    if 'abstract' in p['bib']:
        p['bib']['abstract'] = str(p['bib']['abstract'])
        
    if 'cites_per_year' in p:
        p['cites_per_year'] = json.loads(json.dumps(dict(p['cites_per_year'])))
    else:
        p['cites_per_year'] = dict()
    p['citedby'] = p['citedby'] if 'citedby' in p else 0
    p['last_updated_ts'] = timestamp
    p['last_updated'] = date_str

    
    
with open("ipeirotis_pubs.json", "w") as f:
    json.dump(publications, f)
