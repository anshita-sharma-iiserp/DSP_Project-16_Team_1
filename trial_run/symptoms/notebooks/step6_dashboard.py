import streamlit as st
import pandas as pd
import networkx as nx
import plotly.express as px
from pyvis.network import Network
import os
from pathlib import Path

# Streamlit App Config
st.set_page_config(page_title="Wikipedia Knowledge Flow", layout="wide")
st.title("🌐 COVID-19 Symptoms: Wikipedia Knowledge Structure")
st.markdown("""
This dashboard visualises the Wikipedia internal link graph for articles related to **Symptoms of COVID-19**.
Explore the core hubs, view the interactive network, and track how the knowledge structure evolved across **4 distinct phases**.
""")

# Setup Paths
DATA_DIR = Path('../data')
GRAPHS_DIR = Path('../graphs')

@st.cache_data
def load_data():
    """Load pre-computed metrics and temporal shifts."""
    metrics_file = DATA_DIR / 'network_metrics.csv'
    temporal_file = DATA_DIR / 'temporal_shifts.csv'
    
    df_metrics = pd.read_csv(metrics_file) if metrics_file.exists() else None
    
    # We load temporal shifts with article as index for easy lookups
    df_temporal = None
    if temporal_file.exists():
        df_temporal = pd.read_csv(temporal_file, index_col=0)
    
    return df_metrics, df_temporal

@st.cache_resource
def load_graph(phase):
    """Load the GraphML file for a specific phase."""
    graph_file = GRAPHS_DIR / f'symptoms_graph_{phase}.graphml'
    if not graph_file.exists():
        return None
    return nx.read_graphml(graph_file)

df_metrics, df_temporal = load_data()

# ==============================================================================
# TAB LAYOUT
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Network Hubs (Latest)", "🕸️ Interactive Graph", "⏱️ 4-Phase Temporal Evolution", "📖 Methodology & Limitations"])

# --- TAB 1: Network Hubs ---
with tab1:
    st.header("Most Important Knowledge Hubs (PageRank)")
    if df_metrics is not None:
        st.markdown("Top 20 articles by PageRank, showing the most central hubs in the current network.")
        
        # Plotly Bar Chart
        top_20 = df_metrics.head(20).sort_values(by='pagerank', ascending=True)
        fig = px.bar(top_20, x='pagerank', y='article', orientation='h', 
                     title="Top 20 Hubs by PageRank (Current Network)",
                     color='pagerank', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Raw Metrics Data")
        st.dataframe(df_metrics.head(100), use_container_width=True)
    else:
        st.warning("network_metrics.csv not found. Did you run step5_metrics.py?")


# --- TAB 2: Interactive Graph ---
with tab2:
    st.header("Interactive Network Visualisation")
    st.markdown("Use the timeline slider to view the network topology at 4 distinct phases of the pandemic.")
    
    colA, colB = st.columns([1, 2])
    with colA:
        num_nodes = st.slider("Number of Hubs to Display", min_value=10, max_value=300, value=75, step=5)
        node_dist = st.slider("Node Separation Distance", min_value=100, max_value=500, value=250, step=50)

    # 4-Phase Timeline Selection
    st.markdown("### ⏳ Temporal Network Slider")
    phase_options = {
        '2020_03': 'March 2020: The "Classic Triad"',
        '2020_07': 'July 2020: Sensory Discovery',
        '2021_03': 'March 2021: Chronic Realization',
        '2022_01': 'Jan 2022: Omicron Shift'
    }
    
    selected_phase = st.select_slider(
        "Select Time Period",
        options=list(phase_options.keys()),
        format_func=lambda x: phase_options[x],
        value='2022_01'
    )

    G = load_graph(selected_phase)
    if G is not None and df_temporal is not None:
        try:
            # Rank nodes by PageRank in the selected selected_phase
            top_articles = df_temporal.sort_values(by=f'pr_{selected_phase}', ascending=False).head(num_nodes).index.tolist()
            
            # Nodes may not exist in earlier graphs, so safely take intersection
            top_nodes = [n for n in top_articles if n in G.nodes()]
            sub_G = G.subgraph(top_nodes)
            
            # Initialize Pyvis
            net = Network(height="650px", width="100%", bgcolor="#1a1a1a", font_color="white", directed=True)
            
            # Add nodes with sizing based on degree
            for node in sub_G.nodes():
                degree = sub_G.degree(node)
                # Make the nodes slightly transparent so you can see overlapping links
                net.add_node(node, label=node, title=f"{node} (Degree: {degree})", size=min(degree * 1.5, 40), color="rgba(97, 175, 239, 0.9)")
                
            # Add edges (make them semi-transparent to reduce visual noise)
            for source, target in sub_G.edges():
                net.add_edge(source, target, color="rgba(150, 150, 150, 0.3)")
                
            # Dramatic physics customisation to stop overlapping!
            net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=node_dist, spring_strength=0.04, damping=0.09, overlap=0)
            
            # Save and display
            html_path = "network_map.html"
            net.save_graph(html_path)
            
            # Read HTML directly into Streamlit
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=620)
        except Exception as e:
            st.error(f"Error filtering nodes for {selected_phase}. Re-run step 4. {e}")
    else:
        st.warning("GraphML files or temporal_shifts.csv not found. Please run step4_temporal.py.")


# --- TAB 3: Temporal Evolution ---
with tab3:
    st.header("Temporal Shifts: 4-Phase Evolution")
    if df_temporal is not None:
        st.markdown("### Top Surging Articles (March 2020 ➔ January 2022)")
        st.markdown("These articles became drastically more central to the Wikipedia knowledge network across the 4 phases.")
        
        # Sort by overall shift
        surging = df_temporal.sort_values('shift_overall', ascending=False).head(15).reset_index()
        
        # Plot
        fig2 = px.bar(surging, x='shift_overall', y=surging.columns[0], orientation='h', 
                      title="Rise in Importance (Full Pandemic Timeline)",
                      labels={surging.columns[0]: 'Article Name', 'shift_overall': 'Overall PageRank Growth'},
                      color='shift_overall', color_continuous_scale='Inferno')
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("Sequential Shifts Data")
        st.dataframe(df_temporal[['shift_P1_to_P2', 'shift_P2_to_P3', 'shift_P3_to_P4', 'shift_overall']].head(20), use_container_width=True)
    else:
        st.warning("temporal_shifts.csv not found.")

# --- TAB 4: Methodology & Limitations ---
with tab4:
    st.header("Methodology & Limitations")
    st.markdown("""
### 1. Graph Storage Strategies: Adjacency Lists vs. Edge Tables
During the data ingestion phase, we employed two distinct graph storage formats, each suited for different use-cases:

*   **Edge Tables (`symptoms_edgelist.csv`):** We saved the network as a flat CSV file where each row represents a directed link `(Source, Target)`. 
    *   *Pros:* Highly scalable, human-readable, and serves as an excellent intermediate format for bulk inserting into databases.
    *   *Cons:* Inefficient for complex graph traversal algorithms. To find all neighbors of a node, a full sequential scan is required.
*   **GraphML (`symptoms_graph.graphml`):** We serialized the in-memory NetworkX objects into GraphML XML structures.
    *   *Pros:* Preserves graph-level attributes, node metadata, and edge directions perfectly. It allows us to instantly load the mathematical topology into Memory (RAM) for complex multi-hop algorithms like PageRank or Barnes-Hut physics simulations.
    *   *Cons:* XML overhead makes file sizes large. Loading the entire graph into memory limits the maximum size to the available RAM.

### 2. Data & Modelling Limitations
While this dashboard successfully tracks structural shifts in Wikipedia's consensus on COVID-19 Symptoms, the methodology carries innate data limitations:

*   **API Snapshot Limits (The Granularity Trade-off):** Fetching historical revisions via the Wikimedia API (`prop=revisions`) requires retrieving the raw wikitext and manually parsing it with Regular Expressions. Fetching every month for 4,000 articles equals ~300,000 API requests. To prevent rate-limiting and ensure reproducibility, we limited our temporal analysis to 4 distinct "Phases" across 386 core articles. This provides excellent macro-level narrative but loses micro-level granularity (we don't see the exact day a node surged).
*   **Redirect Handling & Semantics:** Wikipedia heavily utilizes `#REDIRECT` pages (e.g., "Loss of smell" -> "Anosmia"). While our scripts tracked major article names, a completely unified semantic analysis would require resolving every redirect link recursively. Additionally, our regex link extraction treats all links identically, ignoring the semantic context (whether an article hyperlinks to a symptom because it *causes* it, or because it is a *misconception*).
*   **Incomplete Ground Truth:** Wikipedia is a secondary source written by volunteers. The "structural shifts" observed reflect when the *public/editors* integrated medical concepts, which usually trails true clinical discovery timelines by weeks or months.
""")
