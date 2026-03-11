# Step 5: Graph Metrics (Degree, Centrality, Connectivity)
# Computes key network metrics for the Wikipedia link graph.
# Uses GPU acceleration via RAPIDS cuGraph if available.

import networkx as nx
import pandas as pd
import time
import os
from pathlib import Path

# Try to import GPU-accelerated graph library (RAPIDS cuGraph)
try:
    import cugraph
    import cudf
    USE_GPU = True
    print("🚀 CUDA GPU Detected! cuGraph will be used for heavy metrics.")
except ImportError:
    USE_GPU = False
    print("🐢 No cuGraph found. Falling back to CPU via NetworkX (might be slow).")

# Setup paths
DATA_DIR = Path('../data')
GRAPHS_DIR = Path('../graphs')
graphml_path = GRAPHS_DIR / 'symptoms_graph.graphml'

print("=" * 60)
print("  Step 5: Graph Metrics Computation")
print("=" * 60)

# 1. Load Graph
print(f"\n[1/3] Loading GraphML from {graphml_path.name}...")
start = time.time()
G = nx.read_graphml(graphml_path)

# Ensure nodes are native types (GraphML loads them as strings sometimes)
G = nx.convert_node_labels_to_integers(G, label_attribute='article_name')
print(f"  → Loaded in {time.time()-start:.2f}s")
print(f"  Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()}")

# 2. Compute Metrics
print("\n[2/3] Computing Centrality & Connectivity Metrics...")
metrics = []

if USE_GPU:
    # --- GPU ACCELERATED FAST PATH ---
    start = time.time()
    
    # 1. Convert to cuGraph
    cg = cugraph.from_networkx(G)
    print(f"  [GPU] Graph converted to cuGraph structure ({time.time()-start:.2f}s)")
    
    # 2. Degree Centrality
    s2 = time.time()
    df_degree = cugraph.degree_centrality(cg)
    print(f"  [GPU] Degree Centrality done in {time.time()-s2:.2f}s")
    
    # 3. PageRank (often better than betweenness for large dense wiki graphs)
    s2 = time.time()
    df_pr = cugraph.pagerank(cg, alpha=0.85, max_iter=100)
    print(f"  [GPU] PageRank done in {time.time()-s2:.2f}s")
    
    # Merge GPU DataFrames and convert back to Pandas
    df_metrics_gpu = df_degree.merge(df_pr, on='vertex')
    df_metrics = df_metrics_gpu.to_pandas()
    
    # Map integer IDs back to actual article names
    mapping = nx.get_node_attributes(G, 'article_name')
    df_metrics['article'] = df_metrics['vertex'].map(mapping)
    df_metrics = df_metrics.set_index('article').drop(columns=['vertex'])
    
    total = time.time() - start
    print(f"  → GPU Metrics complete in {total:.2f}s total")

else:
    # --- CPU FALLBACK (NetworkX) ---
    start = time.time()
    
    print("  [CPU] Computing In/Out Degrees...")
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())
    
    print("  [CPU] Computing Degree Centrality...")
    deg_cent = nx.degree_centrality(G)
    
    print("  [CPU] Computing PageRank (approximation for global hub status)...")
    pagerank = nx.pagerank(G, alpha=0.85)

    # For betweenness centrality on CPU, doing it on 4000 nodes takes ages.
    # We will sample 10% of nodes if falling back to CPU.
    print("  [CPU] Computing Betweenness Centrality (Estimating on k=300 nodes)...")
    bet_cent = nx.betweenness_centrality(G, k=300, seed=42)
    
    # Build dataframe
    mapping = nx.get_node_attributes(G, 'article_name')
    
    df_metrics = pd.DataFrame({
        'in_degree': in_degree,
        'out_degree': out_degree,
        'degree_centrality': deg_cent,
        'pagerank': pagerank,
        'betweenness': bet_cent
    })
    
    # Map index back to string names
    df_metrics.index = [mapping[i] for i in df_metrics.index]
    df_metrics.index.name = 'article'

    total = time.time() - start
    print(f"  → CPU Metrics complete in {total:.2f}s total")


# 3. View & Save Results
print("\n[3/3] Analysis Results")

# Sort by PageRank (best indicator of global importance in Wikipedia)
df_metrics = df_metrics.sort_values(by='pagerank', ascending=False)

print("\n🏆 Top 15 Most Important COVID-19 Symptoms Articles (by PageRank):")
print(df_metrics.head(15).to_string())

output_csv = DATA_DIR / 'network_metrics.csv'
df_metrics.to_csv(output_csv)
print(f"\n  → Saved full metrics to: {output_csv.name}")

print("\nStep 5 Complete! Run step6_dashboard.py next.")
