# How to Import Pre-computed Centrality Metrics into the Dashboard

Hi Aadya! 

I have pre-computed all the heavy PageRank, Betweenness, Eigenvector, and Degree Centrality mathematics for the 2024, 2025, and 2026 Wikipedia graphs. This will save the Streamlit dashboard from crashing or taking forever to load Nidhi's massive 40,000+ line graph.

Here is exactly how you can plug my pre-computed data into your dashboard code!

### 1. The Handoff File
Inside the `pratik_progress` folder, there is a file called `centrality_master_export.csv`. Keep this alongside your dashboard script.

### 2. Updating `dashboard_code.py`

You currently have a `@st.cache_data` function called `compute_metrics(_G)` that runs `nx.betweenness_centrality()` natively. 

**Delete or comment out your entire `compute_metrics(_G)` function and replace it with this:**

```python
import pandas as pd
import streamlit as st

@st.cache_data
def load_pratiks_centrality_data():
    # Load the pre-computed metrics
    return pd.read_csv("pratik_progress/centrality_master_export.csv")

def get_metrics_for_year(year):
    # Retrieve the exact mathematical columns for the specific snapshot
    df_all = load_pratiks_centrality_data()
    df_year = df_all[df_all["year"] == year].copy()
    
    # Sort by PageRank to match your previous dataframe format
    df_year = df_year.sort_values("pagerank", ascending=False).reset_index(drop=True)
    return df_year
```

### 3. Usage in your loop

Where you previously had your snapshot loop:
```python
    for year, _G in snapshots.items():
        df, _G = compute_metrics(_G)
        top = df.head(top_n)[["article", metric]].copy()
```

You can now use my instantaneous function:
```python
    for year, _G in snapshots.items():
        # df, _G = compute_metrics(_G)  <-- Delete this
        df = get_metrics_for_year(year) # <-- Use this!
        
        top = df.head(top_n)[["article", metric]].copy()
```

### Note on Columns:
My CSV perfectly matches your exact expected names (`in_degree`, `out_degree`, `pagerank`, `betweenness`, `article`). It natively contains raw integers for the In/Out degree, so your hover labels (`In-degree: 154`) will continue working perfectly without decimals!
