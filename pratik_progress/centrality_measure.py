import networkx as nx
import pandas as pd
import time
import os

# Paths to the graphs Nidhi provided
graphs_to_process = {
    "2020": "nidhi_progress/gexf_version_8/COVID_19_2020.gexf",
    "2021": "nidhi_progress/gexf_version_8/COVID_19_2021.gexf",
    "2022": "nidhi_progress/gexf_version_8/COVID_19_2022.gexf",
    "2023": "nidhi_progress/gexf_version_8/COVID_19_2023.gexf",
    "2024": "nidhi_progress/gexf_version_8/COVID_19_2024.gexf",
    "2025": "nidhi_progress/gexf_version_8/COVID_19_2025.gexf",
    "2026": "nidhi_progress/gexf_version_8/COVID_19_2026.gexf"
}

def analyze_centrality(filepath, year):
    print(f"\n{'-'*40}")
    print(f" Analyzing Centrality for {year}")
    print(f"{'-'*40}")
    
    start = time.time()
    # Read graph
    G = nx.read_gexf(filepath)
    print(f"[OK] Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges in {time.time()-start:.2f}s")
    
    # 1. PageRank Centrality (Global importance)
    print("Computing PageRank Centrality...")
    t0 = time.time()
    pagerank = nx.pagerank(G, alpha=0.85)
    print(f"  -> Done in {time.time()-t0:.2f}s")
    
    # 2. Degree Centrality (Local immediate importance)
    print("Computing In/Out Degree Centrality...")
    t0 = time.time()
    in_degree_cent = nx.in_degree_centrality(G)
    out_degree_cent = nx.out_degree_centrality(G)
    
    # Raw degree counts (Dashboard expects integers for hover text)
    in_degree_raw = dict(G.in_degree())
    out_degree_raw = dict(G.out_degree())
    print(f"  -> Done in {time.time()-t0:.2f}s")
    
    # 3. Betweenness Centrality (Bottlenecks / Bridges)
    # Sampling k=500 nodes to ensure it calculates quickly while remaining statistically accurate for large graphs
    k_samples = min(500, G.number_of_nodes())
    print(f"Computing Betweenness Centrality (Approximation k={k_samples})...")
    t0 = time.time()
    betweenness = nx.betweenness_centrality(G, k=k_samples, seed=42)
    print(f"  -> Done in {time.time()-t0:.2f}s")
    
    # 4. Eigenvector Centrality (Influence from other influential nodes)
    print("Computing Eigenvector Centrality...")
    t0 = time.time()
    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=600, tol=1e-4)
        print(f"  -> Done in {time.time()-t0:.2f}s")
    except nx.PowerIterationFailedConvergence:
        print("  -> Eigenvector centrality failed to converge. Defaulting to 0.")
        eigenvector = {n: 0 for n in G.nodes()}

    # Combine all metrics into a Pandas DataFrame
    df = pd.DataFrame({
        'article': list(G.nodes()),
        'year': year,
        'pagerank': [pagerank.get(n, 0) for n in G.nodes()],
        'in_degree': [in_degree_raw.get(n, 0) for n in G.nodes()],       # Raw integer for dashboard
        'out_degree': [out_degree_raw.get(n, 0) for n in G.nodes()],     # Raw integer for dashboard
        'in_degree_cent': [in_degree_cent.get(n, 0) for n in G.nodes()], # Float centrality
        'out_degree_cent': [out_degree_cent.get(n, 0) for n in G.nodes()],# Float centrality
        'betweenness': [betweenness.get(n, 0) for n in G.nodes()],
        'eigenvector': [eigenvector.get(n, 0) for n in G.nodes()]
    })
    
    return df

if __name__ == "__main__":
    
    # Optional: Create your own output directory to keep things organized
    output_dir = "pratik_progress"
    os.makedirs(output_dir, exist_ok=True)
    
    all_dfs = []
    
    for year, path in graphs_to_process.items():
        if os.path.exists(path):
            df = analyze_centrality(path, year)
            all_dfs.append(df)
        else:
            print(f"[!] Warning: File {path} not found. Skipping {year}.")
            
    if all_dfs:
        print(f"\nCombining all years and exporting to CSV...")
        final_df = pd.concat(all_dfs, ignore_index=True)
        
        # Sort by year and pagerank to make the CSV inherently useful
        final_df = final_df.sort_values(by=['year', 'pagerank'], ascending=[True, False])
        
        out_csv = os.path.join(output_dir, "centrality_master_export.csv")
        final_df.to_csv(out_csv, index=False)
        
        print(f"\n[DONE] All centrality metrics computed successfully!")
        print(f"[DONE] Exported to: {out_csv}")
        print("\nYou can now tell Aadya to load this CSV in her dashboard using 'pd.read_csv()'!")
    else:
        print("\n[ERROR] No graphs were processed.")
