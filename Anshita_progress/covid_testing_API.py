"""
import wikipediaapi

wiki = wikipediaapi.Wikipedia('MyCOVIDProject/1.0 (anshita.sharma@students.iiserpune.ac.in)', 'en')
page = wiki.page("COVID-19 testing")

print(f"Title: {page.title}")
print(f"Links count: {len(page.links)}")  # All outgoing links

# See first 10 links
for title, link in list(page.links.items())[:10]:
    print(f"   -> {title}")

    """
# wikipediaapi seems to be not a good idea for revision history. So we use requests + API endpoint in URL 
import requests
import json
import time
from datetime import datetime
import os

# Your article focus (start with one, expand later)

ARTICLE = "COVID-19 testing"  

# Wikipedia API endpoint
URL = "https://en.wikipedia.org/w/api.php"


HEADERS = {
    'User-Agent': 'COVIDLinkAnalysis/1.0 (anshita.sharma@students.iiserpune.ac.in)'
}

# Snapshots
SNAPSHOTS = [
    {"name": "pre_pandemic", "date": "2020-01-01T00:00:00Z"},
    {"name": "early_pandemic", "date": "2020-06-01T00:00:00Z"},
    {"name": "mid_pandemic", "date": "2021-06-01T00:00:00Z"},
    {"name": "late_pandemic", "date": "2022-06-01T00:00:00Z"},
    {"name": "current", "date": "2024-01-01T00:00:00Z"}
]
#Get all outgoing links from an article as they existed at snapshot_date
def get_links_at_snapshot(article_title, snapshot_date):

    print(f"  Fetching links for {snapshot_date}...")
    
    
    params = {                                       #Step-1 Revision ID closest to our target date
        "action": "query",
        "format": "json",
        "titles": article_title,
        "prop": "revisions",
        "rvstart": snapshot_date,
        "rvlimit": 1,
        "rvdir": "older",
        "rvprop": "ids|timestamp"
    }
    
    response = requests.get(URL, headers=HEADERS, params=params)
    data = response.json()
    

    pages = data.get('query', {}).get('pages', {})                     # Extract revision ID
    page_id = list(pages.keys())[0]
    
    if 'revisions' not in pages[page_id]:
        print(f"    No revision found for {snapshot_date}")
        return []
    
    revision_id = pages[page_id]['revisions'][0]['revid']
    revision_timestamp = pages[page_id]['revisions'][0]['timestamp']
    print(f"    Found revision {revision_id} from {revision_timestamp}")
    
    # Step 2: Get all links from that specific revision
    # Method A: Parse from content (more accurate but slower)
    params = {
        "action": "parse",
        "format": "json",
        "oldid": revision_id,
        "prop": "links"
    }
    
    response = requests.get(URL, headers=HEADERS, params=params)
    data = response.json()
    
    links = []
    if 'parse' in data and 'links' in data['parse']:
        for link in data['parse']['links']:
            # Filter for main namespace articles (not File:, Category:, etc.)
            if link.get('ns') == 0:  # ns=0 is main article space
                links.append(link['*'])
    
    print(f"    Found {len(links)} links")
    return links

def test_different_storage_methods(article_title):
    """
    Compare storage strategies for dashboard friendliness
    """
    print(f"\n=== Testing storage methods for '{article_title}' ===\n")
    
    all_snapshot_data = {}
    
    # Collect data for all snapshots
    for snapshot in SNAPSHOTS:
        links = get_links_at_snapshot(article_title, snapshot['date'])
        all_snapshot_data[snapshot['name']] = {
            'date': snapshot['date'],
            'links': links,
            'count': len(links)
        }
        time.sleep(1)  # Be nice to the API
    
    # STORAGE METHOD 1: Separate files per snapshot
    print("\n--- Method 1: Separate files per snapshot ---")
    
    # Create a directory
    os.makedirs('snapshot_files', exist_ok=True)
    
    for snapshot_name, data in all_snapshot_data.items():
        filename = f"snapshot_files/{article_title.replace(' ', '_')}_{snapshot_name}.json"
        with open(filename, 'w') as f:
            # Store just the links (minimal)
            json.dump(data['links'], f, indent=2)
        print(f"  Saved {data['count']} links to {filename}")
    
    # STORAGE METHOD 2: Single file with all snapshots
    print("\n--- Method 2: Single file with time dimension ---")
    
    filename = f"snapshot_files/{article_title.replace(' ', '_')}_all_snapshots.json"
    with open(filename, 'w') as f:
        # Store structured data with metadata
        json.dump({
            'article': article_title,
            'snapshots': all_snapshot_data,
            'metadata': {
                'retrieved': datetime.now().isoformat(),
                'snapshot_count': len(SNAPSHOTS)
            }
        }, f, indent=2)
    print(f"  Saved all snapshots to {filename}")
    
    # STORAGE METHOD 3: Edge table format (database-friendly)
    print("\n--- Method 3: Edge table format (database-ready) ---")
    
    edge_table = []
    for snapshot_name, data in all_snapshot_data.items():
        for link in data['links']:
            edge_table.append({
                'source': article_title,
                'target': link,
                'snapshot': snapshot_name,
                'date': data['date'],
                'timestamp': int(time.time())  # placeholder
            })
    
    filename = f"snapshot_files/{article_title.replace(' ', '_')}_edge_table.json"
    with open(filename, 'w') as f:
        json.dump(edge_table, f, indent=2)
    print(f"  Saved {len(edge_table)} edges to {filename}")
    
    # Quick comparison stats
    print("\n=== Storage Comparison ===")
    print(f"Method 1 (separate files): {len(SNAPSHOTS)} files, easy to load one snapshot")
    print(f"Method 2 (combined): 1 file, easy to see evolution")
    print(f"Method 3 (edge table): 1 file, database import ready")
    
    return all_snapshot_data

def analyze_temporal_changes(data):
    """
    Simple analysis of how links changed
    """
    print("\n=== Temporal Analysis ===")
    
    snapshots = list(data.keys())
    
    for i in range(len(snapshots)-1):
        current = snapshots[i]
        next_snap = snapshots[i+1]
        
        current_links = set(data[current]['links'])
        next_links = set(data[next_snap]['links'])
        
        added = next_links - current_links
        removed = current_links - next_links
        
        print(f"\n{current} → {next_snap}:")
        print(f"  Links before: {len(current_links)}")
        print(f"  Links after: {len(next_links)}")
        print(f"  Added: {len(added)}")
        print(f"  Removed: {len(removed)}")
        
        # Show examples
        if added:
            print(f"  Sample added: {list(added)[:3]}")
        if removed:
            print(f"  Sample removed: {list(removed)[:3]}")


if __name__ == "__main__":
    print("=" * 50)
    print("WIKIPEDIA LINK ANALYSIS PROTOTYPE")
    print("=" * 50)
    
    # Test with a single article first
    article = "COVID-19 testing"  
    print(f"\nAnalyzing: {article}")
    
    
    data = test_different_storage_methods(article)
    
    analyze_temporal_changes(data)
    
    print("Next: Check the 'snapshot_files' folder to see the different storage formats")
    print("Discuss with team: Which storage method feels right for your dashboard?")