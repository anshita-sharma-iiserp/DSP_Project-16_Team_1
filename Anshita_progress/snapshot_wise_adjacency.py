# -*- coding: utf-8 -*-
"""Wikipedia Link Analysis - Temporal Snapshots with Heatmaps"""

import requests
import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime
import time

# User-Agent header for API requests
headers = {"User-Agent": "WikiNetworkProject/1.0"}

# ============ HELPER FUNCTIONS ============
80
def filter_links(links):
    """Remove Wikipedia administrative pages and non-article namespaces"""
    bad_prefixes = ("Help:", "File:", "Category:", "Special:", "Talk:", "Wikipedia:", "Template:", "Portal:")
    return [l for l in links if not l.startswith(bad_prefixes)]

def get_top_revisions(title, limit=5):
    """Fetch most recent revisions of an article"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "rvlimit": limit,
        "prop": "revisions",
        "rvprop": "ids|timestamp",
        "format": "json"
    }

    r = requests.get(url, params=params, headers=headers).json()
    pages = r['query']['pages']

    for page in pages.values():
        return page.get("revisions", [])

    return []

def get_latest_revision(title):
    """Fetch the latest revision ID of an article"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "rvlimit": 1,
        "prop": "revisions",
        "rvprop": "ids|timestamp",
        "format": "json"
    }

    r = requests.get(url, params=params, headers=headers).json()
    pages = r['query']['pages']

    for page in pages.values():
        revs = page.get("revisions", [])
        if revs:
            return revs[0]

    return None

def get_closest_revision(title, target_timestamp):
    """Find the revision closest to (but not after) target_timestamp"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "rvlimit": 10,
        "rvprop": "ids|timestamp",
        "rvstart": target_timestamp,
        "rvdir": "older",
        "prop": "revisions",
        "format": "json"
    }

    r = requests.get(url, params=params, headers=headers).json()
    pages = r['query']['pages']

    for page in pages.values():
        revs = page.get("revisions", [])
        if revs:
            return revs[0]

    return None

def get_links_from_revision(rev_id, max_links):
    """Extract links from a specific revision ID"""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "oldid": rev_id,
        "prop": "links",
        "format": "json"
    }

    r = requests.get(url, params=params, headers=headers).json()

    links = []
    if "parse" in r and "links" in r["parse"]:
        links = [l["*"] for l in r["parse"]["links"] if l["ns"] == 0]

    links = filter_links(links)
    return links[:max_links]

# ============ BUILD TEMPORAL SNAPSHOTS ============

def build_temporal_snapshots(seed_article, max_links=5, num_snapshots=80):
    """
    Build multiple time snapshots of the link network around a seed article.
    
    Returns:
        dict: { "YYYY-MM-DD": adjacency_dict, ... }
        
    Adjacency dict format:
        {
            "Article_Title (rev_id)": ["Linked_Article_1", "Linked_Article_2", ...],
            ...
        }
    """
    snapshots = {}
    
    # Get revision history for the seed article
    revisions = get_top_revisions(seed_article, limit=num_snapshots)
    
    if not revisions:
        print(f"No revisions found for {seed_article}")
        return snapshots
    
    print(f"Building {len(revisions)} snapshots for {seed_article}...")
    
    # Process each revision as a separate snapshot
    for idx, rev in enumerate(revisions):
        rev_id = rev["revid"]
        rev_timestamp = rev["timestamp"]
        snapshot_date = rev_timestamp[:10]  # Format: YYYY-MM-DD
        
        print(f"  Snapshot {idx+1}: {snapshot_date} (rev {rev_id})")
        
        # Build adjacency dictionary for this snapshot
        adj_dict = {}
        
        # --- Hop 0: Seed article at this revision ---
        seed_node = f"{seed_article} ({rev_id})"
        adj_dict[seed_node] = []
        
        # --- Hop 1: Links from seed article at this revision ---
        hop1_links = get_links_from_revision(rev_id, max_links)
        
        for link in hop1_links:
            # Get the closest revision of the linked article that existed at this snapshot time
            child_rev = get_closest_revision(link, rev_timestamp)
            
            if not child_rev:
                continue
            
            child_id = child_rev["revid"]
            child_node = f"{link} ({child_id})"
            
            # Add edge from seed to child
            adj_dict[seed_node].append(child_node)
            
            # --- Hop 2: Links from child article at its revision ---
            hop2_links = get_links_from_revision(child_id, max_links)
            
            # Store child's outgoing links
            adj_dict[child_node] = hop2_links
        
        # Store snapshot with date as key
        snapshots[snapshot_date] = adj_dict
        
        # Small delay to avoid hitting API rate limits
        time.sleep(0.5)
    
    return snapshots

# ============ CONVERT SNAPSHOTS TO NETWORKX GRAPHS ============

def snapshots_to_graphs(snapshots):
    """
    Convert temporal snapshots dictionary to NetworkX DiGraphs.
    
    Returns:
        dict: { timestamp: nx.DiGraph, ... }
    """
    graphs = {}
    
    for timestamp, adj_dict in snapshots.items():
        G = nx.DiGraph()
        
        for source, targets in adj_dict.items():
            for target in targets:
                G.add_edge(source, target)
        
        graphs[timestamp] = G
        
        print(f"{timestamp}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    return graphs

# ============ METRICS COMPUTATION ============

def compute_snapshot_metrics(graphs):
    """
    Compute key graph metrics for each snapshot.
    
    Returns:
        dict: { timestamp: { metric_name: value, ... }, ... }
    """
    metrics = {}
    
    for timestamp, G in graphs.items():
        print(f"Computing metrics for {timestamp}...")
        
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        density = nx.density(G) if n_nodes > 1 else 0
        
        # Degree metrics
        in_degree = dict(G.in_degree())
        out_degree = dict(G.out_degree())
        
        top_in_degree = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:10]
        top_out_degree = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # PageRank
        try:
            pagerank = nx.pagerank(G, max_iter=100)
            top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
        except:
            top_pagerank = []
        
        # NEW: Betweenness centrality (approximated for speed)
        print(f"    Computing betweenness (this may take a moment)...")
        try:
            # Use k=min(100, n_nodes) for approximation
            k_samples = min(100, n_nodes)
            betweenness = nx.betweenness_centrality(G, k=k_samples)
            top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
        except Exception as e:
            print(f"    Betweenness computation failed: {e}")
            top_betweenness = []
        
        # NEW: Clustering coefficient (for directed graphs, using undirected version)
        try:
            G_undirected = G.to_undirected()
            avg_clustering = nx.average_clustering(G_undirected)
        except:
            avg_clustering = 0
        
        # NEW: Average path length (sample for large graphs)
        try:
            if n_nodes < 500:
                avg_path_length = nx.average_shortest_path_length(G_undirected)
            else:
                # Sample 100 nodes for approximation
                nodes_sample = list(G.nodes())[:100]
                avg_path_length = nx.average_shortest_path_length(G_undirected, nodes_sample)
        except:
            avg_path_length = float('inf')
        
        # Connectivity metrics
        scc_count = nx.number_strongly_connected_components(G)
        wcc_count = nx.number_weakly_connected_components(G)
        
        largest_scc = max(nx.strongly_connected_components(G), key=len) if n_nodes > 0 else set()
        largest_scc_size = len(largest_scc)
        
        largest_wcc = max(nx.weakly_connected_components(G), key=len) if n_nodes > 0 else set()
        largest_wcc_size = len(largest_wcc)
        
        # NEW: Diameter (only if graph is connected)
        diameter = None
        try:
            if nx.is_weakly_connected(G):
                # Convert to undirected for diameter
                diameter = nx.diameter(G_undirected)
        except:
            diameter = None
        
        # NEW: Modularity (requires community detection)
        modularity = None
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G_undirected)
            modularity = community_louvain.modularity(partition, G_undirected)
        except:
            modularity = None
        
        metrics[timestamp] = {
            # Basic stats
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "density": round(density, 6),
            "avg_in_degree": round(sum(in_degree.values()) / n_nodes, 2) if n_nodes > 0 else 0,
            "avg_out_degree": round(sum(out_degree.values()) / n_nodes, 2) if n_nodes > 0 else 0,
            
            # Connectivity
            "scc_count": scc_count,
            "largest_scc_size": largest_scc_size,
            "wcc_count": wcc_count,
            "largest_wcc_size": largest_wcc_size,
            "diameter": diameter,
            
            # Advanced metrics
            "avg_clustering": round(avg_clustering, 4),
            "avg_path_length": round(avg_path_length, 2) if avg_path_length != float('inf') else "disconnected",
            "modularity": round(modularity, 4) if modularity else None,
            
            # Top nodes
            "top_10_cited": [(article, score) for article, score in top_in_degree],
            "top_10_linking": [(article, score) for article, score in top_out_degree],
            "top_10_pagerank": [(article, round(score, 4)) for article, score in top_pagerank],
            "top_10_bottlenecks": [(article, round(score, 4)) for article, score in top_betweenness]
        }
    
    return metrics

# ============ TEMPORAL COMPARISON ============

def compare_snapshots(graphs):
    """
    Compare edge sets between consecutive snapshots.
    
    Returns:
        dict: { timestamp: {"added": [...], "removed": [...]}, ... }
    """
    timestamps = sorted(graphs.keys())
    changes = {}
    
    for i in range(1, len(timestamps)):
        prev_ts = timestamps[i-1]
        curr_ts = timestamps[i]
        
        G_prev = graphs[prev_ts]
        G_curr = graphs[curr_ts]
        
        edges_prev = set(G_prev.edges())
        edges_curr = set(G_curr.edges())
        
        added = edges_curr - edges_prev
        removed = edges_prev - edges_curr
        
        changes[curr_ts] = {
            "added_count": len(added),
            "removed_count": len(removed),
            "added_edges": list(added)[:20],
            "removed_edges": list(removed)[:20]
        }
        
        print(f"\nChanges from {prev_ts} to {curr_ts}:")
        print(f"  Added: {len(added)} edges")
        print(f"  Removed: {len(removed)} edges")
    
    return changes

# ============ HEATMAP VISUALIZATIONS ============

def plot_adjacency_heatmap(G, timestamp, save_path=None):
    """
    Create a heatmap visualization of the adjacency matrix.
    Nodes are sorted by degree for better pattern visibility.
    """
    nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
    n = len(nodes)
    
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    
    # Build adjacency matrix
    adj_matrix = np.zeros((n, n))
    for u, v in G.edges():
        if u in node_to_idx and v in node_to_idx:
            adj_matrix[node_to_idx[u], node_to_idx[v]] = 1
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        adj_matrix,
        cmap='Blues',
        cbar_kws={'label': 'Link Exists'},
        xticklabels=False,
        yticklabels=False
    )
    
    plt.title(f"Adjacency Heatmap - {timestamp}\n{n} nodes, {G.number_of_edges()} edges")
    plt.xlabel("Target Articles")
    plt.ylabel("Source Articles")
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
    
    return plt.gcf()

def plot_community_heatmap(G, timestamp, save_path=None):
    """
    Create a heatmap with nodes sorted by community for seeing cluster structure.
    """
    G_undirected = G.to_undirected()
    
    try:
        import community as community_louvain
        partition = community_louvain.best_partition(G_undirected)
        
        # Sort nodes by community ID, then by degree within community
        nodes_by_community = sorted(
            G.nodes(),
            key=lambda x: (partition.get(x, 0), G.degree(x))
        )
        has_communities = True
    except:
        # Fallback to degree sorting
        nodes_by_community = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
        has_communities = False
        partition = {}
    
    n = len(nodes_by_community)
    node_to_idx = {node: i for i, node in enumerate(nodes_by_community)}
    
    # Build matrix
    adj_matrix = np.zeros((n, n))
    for u, v in G.edges():
        if u in node_to_idx and v in node_to_idx:
            adj_matrix[node_to_idx[u], node_to_idx[v]] = 1
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(adj_matrix, cmap='Blues', aspect='auto')
    plt.colorbar(im, ax=ax, label='Link Exists')
    
    # Add community boundary lines
    if has_communities:
        current_community = None
        boundary_positions = []
        for i, node in enumerate(nodes_by_community):
            comm = partition.get(node, 0)
            if current_community is None:
                current_community = comm
            elif comm != current_community:
                boundary_positions.append(i - 0.5)
                current_community = comm
        
        for pos in boundary_positions:
            ax.axhline(y=pos, color='red', linewidth=1, linestyle='--')
            ax.axvline(x=pos, color='red', linewidth=1, linestyle='--')
        
        title = f"Community-Sorted Heatmap - {timestamp}\n(Red lines = community boundaries)"
    else:
        title = f"Degree-Sorted Heatmap - {timestamp}"
    
    ax.set_title(title)
    ax.set_xlabel("Target Articles")
    ax.set_ylabel("Source Articles")
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
    
    return fig

def compare_heatmaps_across_time(graphs, save_dir="heatmaps"):
    """
    Create side-by-side heatmaps for all snapshots.
    """
    import os
    os.makedirs(save_dir, exist_ok=True)
    
    timestamps = sorted(graphs.keys())
    n_snapshots = len(timestamps)
    
    # Side-by-side comparison
    fig, axes = plt.subplots(1, n_snapshots, figsize=(5 * n_snapshots, 4))
    if n_snapshots == 1:
        axes = [axes]
    
    for idx, timestamp in enumerate(timestamps):
        G = graphs[timestamp]
        nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
        n = len(nodes)
        
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        adj_matrix = np.zeros((n, n))
        for u, v in G.edges():
            if u in node_to_idx and v in node_to_idx:
                adj_matrix[node_to_idx[u], node_to_idx[v]] = 1
        
        axes[idx].imshow(adj_matrix, cmap='Blues', aspect='auto')
        axes[idx].set_title(f"{timestamp}\n{n} nodes, {G.number_of_edges()} edges")
        axes[idx].set_xlabel("Target")
        axes[idx].set_ylabel("Source")
        axes[idx].tick_params(labelbottom=False, labelleft=False)
    
    plt.suptitle("Network Density Evolution Over Time", fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{save_dir}/temporal_heatmap_comparison.png", dpi=150)
    
    # Individual community-sorted heatmaps
    for timestamp in timestamps:
        G = graphs[timestamp]
        plot_community_heatmap(G, timestamp, save_path=f"{save_dir}/community_heatmap_{timestamp}.png")
    
    print(f"Heatmaps saved to {save_dir}/")

def plot_sparsity_pattern(G, timestamp, save_path=None):
    """
    Create a sparsity pattern plot for larger graphs.
    """
    nodes = list(G.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    n = len(nodes)
    
    rows, cols = [], []
    for u, v in G.edges():
        rows.append(node_to_idx[u])
        cols.append(node_to_idx[v])
    
    plt.figure(figsize=(10, 8))
    plt.spy([rows, cols], markersize=0.5, aspect='auto')
    plt.title(f"Sparsity Pattern - {timestamp}\n{n} nodes, {G.number_of_edges()} edges")
    plt.xlabel("Target")
    plt.ylabel("Source")
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
    
    return plt.gcf()

# ============ SUMMARY VISUALIZATION ============

def plot_metrics_over_time(metrics, save_path=None):
    """
    Create a multi-panel plot showing key metrics over time.
    """
    timestamps = sorted(metrics.keys())
    
    fig, axes = plt.subplots(2, 80, figsize=(15, 10))
    
    # Nodes and edges
    nodes = [metrics[ts]["n_nodes"] for ts in timestamps]
    edges = [metrics[ts]["n_edges"] for ts in timestamps]
    
    axes[0, 0].plot(timestamps, nodes, marker='o', linewidth=2)
    axes[0, 0].set_title('Nodes Over Time')
    axes[0, 0].set_ylabel('Number of Nodes')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    axes[0, 1].plot(timestamps, edges, marker='o', linewidth=2, color='orange')
    axes[0, 1].set_title('Edges Over Time')
    axes[0, 1].set_ylabel('Number of Edges')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # Density
    density = [metrics[ts]["density"] for ts in timestamps]
    axes[0, 2].plot(timestamps, density, marker='o', linewidth=2, color='green')
    axes[0, 2].set_title('Density Over Time')
    axes[0, 2].set_ylabel('Density')
    axes[0, 2].tick_params(axis='x', rotation=45)
    
    # SCC size
    scc_size = [metrics[ts]["largest_scc_size"] for ts in timestamps]
    axes[1, 0].plot(timestamps, scc_size, marker='o', linewidth=2, color='red')
    axes[1, 0].set_title('Largest SCC Size Over Time')
    axes[1, 0].set_ylabel('Size')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Average degree
    avg_degree = [metrics[ts]["avg_in_degree"] for ts in timestamps]
    axes[1, 1].plot(timestamps, avg_degree, marker='o', linewidth=2, color='purple')
    axes[1, 1].set_title('Average In-Degree Over Time')
    axes[1, 1].set_ylabel('Average Degree')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    # Clustering coefficient
    clustering = [metrics[ts]["avg_clustering"] for ts in timestamps]
    axes[1, 2].plot(timestamps, clustering, marker='o', linewidth=2, color='brown')
    axes[1, 2].set_title('Average Clustering Coefficient')
    axes[1, 2].set_ylabel('Clustering')
    axes[1, 2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
    
    return fig

# ============ MAIN EXECUTION ============

if __name__ == "__main__":
    
    # --- Step 1: Build temporal snapshots ---
    seed = "SARS-CoV-2"
    print(f"Building temporal snapshots for '{seed}'...")
    
    snapshots = build_temporal_snapshots(
        seed_article=seed,
        max_links=5,
        num_snapshots=80
    )
    
    # --- Step 2: Save snapshots to JSON ---
    with open("snapshots.json", "w") as f:
        json.dump(snapshots, f, indent=2)
    print(f"\nSaved {len(snapshots)} snapshots to snapshots.json")
    
    # --- Step 80: Convert to NetworkX graphs ---
    print("\n" + "="*50)
    print("Converting snapshots to NetworkX graphs...")
    graphs = snapshots_to_graphs(snapshots)
    
    # --- Step 4: Compute metrics ---
    print("\n" + "="*50)
    print("Computing metrics...")
    metrics = compute_snapshot_metrics(graphs)
    
    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("\nSaved metrics to metrics.json")
    
    # --- Step 5: Temporal comparison ---
    print("\n" + "="*50)
    print("Analyzing temporal changes...")
    changes = compare_snapshots(graphs)
    
    with open("changes.json", "w") as f:
        json.dump(changes, f, indent=2)
    print("\nSaved changes to changes.json")
    
    # --- Step 6: Heatmap visualizations ---
    print("\n" + "="*50)
    print("Generating heatmap visualizations...")
    compare_heatmaps_across_time(graphs, save_dir="heatmaps")
    
    # Generate individual heatmaps for each snapshot
    for timestamp, G in graphs.items():
        plot_adjacency_heatmap(G, timestamp, save_path=f"heatmaps/adjacency_heatmap_{timestamp}.png")
        print(f"  Saved heatmaps/adjacency_heatmap_{timestamp}.png")
    
    # --- Step 7: Metrics summary plot ---
    print("\n" + "="*50)
    print("Generating metrics summary...")
    plot_metrics_over_time(metrics, save_path="metrics_summary.png")
    print("Saved metrics_summary.png")
    
    print("\n" + "="*50)
    print("✅ DONE! Generated files:")
    print("  - snapshots.json (raw adjacency data)")
    print("  - metrics.json (all graph metrics)")
    print("  - changes.json (edge changes between snapshots)")
    print("  - metrics_summary.png (metrics over time)")
    print("  - heatmaps/ (directory with heatmap visualizations)")