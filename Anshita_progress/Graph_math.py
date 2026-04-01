# -*- coding: utf-8 -*-
"""Wikipedia Link Analysis Pipeline - Analysis Only
   Loads GEXF snapshots, computes graph-level metrics, generates plots
   
"""

import networkx as nx
import json
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
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
            G = nx.read_gexf(filepath)
            # Ensure it's directed (Wikipedia links are directed)
            if not nx.is_directed(G):
                G = G.to_directed()
            graphs[year] = G
            print(f"  ✓ {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        except Exception as e:
            print(f"  ✗ Error loading {year}: {e}")
    
    return graphs



#GRAPH-LEVEL METRICS


def compute_graph_metrics(G, year):
    """
    Compute graph-level metrics only.
    """
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G) if n_nodes > 1 else 0
    
    # Degree metrics (aggregated)
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())
    
    avg_in_degree = sum(in_degree.values()) / n_nodes if n_nodes > 0 else 0
    avg_out_degree = sum(out_degree.values()) / n_nodes if n_nodes > 0 else 0
    
    # Top 10 hubs (for hub evolution analysis)
    top_out_degree = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:10]
    top_in_degree = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:10]
    
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
    
    # Clustering coefficient (graph-level)
    try:
        G_undirected = G.to_undirected()
        avg_clustering = nx.average_clustering(G_undirected)
    except:
        avg_clustering = 0
    
    # Average path length and diameter (only if graph is connected enough)
    avg_path_length = None
    diameter = None
    
    try:
        if nx.is_weakly_connected(G):
            largest_comp = max(nx.weakly_connected_components(G), key=len)
            G_largest = G.subgraph(largest_comp).to_undirected()
            if G_largest.number_of_nodes() > 1:
                avg_path_length = nx.average_shortest_path_length(G_largest)
                diameter = nx.diameter(G_largest)
    except Exception as e:
        pass
    
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
        "avg_clustering": round(avg_clustering, 4),
        "avg_path_length": round(avg_path_length, 2) if avg_path_length else None,
        "diameter": diameter,
        "top_hubs": [(node.split(" (")[0], degree) for node, degree in top_out_degree],
        "top_authorities": [(node.split(" (")[0], degree) for node, degree in top_in_degree]
    }



# TEMPORAL COMPARISON


def compare_temporal_changes(graphs, all_metrics):
    """
    Compare graphs across consecutive years.
    Returns dict of changes between snapshots.
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
        
        # Hub changes (top 5 hubs)
        hubs_prev = set([node for node, _ in all_metrics[prev_year]["top_hubs"][:5]])
        hubs_curr = set([node for node, _ in all_metrics[curr_year]["top_hubs"][:5]])
        
        new_hubs = hubs_curr - hubs_prev
        lost_hubs = hubs_prev - hubs_curr
        
        changes[f"{prev_year}_to_{curr_year}"] = {
            "nodes_added": len(nodes_added),
            "nodes_removed": len(nodes_removed),
            "edges_added": len(edges_added),
            "edges_removed": len(edges_removed),
            "new_hubs": list(new_hubs)[:10],
            "lost_hubs": list(lost_hubs)[:10]
        }
        
        print(f"  Nodes: +{len(nodes_added)}, -{len(nodes_removed)}")
        print(f"  Edges: +{len(edges_added)}, -{len(edges_removed)}")
        print(f"  New hubs: {len(new_hubs)}, Lost hubs: {len(lost_hubs)}")
    
    return changes


def compute_structural_shifts(all_metrics, changes):
    """
    Identify structural shifts: fragmentation, consolidation, densification.
    """
    years = sorted(all_metrics.keys())
    shifts = []
    
    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]
        
        prev = all_metrics[prev_year]
        curr = all_metrics[curr_year]
        
        # Fragmentation: increase in SCC count
        if curr["scc_count"] > prev["scc_count"] * 1.2:
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
        
        # Densification: density increase
        if curr["density"] > prev["density"] * 1.1:
            shifts.append({
                "year": curr_year,
                "type": "densification",
                "description": f"Network density increased from {prev['density']:.6f} to {curr['density']:.6f}",
                "magnitude": curr["density"] - prev["density"]
            })
    
    return shifts



# STEP 4: VISUALIZATIONS (Your main output)


def plot_growth_trends(all_metrics, output_dir="analysis_plots"):
    """
    Plot 1: Growth trends - Nodes and edges over time
    """
    os.makedirs(output_dir, exist_ok=True)
    
    years = sorted(all_metrics.keys())
    nodes = [all_metrics[y]["n_nodes"] for y in years]
    edges = [all_metrics[y]["n_edges"] for y in years]
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Nodes on primary y-axis
    ax1.plot(years, nodes, marker='o', linewidth=2, color='blue', label='Nodes')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Number of Nodes', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, alpha=0.3)
    
    # Edges on secondary y-axis
    ax2 = ax1.twinx()
    ax2.plot(years, edges, marker='s', linewidth=2, color='orange', label='Edges')
    ax2.set_ylabel('Number of Edges', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    
    plt.title('Knowledge Network Growth Over Time')
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/growth_trends.png", dpi=150)
    plt.close()
    print(f"Saved: {output_dir}/growth_trends.png")


def plot_density_and_connectivity(all_metrics, output_dir="analysis_plots"):
    """
    Plot 2: Density and connectivity metrics over time
    """
    os.makedirs(output_dir, exist_ok=True)
    
    years = sorted(all_metrics.keys())
    density = [all_metrics[y]["density"] for y in years]
    scc_size = [all_metrics[y]["largest_scc_size"] for y in years]
    avg_degree = [all_metrics[y]["avg_out_degree"] for y in years]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Density
    axes[0].plot(years, density, marker='o', linewidth=2, color='green')
    axes[0].set_title('Network Density')
    axes[0].set_xlabel('Year')
    axes[0].set_ylabel('Density')
    axes[0].grid(True, alpha=0.3)
    
    # Largest SCC
    axes[1].plot(years, scc_size, marker='o', linewidth=2, color='red')
    axes[1].set_title('Largest Strongly Connected Component')
    axes[1].set_xlabel('Year')
    axes[1].set_ylabel('Size')
    axes[1].grid(True, alpha=0.3)
    
    # Average Degree
    axes[2].plot(years, avg_degree, marker='o', linewidth=2, color='purple')
    axes[2].set_title('Average Out-Degree')
    axes[2].set_xlabel('Year')
    axes[2].set_ylabel('Degree')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/density_connectivity.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/density_connectivity.png")


def plot_hub_evolution(all_metrics, output_dir="analysis_plots"):
    """
    Plot 3: Hub evolution - Top hubs per year
    """
    os.makedirs(output_dir, exist_ok=True)
    
    years = sorted(all_metrics.keys())
    
    # Create a figure with subplots for each year
    fig, axes = plt.subplots(1, len(years), figsize=(6 * len(years), 6))
    if len(years) == 1:
        axes = [axes]
    
    for idx, year in enumerate(years):
        hubs = all_metrics[year]["top_hubs"][:5]
        hub_names = [h[0][:30] + "..." if len(h[0]) > 30 else h[0] for h in hubs]
        hub_degrees = [h[1] for h in hubs]
        
        axes[idx].barh(hub_names, hub_degrees, color='steelblue')
        axes[idx].set_title(f'Top Hubs - {year}')
        axes[idx].set_xlabel('Out-Degree')
        axes[idx].invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/hub_evolution.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/hub_evolution.png")


def plot_structural_shifts(all_metrics, shifts, output_dir="analysis_plots"):
    """
    Plot 4: Highlight structural shifts
    """
    os.makedirs(output_dir, exist_ok=True)
    
    years = sorted(all_metrics.keys())
    
    # Metrics to track for shifts
    scc_counts = [all_metrics[y]["scc_count"] for y in years]
    scc_sizes = [all_metrics[y]["largest_scc_size"] for y in years]
    densities = [all_metrics[y]["density"] for y in years]
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # SCC Count
    axes[0].plot(years, scc_counts, marker='o', linewidth=2, color='brown')
    axes[0].set_title('Number of Strongly Connected Components')
    axes[0].set_ylabel('Count')
    axes[0].grid(True, alpha=0.3)
    
    # Highlight shifts on SCC count
    for shift in shifts:
        if shift['type'] == 'fragmentation':
            year_idx = years.index(shift['year'])
            axes[0].axvline(x=shift['year'], color='red', linestyle='--', alpha=0.7)
            axes[0].text(shift['year'], scc_counts[year_idx] + 1, '↑ Fragmentation', 
                        ha='center', color='red', fontsize=9)
    
    # Largest SCC Size
    axes[1].plot(years, scc_sizes, marker='o', linewidth=2, color='green')
    axes[1].set_title('Largest SCC Size')
    axes[1].set_ylabel('Size')
    axes[1].grid(True, alpha=0.3)
    
    for shift in shifts:
        if shift['type'] == 'consolidation':
            year_idx = years.index(shift['year'])
            axes[1].axvline(x=shift['year'], color='green', linestyle='--', alpha=0.7)
            axes[1].text(shift['year'], scc_sizes[year_idx] + 5, '↑ Consolidation', 
                        ha='center', color='green', fontsize=9)
    
    # Density
    axes[2].plot(years, densities, marker='o', linewidth=2, color='blue')
    axes[2].set_title('Network Density')
    axes[2].set_xlabel('Year')
    axes[2].set_ylabel('Density')
    axes[2].grid(True, alpha=0.3)
    
    for shift in shifts:
        if shift['type'] == 'densification':
            year_idx = years.index(shift['year'])
            axes[2].axvline(x=shift['year'], color='blue', linestyle='--', alpha=0.7)
            axes[2].text(shift['year'], densities[year_idx] + 0.001, '↑ Densification', 
                        ha='center', color='blue', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/structural_shifts.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/structural_shifts.png")


def plot_summary_dashboard(all_metrics, output_dir="analysis_plots"):
    """
    Plot 5: Summary dashboard with all key metrics
    """
    os.makedirs(output_dir, exist_ok=True)
    
    years = sorted(all_metrics.keys())
    
    # Extract all metrics
    nodes = [all_metrics[y]["n_nodes"] for y in years]
    edges = [all_metrics[y]["n_edges"] for y in years]
    density = [all_metrics[y]["density"] for y in years]
    scc_size = [all_metrics[y]["largest_scc_size"] for y in years]
    avg_degree = [all_metrics[y]["avg_out_degree"] for y in years]
    clustering = [all_metrics[y]["avg_clustering"] for y in years]
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    metrics_list = [
        (nodes, 'Nodes', 'blue', axes[0, 0]),
        (edges, 'Edges', 'orange', axes[0, 1]),
        (density, 'Density', 'green', axes[0, 2]),
        (scc_size, 'Largest SCC', 'red', axes[1, 0]),
        (avg_degree, 'Avg Out-Degree', 'purple', axes[1, 1]),
        (clustering, 'Avg Clustering', 'brown', axes[1, 2])
    ]
    
    for data, title, color, ax in metrics_list:
        ax.plot(years, data, marker='o', linewidth=2, color=color)
        ax.set_title(title)
        ax.set_xlabel('Year')
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for x, y in zip(years, data):
            ax.annotate(f'{y:.4f}' if isinstance(y, float) and y < 1 else str(int(y)),
                       (x, y), textcoords="offset points", xytext=(0, 10), ha='center')
    
    plt.suptitle('Wikipedia Knowledge Network Analysis - Summary Dashboard', fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/summary_dashboard.png", dpi=150)
    plt.close()
    print(f"✓ Saved: {output_dir}/summary_dashboard.png")



#EXPORT METRICS 


def export_metrics_json(all_metrics, changes, shifts, output_dir="analysis_plots"):
    """
    Export all metrics as JSON for reference.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean metrics (remove any internal fields if present)
    clean_metrics = {}
    for year, metrics in all_metrics.items():
        clean_metrics[year] = {k: v for k, v in metrics.items() 
                                if not k.startswith("_")}
    
    output = {
        "metrics": clean_metrics,
        "changes": changes,
        "structural_shifts": shifts
    }
    
    with open(f"{output_dir}/analysis_metrics.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved: {output_dir}/analysis_metrics.json")


def print_summary_table(all_metrics):
    """
    Print a formatted summary table of all metrics.
    """
    print("\n" + "="*80)
    print("SUMMARY TABLE: Graph Metrics Over Time")
    print("="*80)
    
    # Header
    print(f"{'Year':<6} {'Nodes':<8} {'Edges':<8} {'Density':<10} {'Avg Degree':<12} {'Largest SCC':<12} {'SCC Count':<10}")
    print("-"*80)
    
    for year, metrics in sorted(all_metrics.items()):
        print(f"{year:<6} {metrics['n_nodes']:<8} {metrics['n_edges']:<8} "
              f"{metrics['density']:<10.6f} {metrics['avg_out_degree']:<12.2f} "
              f"{metrics['largest_scc_size']:<12} {metrics['scc_count']:<10}")
    
    print("="*80)


def print_hub_evolution(all_metrics):
    """
    Print hub evolution across years.
    """
    print("\n" + "="*60)
    print("HUB EVOLUTION (Top 5 Out-Degree)")
    print("="*60)
    
    for year, metrics in sorted(all_metrics.items()):
        print(f"\n{year}:")
        for i, (hub_name, degree) in enumerate(metrics["top_hubs"][:5], 1):
            print(f"  {i}. {hub_name} (degree: {degree})")



# MAIN PIPELINE


def run_analysis_pipeline(file_dict, output_dir="analysis_plots"):
    """
    Main analysis pipeline - loads graphs, computes metrics, generates plots.
    
    Args:
        file_dict: dict like {"2024": "path/to/2024.gexf", "2025": "path/to/2025.gexf"}
        output_dir: Directory for output files
    """
    print("="*60)
    print("WIKIPEDIA LINK ANALYSIS - ANALYSIS PIPELINE")
    print("Analysis Only")
    print("="*60)
    
    start_time = time.time()
    
    # Step 1: Load data
    print("\n[1/5] Loading GEXF files...")
    graphs = load_gexf_snapshots(file_dict)
    if not graphs:
        print("No graphs loaded. Exiting.")
        return
    
    # Step 2: Compute graph-level metrics
    print("\n[2/5] Computing graph-level metrics...")
    all_metrics = {}
    
    for year, G in graphs.items():
        print(f"  Processing {year}...")
        all_metrics[year] = compute_graph_metrics(G, year)
    
    # Step 3: Temporal comparison
    print("\n[3/5] Computing temporal changes...")
    changes = compare_temporal_changes(graphs, all_metrics)
    
    # Step 4: Detect structural shifts
    print("\n[4/5] Detecting structural shifts...")
    shifts = compute_structural_shifts(all_metrics, changes)
    
    if shifts:
        print("\n  Structural shifts detected:")
        for shift in shifts:
            print(f"    {shift['year']}: {shift['type']} - {shift['description']}")
    else:
        print("  No significant structural shifts detected.")
    
    # Step 5: Generate visualizations
    print("\n[5/5] Generating visualizations...")
    plot_growth_trends(all_metrics, output_dir)
    plot_density_and_connectivity(all_metrics, output_dir)
    plot_hub_evolution(all_metrics, output_dir)
    plot_structural_shifts(all_metrics, shifts, output_dir)
    plot_summary_dashboard(all_metrics, output_dir)
    
    # Export metrics
    export_metrics_json(all_metrics, changes, shifts, output_dir)
    
    # Print summaries
    print_summary_table(all_metrics)
    print_hub_evolution(all_metrics)
    
    # Done
    elapsed = time.time() - start_time
    print(f"\n" + "="*60)
    print(f"✅ ANALYSIS COMPLETE! Time elapsed: {elapsed:.2f} seconds")
    print(f"Output saved to: {output_dir}/")
    print("="*60)



# EXECUTION


if __name__ == "__main__":
    # Define your GEXF files here
    gexf_files = {
        "2024": "nidhi_progress/wiki_graph_2024.gexf",
        "2025": "nidhi_progress/wiki_graph_2025.gexf",
        "2026": "nidhi_progress/wiki_graph_2026.gexf"
    }
    
    # Run the analysis pipeline
    run_analysis_pipeline(
        file_dict=gexf_files,
        output_dir="analysis_plots"
    )