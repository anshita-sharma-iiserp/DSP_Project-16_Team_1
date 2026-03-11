# Step 1: Article Discovery — COVID-19 Symptoms
# Run this script first to identify your article set before building the graph.

import requests
import json
import time
import pandas as pd
import os

os.makedirs('../data', exist_ok=True)

# Wikimedia API requires a User-Agent header
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'DSP-Project-COVID19/1.0 (pratiksahoo3551@gmail.com) Python/requests'
})

# ─────────────────────────────────────────────
# METHOD 1: Category Expansion via Wikimedia API
# Gets all articles inside a Wikipedia category
# ─────────────────────────────────────────────

def get_category_members(category, limit=500):
    """Fetch all article titles from a Wikipedia category."""
    url = 'https://en.wikipedia.org/w/api.php'
    articles = []
    cmcontinue = None

    while True:
        params = {
            'action':  'query',
            'list':    'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': 50,
            'cmtype':  'page',       # only articles, not subcategories
            'format':  'json'
        }
        if cmcontinue:
            params['cmcontinue'] = cmcontinue

        r = SESSION.get(url, params=params, timeout=10).json()
        for member in r.get('query', {}).get('categorymembers', []):
            articles.append(member['title'])

        if 'continue' in r and len(articles) < limit:
            cmcontinue = r['continue']['cmcontinue']
        else:
            break
        time.sleep(0.3)

    return articles


def get_subcategories(category):
    """Fetch subcategory names inside a Wikipedia category."""
    url = 'https://en.wikipedia.org/w/api.php'
    params = {
        'action':  'query',
        'list':    'categorymembers',
        'cmtitle': f'Category:{category}',
        'cmlimit': 50,
        'cmtype':  'subcat',
        'format':  'json'
    }
    r = SESSION.get(url, params=params, timeout=10).json()
    subcats = []
    for member in r.get('query', {}).get('categorymembers', []):
        # Strip 'Category:' prefix
        subcats.append(member['title'].replace('Category:', ''))
    return subcats


# ─────────────────────────────────────────────
# METHOD 2: Link Expansion
# Start from seed articles and find what they link to
# ─────────────────────────────────────────────

def get_outlinks(page_title):
    """Get all articles linked from a Wikipedia page."""
    url = 'https://en.wikipedia.org/w/api.php'
    links = []
    plcontinue = None

    while True:
        params = {
            'action':      'query',
            'titles':      page_title,
            'prop':        'links',
            'pllimit':     'max',
            'plnamespace': 0,
            'format':      'json'
        }
        if plcontinue:
            params['plcontinue'] = plcontinue

        r = SESSION.get(url, params=params, timeout=10).json()
        for page_data in r.get('query', {}).get('pages', {}).values():
            for link in page_data.get('links', []):
                links.append(link['title'])

        if 'continue' in r:
            plcontinue = r['continue']['plcontinue']
        else:
            break
        time.sleep(0.3)

    return links


def get_backlinks(page_title, limit=200):
    """Get articles that link TO this page (in-links)."""
    url = 'https://en.wikipedia.org/w/api.php'
    links = []
    blcontinue = None

    while True:
        params = {
            'action':    'query',
            'list':      'backlinks',
            'bltitle':   page_title,
            'bllimit':   50,
            'blnamespace': 0,
            'format':    'json'
        }
        if blcontinue:
            params['blcontinue'] = blcontinue

        r = SESSION.get(url, params=params, timeout=10).json()
        for bl in r.get('query', {}).get('backlinks', []):
            links.append(bl['title'])

        if 'continue' in r and len(links) < limit:
            blcontinue = r['continue']['blcontinue']
        else:
            break
        time.sleep(0.3)

    return links


# ══════════════════════════════════════════════
# MAIN: Discover articles for COVID-19 SYMPTOMS
# ══════════════════════════════════════════════

print("=" * 55)
print("  Step 1: Wikipedia Article Discovery")
print("  Domain: COVID-19 | Sub-topic: Symptoms")
print("=" * 55)

# ── 1. Category-based discovery ──────────────
# These are the most relevant Wikipedia categories for COVID-19 symptoms
TARGET_CATEGORIES = [
    'COVID-19',
    'Symptoms of COVID-19',
    'Long COVID',
    'COVID-19 pandemic',
]

print("\n[1/3] Fetching articles from categories...")
category_articles = set()

for cat in TARGET_CATEGORIES:
    print(f"  Category: '{cat}' ...", end=' ')
    # Also fetch subcategories one level deep
    subcats = get_subcategories(cat)
    members = get_category_members(cat)
    category_articles.update(members)
    print(f"{len(members)} articles | {len(subcats)} subcategories")

    for subcat in subcats[:5]:  # Limit to avoid explosion
        sub_members = get_category_members(subcat, limit=30)
        category_articles.update(sub_members)

print(f"  >> Total from categories: {len(category_articles)} articles")

# ── 2. Seed article link expansion ────────────
SYMPTOM_SEEDS = [
    'COVID-19',
    'Symptoms of COVID-19',
    'Long COVID',
    'Anosmia',
    'Ageusia',
    'Dyspnea',
    'Fatigue',
    'Fever',
    'Cough',
    'Cytokine storm',
    'Pneumonia',
    'SARS-CoV-2',
    'Post-acute sequelae of COVID-19',
]

print("\n[2/3] Collecting outlinks from seed articles...")
seed_outlinks = set()

for seed in SYMPTOM_SEEDS:
    print(f"  Expanding: '{seed}' ...", end=' ')
    try:
        links = get_outlinks(seed)
        seed_outlinks.update(links)
        print(f"{len(links)} links")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(0.5)

print(f"  >> Total outlinks found: {len(seed_outlinks)}")

# ── 3. Backlinks for main article ─────────────
print("\n[3/3] Fetching backlinks for 'Symptoms of COVID-19'...")
backlinks = get_backlinks('Symptoms of COVID-19', limit=200)
print(f"  >> {len(backlinks)} articles link to 'Symptoms of COVID-19'")

# ══════════════════════════════════════════════
# Combine & filter all discovered articles
# ══════════════════════════════════════════════

all_articles = category_articles | seed_outlinks | set(backlinks) | set(SYMPTOM_SEEDS)

# Filter: remove articles that are clearly not relevant
EXCLUDE_KEYWORDS = [
    'Wikipedia:', 'Template:', 'Help:', 'File:', 'Portal:',
    'Talk:', 'User:', 'List of', 'Draft:', 'Module:'
]
filtered = [
    a for a in all_articles
    if not any(a.startswith(kw) for kw in EXCLUDE_KEYWORDS)
]

print(f"\n{'='*55}")
print(f"  DISCOVERY SUMMARY")
print(f"{'='*55}")
print(f"  From categories:    {len(category_articles)}")
print(f"  From link expansion: {len(seed_outlinks)}")
print(f"  From backlinks:     {len(backlinks)}")
print(f"  Total (raw):        {len(all_articles)}")
print(f"  After filtering:    {len(filtered)}")
print(f"  Seed articles:      {len(SYMPTOM_SEEDS)} (always included)")

# Save results
df = pd.DataFrame({
    'article': sorted(filtered),
    'is_seed': [a in SYMPTOM_SEEDS for a in sorted(filtered)],
    'source':  [
        'seed' if a in SYMPTOM_SEEDS
        else 'category' if a in category_articles
        else 'backlink' if a in backlinks
        else 'outlink'
        for a in sorted(filtered)
    ]
})

output_path = '../data/discovered_articles.csv'
df.to_csv(output_path, index=False)
print(f"\n  Saved to: {os.path.abspath(output_path)}")
print(f"\nSample articles discovered:")
print(df[df['is_seed'] == False].head(20).to_string(index=False))
