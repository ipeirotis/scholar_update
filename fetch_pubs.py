import scholarly
import json
import tqdm

# Set up scholarly to use the Tor proxy
proxies = {'http' : 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
scholarly.scholarly.use_proxy(**proxies)

search_query = scholarly.search_author('Ipeirotis')
author = next(search_query).fill()

author_dict = dict(author.__dict__)

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
    p['cites_per_year'] = json.loads(json.dumps(dict(p['cites_per_year'])))
    p['citedby'] = p['citedby'] if 'citedby' in p else 0
    
    
with open("ipeirotis_pubs.json", "w") as f:
    json.dump(publications, f)
