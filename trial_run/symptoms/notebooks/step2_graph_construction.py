# Step 2 & 3: Ingestion & Graph Construction
# Reads the articles discovered in Step 1, fetches their outgoing Wikipedia links,
# and builds a directed graph of the COVID-19 Symptoms domain.

import requests
import networkx as nx
import pandas as pd
import json
import time
import os
from pathlib import Path

# Setup directories
DATA_DIR = Path('../data')
GRAPHS_DIR = Path('../graphs')
os.makedirs(GRAPHS_DIR, exist_ok=True)

# Wikimedia API requires a User-Agent header
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'DSP-Project-COVID19/1.0 (pratiksahoo3551@gmail.com) Python/requests'
})

def get_outlinks_bulk(page_titles, max_retries=3):
    """
    Fetch all outgoing links for a list of Wikipedia articles.
    Uses Wikipedia's bulk query feature (max 50 titles per request) for speed.
    """
    url = 'https://en.wikipedia.org/w/api.php'
    titles_str = '|'.join(page_titles)
    
    links_dict = {title: [] for title in page_titles}
    plcontinue = None

    while True:
        params = {
            'action':      'query',
            'titles':      titles_str,
            'prop':        'links',
            'pllimit':     'max',
            'plnamespace': 0,      # Only link to main namespace articles
            'format':      'json'
        }
        if plcontinue:
            params['plcontinue'] = plcontinue

        for attempt in range(max_retries):
            try:
                r = SESSION.get(url, params=params, timeout=15).json()
                break
            except Exception as e:
                print(f'    Retry {attempt+1}/{max_retries} due to {e}')
                time.sleep(2)
        else:
            print(f'    Failed to fetch batch after {max_retries} retries.')
            return links_dict

        # Parse responses
        pages = r.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            title = page_data.get('title')
            if not title: continue
            
            # Map normalized titles back to original if Wikipedia changed them
            # (e.g. "covid-19" -> "COVID-19")
            
            for link in page_data.get('links', []):
                links_dict[title].append(link['title'])

        if 'continue' in r:
            plcontinue = r['continue']['plcontinue']
        else:
            break

    return links_dict


print("=" * 60)
print("  Step 2: Link Ingestion & Graph Construction")
print("=" * 60)

# 1. Load the articles discovered in Step 1
input_path = DATA_DIR / 'discovered_articles.csv'
if not input_path.exists():
    raise FileNotFoundError(f"Missing {input_path}. Run step1_article_discovery.py first.")

df_articles = pd.read_csv(input_path)
article_list = df_articles['article'].tolist()
print(f"Loaded {len(article_list)} articles from {input_path.name}")

# To make the trial run feasible locally in reasonable time, we'll build the 
# graph from the 200 most relevant articles (seeds + category members), 
# rather than querying 4,000 articles which would take 2+ hours on the API.
# (You can expand this later if you want the full graph!)

target_articles = df_articles[
    df_articles['source'].isin(['seed', 'category', 'backlink'])
]['article'].tolist()

# Ensure it's not too massive for a trial (cap at ~500)
if len(target_articles) > 500:
    target_articles = target_articles[:500]

print(f"\n[1/3] Fetching outlinks for {len(target_articles)} core articles...")
print("      (Using Wikipedia API bulk queries of 50 articles at a time)")

# 2. Fetch links in batches of 50
BATCH_SIZE = 50
all_links = {}

start_time = time.time()
for i in range(0, len(target_articles), BATCH_SIZE):
    batch = target_articles[i : i + BATCH_SIZE]
    print(f"  Fetching batch {i//BATCH_SIZE + 1} ({len(batch)} articles)...")
    
    batch_links = get_outlinks_bulk(batch)
    all_links.update(batch_links)
    time.sleep(1)  # Respect API limits

duration = time.time() - start_time
print(f"  >> Download complete in {duration:.1f} seconds.")

# Save raw links
raw_links_path = DATA_DIR / 'raw_links_step2.json'
with open(raw_links_path, 'w', encoding='utf-8') as f:
    json.dump(all_links, f, indent=2, ensure_ascii=False)
print(f"  >> Saved raw links to {raw_links_path.name}")


# 3. Construct Directed Graph
print("\n[2/3] Constructing directed graph (NetworkXDiGraph)...")

G = nx.DiGraph()

# Add all target articles as nodes first
for article in target_articles:
    G.add_node(article, is_core=True)

# Add edges
edge_count = 0
for source, targets in all_links.items():
    for target in targets:
        # We only want to add edges if the target is ALSO in our domain set
        # Otherwise the graph explodes to millions of random Wikipedia nodes
        if target in df_articles['article'].values:
            G.add_edge(source, target)
            edge_count += 1

print("\n[3/3] Graph Summary:")
print(f"  Nodes (Articles): {G.number_of_nodes()}")
print(f"  Edges (Links):    {G.number_of_edges()}")
print(f"  Density:          {nx.density(G):.6f}")

if not nx.is_directed_acyclic_graph(G):
    print("  Graph contains cycles (expected for Wikipedia).")


# 4. Save the Graph
# We save in two formats to satisfy the "compare 2 storage strategies" requirement
print("\nSaving graph representations...")

# Storage Strategy A: GraphML (Standard XML format for graphs, keeps metadata)
graphml_path = GRAPHS_DIR / 'symptoms_graph.graphml'
nx.write_graphml(G, graphml_path)
print(f"  >> Saved as GraphML: {graphml_path.name} ({os.path.getsize(graphml_path)/1024:.1f} KB)")

# Storage Strategy B: Edge List (CSV, highly scalable for databases)
edgelist_path = DATA_DIR / 'symptoms_edgelist.csv'
nx.write_edgelist(G, edgelist_path, delimiter=',', data=False)
print(f"  >> Saved as Edge List: {edgelist_path.name} ({os.path.getsize(edgelist_path)/1024:.1f} KB)")

print("\nStep 2 Complete! Run step4_temporal.py next.")
