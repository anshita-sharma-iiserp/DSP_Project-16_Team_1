# -*- coding: utf-8 -*-
"""Wikipedia Link Analysis Pipeline
   Processes GEXF snapshots, computes metrics, and exports results
"""

import networkx as nx
import json
import numpy as np
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.sparse import load_npz
import os
import time


#LOAD DATA


def load_gexf_snapshots(file_dict):
    """
    Load GEXF files into NetworkX graphs.

    Args:
        file_dict: dict like {"2024": "path/to/2024.gexf", "2025": "path/to/2025.gexf"}

    Returns:
        dict: {year: nx.DiGraph}
    """
    graphs = {}

    for year, filepath in file_dict.items():
        print(f"Loading {year}...")
        try:
            G = nx.read_gexf(filepath) #Directed graph
            if not nx.is_directed(G):
                G = G.to_directed()
            graphs[year] = G
            print(f"  ✓ {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"  ✗ Error loading {year}: {e}")

    return graphs



# PER-SNAPSHOT METRICS


def compute_basic_metrics(G, year):
    """Compute basic graph metrics"""
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G) if n_nodes > 1 else 0

    # Degree metrics
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())

    avg_in_degree = sum(in_degree.values()) / n_nodes if n_nodes > 0 else 0
    avg_out_degree = sum(out_degree.values()) / n_nodes if n_nodes > 0 else 0

    # Top 10
    top_in_degree = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:10]
    top_out_degree = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:10]

    # Connectivity components
    scc_count = nx.number_strongly_connected_components(G)
    wcc_count = nx.number_weakly_connected_components(G)

    # Largest SCC
    scc_list = list(nx.strongly_connected_components(G))
    largest_scc = max(scc_list, key=len) if scc_list else set()
    largest_scc_size = len(largest_scc)

    # Largest WCC
    wcc_list = list(nx.weakly_connected_components(G))
    largest_wcc = max(wcc_list, key=len) if wcc_list else set()
    largest_wcc_size = len(largest_wcc)

    return {
        "year": year,
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "density": round(density, 6),
        "avg_in_degree": round(avg_in_degree, 2),
        "avg_out_degree": round(avg_out_degree, 2),
        "scc_count": scc_count,
        "largest_scc_size": largest_scc_size,
        "wcc_count": wcc_count,
        "largest_wcc_size": largest_wcc_size,
        "top_in_degree": [(node, score) for node, score in top_in_degree],
        "top_out_degree": [(node, score) for node, score in top_out_degree],
        # Store raw degree dicts for later use
        "_in_degree": in_degree,
        "_out_degree": out_degree
    }


def compute_pagerank(G, year):
    """Compute PageRank centrality"""
    print(f"  Computing PageRank for {year}...")
    try:
        pagerank = nx.pagerank(G, max_iter=100, tol=1e-6)
        top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            f"pagerank_{year}": pagerank,
            f"top_pagerank_{year}": [(node, round(score, 6)) for node, score in top_pagerank]
        }
    except Exception as e:
        print(f"    PageRank failed: {e}")
        return {f"pagerank_{year}": {}, f"top_pagerank_{year}": []}


def compute_betweenness(G, year, k_samples=None):
    """Compute betweenness centrality (approximated for speed)"""
    n_nodes = G.number_of_nodes()

    # For large graphs, use sampling
    if k_samples is None:
        k_samples = min(100, n_nodes)

    print(f"  Computing Betweenness for {year} (k={k_samples})...")
    try:
        betweenness = nx.betweenness_centrality(G, k=k_samples, normalized=True)
        top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            f"betweenness_{year}": betweenness,
            f"top_betweenness_{year}": [(node, round(score, 6)) for node, score in top_betweenness]
        }
    except Exception as e:
        print(f"    Betweenness failed: {e}")
        return {f"betweenness_{year}": {}, f"top_betweenness_{year}": []}


def compute_clustering_and_paths(G, year):
    """Compute clustering coefficient and average path length"""
    print(f"  Computing clustering for {year}...")

    # Convert to undirected for clustering
    G_undirected = G.to_undirected()

    # Clustering coefficient
    try:
        avg_clustering = nx.average_clustering(G_undirected)
    except:
        avg_clustering = 0

    # Average path length (only if graph is connected)
    avg_path_length = None
    diameter = None

    try:
        if nx.is_weakly_connected(G):
            # Get largest component for path calculations
            largest_comp = max(nx.weakly_connected_components(G), key=len)
            G_largest = G.subgraph(largest_comp).to_undirected()

            if G_largest.number_of_nodes() > 1:
                avg_path_length = nx.average_shortest_path_length(G_largest)
                diameter = nx.diameter(G_largest)
    except Exception as e:
        print(f"    Path calculations failed: {e}")

    return {
        f"avg_clustering_{year}": round(avg_clustering, 4),
        f"avg_path_length_{year}": round(avg_path_length, 2) if avg_path_length else None,
        f"diameter_{year}": diameter
    }


#COMMUNITY DETECTION

def detect_communities(G, year):
    """Detect communities using Louvain algorithm"""
    print(f"  Detecting communities for {year}...")

    try:
        import community as community_louvain

        # Convert to undirected for community detection
        G_undirected = G.to_undirected()

        # Detect communities
        partition = community_louvain.best_partition(G_undirected)
        modularity = community_louvain.modularity(partition, G_undirected)

        # Count communities
        n_communities = len(set(partition.values()))

        # Get community sizes
        community_sizes = Counter(partition.values())
        largest_community_size = max(community_sizes.values())

        print(f"    Found {n_communities} communities, modularity: {modularity:.4f}")

        return {
            f"communities_{year}": partition,
            f"modularity_{year}": round(modularity, 4),
            f"n_communities_{year}": n_communities,
            f"largest_community_size_{year}": largest_community_size
        }
    except ImportError:
        print("    python-louvain not installed. Skipping community detection.")
        return {
            f"communities_{year}": {},
            f"modularity_{year}": None,
            f"n_communities_{year}": None,
            f"largest_community_size_{year}": None
        }
    except Exception as e:
        print(f"    Community detection failed: {e}")
        return {
            f"communities_{year}": {},
            f"modularity_{year}": None,
            f"n_communities_{year}": None,
            f"largest_community_size_{year}": None
        }


# ============================================
# STEP 4: TEMPORAL COMPARISON
# ============================================

def compare_temporal_changes(graphs, all_metrics):
    """
    Compare graphs across consecutive years.

    Returns:
        dict: Changes between snapshots
    """
    years = sorted(graphs.keys())
    changes = {}

    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]

        G_prev = graphs[prev_year]
        G_curr = graphs[curr_year]

        print(f"\nComparing {prev_year} → {curr_year}")

        # Nodes
        nodes_prev = set(G_prev.nodes())
        nodes_curr = set(G_curr.nodes())

        nodes_added = nodes_curr - nodes_prev
        nodes_removed = nodes_prev - nodes_curr

        # Edges
        edges_prev = set(G_prev.edges())
        edges_curr = set(G_curr.edges())

        edges_added = edges_curr - edges_prev
        edges_removed = edges_prev - edges_curr

        # Hub changes (top 10 out-degree)
        hubs_prev = set([node for node, _ in all_metrics[prev_year]["top_out_degree"][:5]])
        hubs_curr = set([node for node, _ in all_metrics[curr_year]["top_out_degree"][:5]])

        new_hubs = hubs_curr - hubs_prev
        lost_hubs = hubs_prev - hubs_curr

        changes[f"{prev_year}_to_{curr_year}"] = {
            "nodes_added": len(nodes_added),
            "nodes_removed": len(nodes_removed),
            "edges_added": len(edges_added),
            "edges_removed": len(edges_removed),
            "new_hubs": list(new_hubs)[:10],
            "lost_hubs": list(lost_hubs)[:10],
            "sample_added_edges": list(edges_added)[:10],
            "sample_removed_edges": list(edges_removed)[:10]
        }

        print(f"  Nodes: +{len(nodes_added)}, -{len(nodes_removed)}")
        print(f"  Edges: +{len(edges_added)}, -{len(edges_removed)}")
        print(f"  New hubs: {len(new_hubs)}, Lost hubs: {len(lost_hubs)}")

    return changes


def compute_structural_shifts(all_metrics, changes):
    """
    Identify structural shifts: fragmentation, consolidation, hub emergence.
    """
    years = sorted(all_metrics.keys())
    shifts = []

    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]

        prev = all_metrics[prev_year]
        curr = all_metrics[curr_year]

        # Fragmentation: increase in SCC count
        if curr["scc_count"] > prev["scc_count"] * 1.2:  # 20% increase
            shifts.append({
                "year": curr_year,
                "type": "fragmentation",
                "description": f"SCC count increased from {prev['scc_count']} to {curr['scc_count']}",
                "magnitude": curr["scc_count"] - prev["scc_count"]
            })

        # Consolidation: increase in largest SCC size
        if curr["largest_scc_size"] > prev["largest_scc_size"] * 1.2:
            shifts.append({
                "year": curr_year,
                "type": "consolidation",
                "description": f"Largest SCC grew from {prev['largest_scc_size']} to {curr['largest_scc_size']} nodes",
                "magnitude": curr["largest_scc_size"] - prev["largest_scc_size"]
            })

        # Density change
        if curr["density"] > prev["density"] * 1.1:
            shifts.append({
                "year": curr_year,
                "type": "densification",
                "description": f"Network density increased from {prev['density']:.6f} to {curr['density']:.6f}",
                "magnitude": curr["density"] - prev["density"]
            })

    return shifts


# ============================================
# STEP 5: ENRICH GEXF WITH METADATA
# ============================================

def enrich_gexf_with_metadata(graphs, all_metrics, output_dir="dashboard_data"):
    """
    Add computed metrics as node attributes to GEXF files.
    """
    os.makedirs(output_dir, exist_ok=True)

    for year, G in graphs.items():
        print(f"Enriching GEXF for {year}...")

        # Get metrics for this year
        metrics = all_metrics[year]

        # Add attributes to each node
        for node in G.nodes():
            # Basic info
            G.nodes[node]["title"] = node.split(" (")[0]  # Clean article title

            # Degree metrics
            G.nodes[node]["in_degree"] = metrics["_in_degree"].get(node, 0)
            G.nodes[node]["out_degree"] = metrics["_out_degree"].get(node, 0)

            # Centrality metrics
            pagerank_dict = metrics.get("_pagerank", {})
            G.nodes[node]["pagerank"] = round(pagerank_dict.get(node, 0), 6)

            betweenness_dict = metrics.get("_betweenness", {})
            G.nodes[node]["betweenness"] = round(betweenness_dict.get(node, 0), 6)

            # Community
            communities_dict = metrics.get("_communities", {})
            G.nodes[node]["community"] = communities_dict.get(node, -1)

            # Flags
            top_in = set([n for n, _ in metrics["top_in_degree"][:10]])
            top_out = set([n for n, _ in metrics["top_out_degree"][:10]])
            top_between = set([n for n, _ in metrics.get("top_betweenness", [])[:10]])

            G.nodes[node]["is_authority"] = node in top_in
            G.nodes[node]["is_hub"] = node in top_out
            G.nodes[node]["is_bottleneck"] = node in top_between

        # Save enriched GEXF
        output_path = f"{output_dir}/Covid-19_{year}_enriched.gexf"
        nx.write_gexf(G, output_path)
        print(f"  ✓ Saved to {output_path}")


# ============================================
# STEP 6: EXPORT JSON FOR DASHBOARD
# ============================================

def export_dashboard_json(graphs, all_metrics, changes, shifts, output_dir="dashboard_data"):
    """
    Export all metrics and data in JSON format for dashboard.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Clean up metrics for JSON (remove internal dicts)
    clean_metrics = {}
    for year, metrics in all_metrics.items():
        clean_metrics[year] = {
            k: v for k, v in metrics.items()
            if not k.startswith("_")  # Remove internal keys
        }

    # Prepare node metadata per snapshot
    node_metadata = {}
    for year, G in graphs.items():
        node_metadata[year] = {}
        for node in G.nodes():
            node_metadata[year][node] = {
                "title": G.nodes[node].get("title", node.split(" (")[0]),
                "in_degree": G.nodes[node].get("in_degree", 0),
                "out_degree": G.nodes[node].get("out_degree", 0),
                "pagerank": G.nodes[node].get("pagerank", 0),
                "betweenness": G.nodes[node].get("betweenness", 0),
                "community": G.nodes[node].get("community", -1),
                "is_hub": G.nodes[node].get("is_hub", False),
                "is_authority": G.nodes[node].get("is_authority", False),
                "is_bottleneck": G.nodes[node].get("is_bottleneck", False)
            }

    # Prepare edge lists
    edge_lists = {}
    for year, G in graphs.items():
        edge_lists[year] = list(G.edges())

    # Export everything
    dashboard_data = {
        "snapshots": list(graphs.keys()),
        "metrics": clean_metrics,
        "changes": changes,
        "structural_shifts": shifts,
        "node_metadata": node_metadata,
        "edge_lists": edge_lists
    }

    output_path = f"{output_dir}/dashboard_data.json"
    with open(output_path, "w") as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"✓ Dashboard JSON saved to {output_path}")

    # Also save metrics separately for reference
    with open("metrics_summary.json", "w") as f:
        json.dump(clean_metrics, f, indent=2)
    print(f"✓ Metrics summary saved to metrics_summary.json")


# ============================================
# STEP 7: VISUALIZATION
# ============================================

def plot_metrics_over_time(all_metrics, output_dir="dashboard_data"):
    """
    Create visualization of key metrics over time.
    """
    os.makedirs(output_dir, exist_ok=True)

    years = sorted(all_metrics.keys())

    # Extract metrics
    nodes = [all_metrics[y]["n_nodes"] for y in years]
    edges = [all_metrics[y]["n_edges"] for y in years]
    density = [all_metrics[y]["density"] for y in years]
    scc_size = [all_metrics[y]["largest_scc_size"] for y in years]
    modularity = [all_metrics[y].get("modularity", 0) for y in years]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Nodes
    axes[0, 0].plot(years, nodes, marker='o', linewidth=2)
    axes[0, 0].set_title('Nodes Over Time')
    axes[0, 0].set_ylabel('Count')
    axes[0, 0].grid(True, alpha=0.3)

    # Edges
    axes[0, 1].plot(years, edges, marker='o', linewidth=2, color='orange')
    axes[0, 1].set_title('Edges Over Time')
    axes[0, 1].set_ylabel('Count')
    axes[0, 1].grid(True, alpha=0.3)

    # Density
    axes[0, 2].plot(years, density, marker='o', linewidth=2, color='green')
    axes[0, 2].set_title('Density Over Time')
    axes[0, 2].set_ylabel('Density')
    axes[0, 2].grid(True, alpha=0.3)

    # Largest SCC
    axes[1, 0].plot(years, scc_size, marker='o', linewidth=2, color='red')
    axes[1, 0].set_title('Largest SCC Size Over Time')
    axes[1, 0].set_ylabel('Size')
    axes[1, 0].grid(True, alpha=0.3)

    # Modularity
    axes[1, 1].plot(years, modularity, marker='o', linewidth=2, color='purple')
    axes[1, 1].set_title('Modularity Over Time')
    axes[1, 1].set_ylabel('Modularity')
    axes[1, 1].grid(True, alpha=0.3)

    # Average in-degree
    avg_degree = [all_metrics[y]["avg_in_degree"] for y in years]
    axes[1, 2].plot(years, avg_degree, marker='o', linewidth=2, color='brown')
    axes[1, 2].set_title('Average In-Degree Over Time')
    axes[1, 2].set_ylabel('Degree')
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/metrics_timeline.png", dpi=150)
    plt.close()

    print(f"✓ Metrics timeline saved to {output_dir}/metrics_timeline.png")


def print_hub_evolution(all_metrics):
    """
    Print table showing hub evolution over time.
    """
    print("\n" + "="*60)
    print("HUB EVOLUTION (Top 5 Out-Degree)")
    print("="*60)

    for year, metrics in sorted(all_metrics.items()):
        print(f"\n{year}:")
        for i, (node, degree) in enumerate(metrics["top_out_degree"][:5], 1):
            title = node.split(" (")[0]
            print(f"  {i}. {title} (degree: {degree})")


# ============================================
# MAIN PIPELINE
# ============================================

def run_pipeline(file_dict, output_dir="dashboard_data"):
    """
    Main pipeline execution.

    Args:
        file_dict: dict like {"2024": "path/to/2024.gexf", "2025": "path/to/2025.gexf"}
        output_dir: Directory for output files
    """
    print("="*60)
    print("WIKIPEDIA LINK ANALYSIS PIPELINE")
    print("="*60)

    start_time = time.time()

    # Step 1: Load data
    print("\n[1/7] Loading GEXF files...")
    graphs = load_gexf_snapshots(file_dict)
    if not graphs:
        print("No graphs loaded. Exiting.")
        return

    # Step 2: Compute metrics per snapshot
    print("\n[2/7] Computing per-snapshot metrics...")
    all_metrics = {}

    for year, G in graphs.items():
        print(f"\nProcessing {year}:")

        # Basic metrics
        basic = compute_basic_metrics(G, year)

        # PageRank
        pr = compute_pagerank(G, year)
        basic["_pagerank"] = pr[f"pagerank_{year}"]
        basic[f"top_pagerank_{year}"] = pr[f"top_pagerank_{year}"]

        # Betweenness
        bt = compute_betweenness(G, year)
        basic["_betweenness"] = bt[f"betweenness_{year}"]
        basic[f"top_betweenness_{year}"] = bt[f"top_betweenness_{year}"]

        # Clustering and paths
        cp = compute_clustering_and_paths(G, year)
        basic.update(cp)

        # Communities
        comm = detect_communities(G, year)
        basic["_communities"] = comm[f"communities_{year}"]
        basic[f"modularity_{year}"] = comm[f"modularity_{year}"]
        basic[f"n_communities_{year}"] = comm[f"n_communities_{year}"]

        all_metrics[year] = basic

    # Step 3: Temporal comparison
    print("\n[3/7] Computing temporal changes...")
    changes = compare_temporal_changes(graphs, all_metrics)

    # Step 4: Detect structural shifts
    print("\n[4/7] Detecting structural shifts...")
    shifts = compute_structural_shifts(all_metrics, changes)

    if shifts:
        print("\nStructural shifts detected:")
        for shift in shifts:
            print(f"  {shift['year']}: {shift['type']} - {shift['description']}")
    else:
        print("  No significant structural shifts detected.")

    # Step 5: Enrich GEXF with metadata
    print("\n[5/7] Enriching GEXF files with metadata...")
    enrich_gexf_with_metadata(graphs, all_metrics, output_dir)

    # Step 6: Export JSON for dashboard
    print("\n[6/7] Exporting dashboard JSON...")
    export_dashboard_json(graphs, all_metrics, changes, shifts, output_dir)

    # Step 7: Generate visualizations
    print("\n[7/7] Generating visualizations...")
    plot_metrics_over_time(all_metrics, output_dir)
    print_hub_evolution(all_metrics)

    # Done
    elapsed = time.time() - start_time
    print(f"\n" + "="*60)
    print(f"✅ PIPELINE COMPLETE! Time elapsed: {elapsed:.2f} seconds")
    print(f"Output saved to: {output_dir}/")
    print("="*60)


# ============================================
# EXECUTION
# ============================================

if __name__ == "__main__":
    # Define your GEXF files here
    # Update paths to match your actual file locations


    gexf_files = {
        "2020": "COVID_19_2020.gexf",
        "2021": "COVID_19_2021.gexf",
        "2022": "COVID_19_2022.gexf",
        "2023": "COVID_19_2023.gexf",
        "2024": "COVID_19_2024.gexf",
        "2025": "COVID_19_2025.gexf",
        "2026": "COVID_19_2026.gexf",
    }
    # Run the pipeline
    run_pipeline(
        file_dict=gexf_files,
        output_dir="dashboard_data"
    )
