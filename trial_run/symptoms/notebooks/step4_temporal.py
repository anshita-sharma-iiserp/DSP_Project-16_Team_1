# Step 4: Temporal Analysis
# Compares the Wikipedia link structure of COVID-19 Symptoms between two distinct dates
# Requires parsing raw Wikitext revisions, as live API only shows current links.

import requests
import networkx as nx
import pandas as pd
import re
import time
import os
import json
from pathlib import Path

DATA_DIR = Path('../data')
GRAPHS_DIR = Path('../graphs')
os.makedirs(GRAPHS_DIR, exist_ok=True)

# Wikimedia API requires a User-Agent header
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'DSP-Project-COVID19/1.0 (pratiksahoo3551@gmail.com) Python/requests'
})

def get_revision_wikitext(page_title, timestamp):
    """
    Fetch the raw wikitext of an article as it existed exactly on a given timestamp.
    """
    url = 'https://en.wikipedia.org/w/api.php'
    params = {
        'action':  'query',
        'titles':  page_title,
        'prop':    'revisions',
        'rvprop':  'content',
        'rvlimit': 1,
        'rvstart': timestamp,  # The anchor date
        'rvdir':   'older',    # Get the revision right *before* or *on* this date
        'format':  'json',
        'rvslots': 'main'
    }
    
    try:
        r = SESSION.get(url, params=params, timeout=10).json()
        pages = r.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if 'missing' in page_data:
                return None  # Article did not exist yet
            
            revisions = page_data.get('revisions', [])
            if not revisions:
                return None
                
            # Extract raw wikitext
            return revisions[0].get('slots', {}).get('main', {}).get('*', '')
    except Exception as e:
        print(f"    Error fetching {page_title} at {timestamp}: {e}")
        return None

def extract_wikilinks(wikitext):
    """
    Uses Regex to extract all internal Wikipedia links from raw Wikitext.
    Handles piped links [[Target|Display Text]] -> 'Target'
    Ignores Files, Categories, and Interwiki links.
    """
    if not wikitext:
        return []
        
    # Regex: Match everything inside [[ ... ]]
    link_pattern = re.compile(r'\[\[(.*?)\]\]')
    matches = link_pattern.findall(wikitext)
    
    clean_links = []
    exclude_prefixes = ('file:', 'category:', 'image:', 'wikipedia:', 'wp:', 'http', ':')
    
    for match in matches:
        # Handle piped links: take everything before the pipe
        target = match.split('|')[0].strip()
        
        # Strip section anchors #
        target = target.split('#')[0].strip()
        
        if not target:
            continue
            
        # Ignore special namespaces
        if target.lower().startswith(exclude_prefixes):
            continue
            
        # Normalize first letter capitalization globally (Wikipedia standard)
        target = target[0].upper() + target[1:] if len(target) > 0 else target
        clean_links.append(target)
        
    return list(set(clean_links))


print("=" * 60)
print("  Step 4: Temporal Analysis (2020 vs 2026)")
print("=" * 60)

# Load target articles (Using the 386 core articles from step 2 for speed)
input_path = DATA_DIR / 'discovered_articles.csv'
df_articles = pd.read_csv(input_path)
target_articles = df_articles[
    df_articles['source'].isin(['seed', 'category', 'backlink'])
]['article'].tolist()

if len(target_articles) > 500:
    target_articles = target_articles[:500]

print(f"Analyzing historical evolution of {len(target_articles)} core articles...\n")

# Define timestamps
SNAPSHOTS = {
    '2020': '2020-04-01T23:59:59Z',  # Start of pandemic
    '2026': '2026-03-01T23:59:59Z'   # Present day
}

temporal_graphs = {}
metrics_history = {}

for year, timestamp in SNAPSHOTS.items():
    print(f"\n[1/3] Building Graph for {year} (Timestamp: {timestamp})")
    
    G = nx.DiGraph()
    G.graph['year'] = year
    missing_nodes = 0
    
    # 1. Fetch text and extract links
    start_time = time.time()
    for i, article in enumerate(target_articles):
        # Progress indicator
        if (i+1) % 50 == 0:
            print(f"  Processed {i+1}/{len(target_articles)} articles...")
            
        wikitext = get_revision_wikitext(article, timestamp)
        
        if wikitext is None:
            missing_nodes += 1
            continue  # Article didn't exist in this year!
            
        G.add_node(article)
        
        links = extract_wikilinks(wikitext)
        for link in links:
            # Only add edge if the target is in our known vocabulary of 3867 articles
            # to prevent graph explosion
            if link in df_articles['article'].values:
                G.add_edge(article, link)
        time.sleep(0.1) # Be nice to API

    # 2. Save Graph structure
    nx.write_graphml(G, GRAPHS_DIR / f'symptoms_graph_{year}.graphml')
    
    # 3. Calculate basic metrics
    density = nx.density(G)
    pr = nx.pagerank(G, alpha=0.85) if G.number_of_nodes() > 0 else {}
    
    temporal_graphs[year] = G
    metrics_history[year] = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
        'missing_or_uncreated': missing_nodes,
        'density': density,
        'pagerank': pr
    }
    
    print(f"  => {year} Graph Built in {time.time()-start_time:.1f}s")
    print(f"     Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()} | Density: {density:.5f}")


print("\n[2/3] Analyzing Temporal Shifts (2020 -> 2026)")

m2020 = metrics_history['2020']
m2026 = metrics_history['2026']

print(f"\n  Structrual Evolution:")
print(f"    - Network Growth: {m2020['nodes']} -> {m2026['nodes']} symptom articles (+{m2026['nodes']-m2020['nodes']})")
print(f"    - Edge Growth: {m2020['edges']} -> {m2026['edges']} connections (+{m2026['edges']-m2020['edges']})")
print(f"    - Density Shift: {m2020['density']:.5f} -> {m2026['density']:.5f}")

# Calculate Top 10 Hub Shifts
df_pr2020 = pd.Series(m2020['pagerank'], name='pr_2020').to_frame()
df_pr2026 = pd.Series(m2026['pagerank'], name='pr_2026').to_frame()

df_shifts = df_pr2026.join(df_pr2020, how='outer').fillna(0)
df_shifts['shift'] = df_shifts['pr_2026'] - df_shifts['pr_2020']
df_shifts = df_shifts.sort_values(by='pr_2026', ascending=False)

print("\n  Top 10 Knowledge Hubs (2026) vs their 2020 Importance:")
print(df_shifts.head(10).to_string())

# Find articles that became WAY more important (Highest Positive Shift)
surge = df_shifts.sort_values(by='shift', ascending=False).head(5)
print("\n  Top 5 Surging Nodes (Became central between 2020-2026):")
print(surge.to_string())

# Save analysis to CSV
df_shifts.to_csv(DATA_DIR / 'temporal_shifts.csv')
print("\n[3/3] Temporal Data Saved.")
print(f"  - Data: {DATA_DIR}/temporal_shifts.csv")
print(f"  - Graphs: {GRAPHS_DIR}/symptoms_graph_2020.graphml, symptoms_graph_2026.graphml")

print("\nStep 4 Complete! 🎉")
