# Step 6: Interactive Dashboard
# Visualises the Wikipedia Link Network for COVID-19 Symptoms
# Run this script using: streamlit run step6_dashboard.py

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
Explore the core hubs, view the interactive network, and track how the knowledge structure evolved between 2020 and 2026.
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
    df_temporal = pd.read_csv(temporal_file) if temporal_file.exists() else None
    
    return df_metrics, df_temporal

@st.cache_resource
def load_graph(year):
    """Load the GraphML file for a specific year."""
    graph_file = GRAPHS_DIR / f'symptoms_graph_{year}.graphml'
    if not graph_file.exists():
        return None
    return nx.read_graphml(graph_file)

df_metrics, df_temporal = load_data()

# ==============================================================================
# TAB LAYOUT
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["📊 Network Hubs (2026)", "🕸️ Interactive Graph", "⏱️ Temporal Evolution"])

# --- TAB 1: Network Hubs ---
with tab1:
    st.header("Most Important Knowledge Hubs (PageRank)")
    if df_metrics is not None:
        st.markdown("Top 20 articles by PageRank, showing the most central hubs in the Wikipedia network.")
        
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
    st.markdown("Use the slider below to reduce the number of nodes and clear up the screen clutter. The graph simulation will pull connected nodes together and push unconnected ones apart.")
    
    colA, colB = st.columns([1, 2])
    with colA:
        num_nodes = st.slider("Number of Hubs to Display", min_value=10, max_value=300, value=75, step=5)
        node_dist = st.slider("Node Separation Distance", min_value=100, max_value=500, value=250, step=50)

    G = load_graph('2026')
    if G is not None and df_metrics is not None:
        # Filter graph for performance and clarity
        top_nodes = df_metrics.head(num_nodes)['article'].tolist()
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
    else:
        st.warning("GraphML files not found. Did you run step4_temporal.py?")


# --- TAB 3: Temporal Evolution ---
with tab3:
    st.header("Temporal Shifts: 2020 vs 2026")
    if df_temporal is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Articles (2020)", "1,434")
        col2.metric("Total Articles (2026)", "2,933", "+1,499", delta_color="normal")
        col3.metric("Total Links Created", "10,149", "+6,713", delta_color="normal")
        
        st.markdown("### Top Surging Articles (Largest PageRank Shift)")
        st.markdown("These articles became drastically more central to the Wikipedia knowledge network between 2020 and 2026.")
        
        # Sort by shift
        surging = df_temporal.sort_values('shift', ascending=False).head(15)
        
        # Plot
        fig2 = px.bar(surging, x='shift', y='Unnamed: 0', orientation='h', 
                      title="Rise in Importance (2020 vs 2026)",
                      labels={'Unnamed: 0': 'Article Name', 'shift': 'PageRank Growth'},
                      color='shift', color_continuous_scale='Inferno')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("temporal_shifts.csv not found.")

