# -*- coding: utf-8 -*-
# the above is used to read special characters
"""
Dashboard for Wikipedia knowledge flow and link structure
"""

# 1) make sure take_in_gexf.py, dashboard_code.py and all the gexf files are in the same directory
# 2) run the take_in_gexf.py using python take_in_gexf.py
# 3) run the dashboard_code.py using streamlit run dashboard_code.py

import streamlit as st     # to build the UI

# page configuration
st.set_page_config(
    page_title="Wikipedia Knowledge Flow (Covid-19)",
    layout="wide",
    initial_sidebar_state="expanded"
)

import json
import os
import networkx as nx     # to build graphs
import plotly.graph_objects as go     # go is graph objects
import plotly.express as px
import pandas as pd

# ─────────────────────────────────────────────

# to load the data
@st.cache_resource     # saves objects created
def load_dashboard_data(
    json_path='dashboard_data/dashboard_data.json',
    gexf_dir = 'dashboard_data'
):
    if not os.path.exists(json_path):
        return None, None

    with open(json_path, 'r') as f:
       data = json.load(f)

    graphs = {}
    for year in data['snapshots']:
        path = os.path.join(gexf_dir, f'Covid-19_{year}_enriched.gexf')
        if os.path.exists(path):
            G = nx.read_gexf(path)
            if not nx.is_directed(G):
                G = G.to_directed()
            graphs[year] = G
        else:
            st.warning(f'Enriched GEXF not found: {path}')

    return data, graphs

def build_metrics_df(data, year, sort_by='pagerank'):

    node_meta = data['node_metadata'][year]
    rows = []
    for node, attributes in node_meta.items():
        rows.append({
            'article':  attributes.get('title', node),
            'pagerank':  attributes.get('pagerank', 0),
            'in_degree':  attributes.get('in_degree', 0),
            'out_degree':  attributes.get('out_degree', 0),
            'betweenness':  attributes.get('betweenness', 0),
            'community': attributes.get('community', -1),
            'is_hub': attributes.get('is_hub', False),
            'is_authority': attributes.get('is_authority', False),
            'is_bottleneck':  attributes.get('is_bottleneck', False),
        })
    df = pd.DataFrame(rows).sort_values(sort_by, ascending=False).reset_index(drop=True)
    return df


# ─────────────────────────────────────────────

# network visualisation
def build_networks(G, metrics_df, top_n=40):

  # defining important data
  top_nodes=metrics_df.head(top_n)["article"].tolist()
  subgraph=G.subgraph(top_nodes)
  pos = nx.spring_layout(subgraph, k=0.8, seed=42, iterations=100)     # spring layout allows for node layout based on connectivity, k controls ideal dist between nodes, seed allows for same graph each time
  pagerank = dict(zip(metrics_df["article"], metrics_df["pagerank"]))
  in_degree = dict(zip(metrics_df["article"], metrics_df["in_degree"]))

  # edges
  edge_x = []     # can be considered the 'coordinate' of x
  edge_y = []
  for u, v in subgraph.edges():
    x1, y1 = pos[u]
    x2, y2 = pos[v]
    edge_x += [x1, x2, None]     # 'none' allows for connection of only x1 and x2
    edge_y += [y1, y2, None]

  # the edge coordinates are joint by a line
  edge_scatter = go.Scatter(
      x=edge_x, y=edge_y,
      mode="lines",
      line=dict(width=0.6, color="#30363d"),
      hoverinfo="none"
  )


  # nodes
  nodes = subgraph.nodes()
  node_x = [pos[n][0] for n in nodes]
  node_y = [pos[n][1] for n in nodes]
  node_sizes = [max(8, pagerank.get(n, 0)*3000) for n in nodes]     # size is a scaled up measure of page rank, with a least count
  node_colors = [in_degree.get(n, 0) for n in nodes]
  node_text = [
      f"<b>{n}</b><br>Pagerank: {pagerank.get(n, 0):.4f}<br>In-degree: {in_degree.get(n, 0)}"     # <b> is to make bold
      for n in nodes
  ]

  node_scatter = go.Scatter(
      x=node_x, y=node_y,
      mode="markers+text",
      hoverinfo="text",
      hovertext=node_text,
      text=[n if pagerank.get(n, 0) > metrics_df["pagerank"].quantile(0.75) else "" for n in subgraph.nodes()],     # top 25th percentile's text is seen
      textposition="top center",
      textfont=dict(size=8, color="#e6edf3"),
      marker=dict(
          size=node_sizes,
          color=node_colors,
          colorscale="YlOrRd",
          showscale=True,
          colorbar=dict(
              title="In-degree",
              bgcolor="#161b22",
              bordercolor="#30363d"
          ),
          line=dict(width=1, color="#30363d")
      )
  )

  fig = go.Figure(
      data=[edge_scatter, node_scatter],
      layout=go.Layout(
          paper_bgcolor="#0d1117",
          plot_bgcolor="#0d1117",
          showlegend=False,
          hovermode="closest",
          margin=dict(b=0, l=0, r=0, t=0),
          xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
          height=550
      )
  )
  return fig


# ─────────────────────────────────────────────

# centrality over time chart
def build_centrality_chart(data, metric="pagerank", top_n=10):

    all_data = []

    for year in data['snapshots']:
        df = build_metrics_df(data, year, sort_by=metric)
        top = df.head(top_n)[["article", metric]].copy()     # copy allows one to make actually make a ___ rather than just view
        top["year"] = year
        all_data.append(top)

    combined = pd.concat(all_data)     # concat appends

    fig = px.line(
        combined,
        x="year", y=metric,
        color="article",
        markers=True,
        template="plotly_dark",
        labels={'year': 'Year', metric:metric.replace("_", " ").title()},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=9))
    return fig


# ─────────────────────────────────────────────

def build_changes_chart(change_records):

    periods = [r["period"] for r in change_records]
    added = [r["edges_added"] for r in change_records]
    removed = [-r["edges_removed"] for r in change_records]

    fig = go.Figure()
    fig.add_trace(go.Bar(     # creates bar chart
        name="Added", x=periods, y=added,
        marker_color="#3fb950", text=added, textposition="outside",
        textfont=dict(color="#3fb950")
    ))
    fig.add_trace(go.Bar(
        name="Removed", x=periods, y=removed,
        marker_color="#f85149", text=[abs(r) for r in removed], textposition="outside",
        textfont=dict(color="#f85149")
    ))
    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        xaxis = dict(gridcolor="#30363d", color="#8b949e"),     # metrics saved as dictionaries
        yaxis=dict(gridcolor="#30363d", color="#8b949e", title="Number of Links"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d"),     # plotly needs configurations in dictionaries
        height=350,
        margin=dict(t=20)
    )

    return fig

# ─────────────────────────────────────────────

# structural shifts chart

def build_structural_shifts_chart(data):

    shifts = data.get('structural_shifts', [])
    if not shifts:
        return None

    shift_df = pd.DataFrame(shifts)
    fig = px.bar(
        shift_df,
        x='year', y='magnitude',
        color='type',
        hover_data=['description'],
        color_discrete_map={
            'fragmentation': '#f85149',
            'consolidation': '#3fb950',
            'densification': '#58a6ff'
        },
        labels={'magnitude': "Magnitude", 'year': 'Year', 'type': "Shift type"}
    )
    fig.update_layout(
        paper_bgcolor='#0d1117',
        plot_bgcolor='#161b22',
        legend=dict(bgcolor='#161b22', bordercolor='#30363d'),
        height=300,
        margin=dict(t=20)
    )
    return fig

# ─────────────────────────────────────────────

# community chart
def build_community_chart(data):

    rows=[]
    for year in data['snapshots']:
        m = data['metrics'][year]
        n_comm_key = f'n_communities_{year}'
        mod_key = f'modularity_{year}'
        rows.append({
            'year': year,
            'communities': m.get(n_comm_key, 0) or 0,
            'modularity': m.get(mod_key, 0) or 0,
        })
    df = pd.DataFrame(rows)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['year'], y=df['communities'],
        name='Communities', marker_color='#58a6ff',
        text=df['communities'], textposition='outside'
    ))
    fig.update_layout(
        paper_bgcolor='#0d1117',
        plot_bgcolor='#161b22',
        xaxis=dict(gridcolor='#30363d', color='#8b949e'),
        yaxis=dict(gridcolor='#30363d', color='#8b949e', title='Number of Communities'),
        legend=dict(bgcolor='#161b22', bordercolor='#30363d'),
        height=300,
        margin=dict(t=20)
    )
    return fig

# ─────────────────────────────────────────────

# to create the UI
def main():
  # header
  # st.markdown is like a print statement, below is in html script for customized markdown
  st.markdown("""
  <div style='padding: 20px 0 0'>
      <h1 style='font-family: Space Mono, monospace:
          Wikipedia Knowledge Flow
      </h1>
      <p style='color: #8b949e; margin: 6px 0 0 0; font-size: 0.95rem'>
          Covid-19
      </p>
  </div>
  """, unsafe_allow_html=True)     # 'true' states that its safe to run

  # to load data
  with st.spinner("loading snapshot data..."):
    data, graphs =load_dashboard_data()

  if data is None:
    st.error("json file not found")
    return

  available_years = sorted(data['snapshots'])     # creates a list in ascending order

  # creating the sidebar
  with st.sidebar:
      st.markdown("### Controls")     # '###' is to define size of text
      selected_year=st.select_slider(
          "Select Year",
          options=available_years,
          value=available_years[-1]     # -1 is get the slider from oldest to newest
      )
      top_n_network=st.slider("Nodes in Network Graph", 10, 200, 100, 5)     # lower limit, upper limit, default, step size
      top_n_table = st.slider("Articles in Rankings Table", 5,30,10,5)
      top_n_lines=st.slider("Articles in Centrality Chart",3,15,8,1)
      metric_choice = st.selectbox(
          "Centrality Metric",
          ["pagerank","in_degree","betweenness"],     # betweeness measures how often a node occurs on the shortest path between two nodes
          format_func=lambda x: x.replace("_"," ").title()     # replace underscore with face
      )

      st.markdown("---")
      st.markdown("### Loaded Snapshots")
      for y in available_years:
          m = data['metrics'][y]
          st.markdown(f"**{y}** - {m['n_nodes']} articles, {m['n_edges']:,} edges")     # asterisk for formating

    # computing metrics for year that is selected
  metrics_df = build_metrics_df(data, selected_year, sort_by=metric_choice)
  G = graphs.get(selected_year)
  year_m = data['metrics'][selected_year]

  # top metrics
  st.markdown(f"### Wikipedia Article Network Overview — {selected_year}")

  c1,c2,c3,c4 = st.columns(4)
  with c1:
    st.metric("Articles (Nodes)", f"{year_m['n_nodes']:,}")
  with c2:
    st.metric("Links (Edges)", f"{year_m['n_edges']:,}")
  with c3:
    st.metric("Network Density", f"{year_m['density']:.4f}")
  with c4:
    top_article=metrics_df.iloc[0]["article"]     # iloc is used to pick a specific column
    st.metric("Top Hub", top_article[:25] + "..." if len(top_article) > 25 else top_article)

  # building the network graph
  st.markdown(f"<div class='section-header'> Network Graph - Top {top_n_network} Articles </div>", unsafe_allow_html=True)
  st.caption("Node size = PageRank importance · Node colour = In-degree · Hover for details")

  with st.spinner("Rending network..."):
    network_fig = build_networks(G, metrics_df, top_n=top_n_network)
    st.plotly_chart(network_fig, width='stretch')

  # table for top articles and centrality chart
  col_left, col_right = st.columns([1,1])
  with col_left:
    st.markdown(f"<div class='section-header'> Top {top_n_table} Articles by {metric_choice.replace('_',' ').title()}</div>", unsafe_allow_html=True)
    display_df= metrics_df[["article", "pagerank",  "in_degree", "out_degree", "betweenness"]].head(top_n_table).copy()
    display_df["pagerank"]=display_df["pagerank"].apply(lambda x: f"{x:.4f}")
    display_df["betweenness"]=display_df["betweenness"].apply(lambda x: f"{x:.4f}")
    display_df.index = range(1, len(display_df)+1)
    display_df.columns = ["Article", "PageRank", "In-Degree", "Out-Degree", " Betweeness"]
    st.dataframe(display_df, use_container_width=True, height=350)

  with col_right:
    st.markdown(f"<div class='section-header'> {metric_choice.replace('_',' ').title()} Over Time</div>", unsafe_allow_html=True)
    centrality_fig = build_centrality_chart(data, metric=metric_choice, top_n=top_n_lines)
    st.plotly_chart(centrality_fig, width='stretch')

  # Community detection results
  n_comm_key = f'n_communities_{selected_year}'
  mod_key  = f'modularity_{selected_year}'
  n_comm = year_m.get(n_comm_key)
  mod = year_m.get(mod_key)

  if n_comm is not None:
      st.markdown('### Community Structure')
      cc1, cc2 = st.columns(2)
      with cc1:
          st.metric('Communities Detected', n_comm)
      with cc2:
          st.metric('Modularity', f'{mod:.4f}' if mod is not None else 'N/A')
      comm_fig = build_community_chart(data)
      st.plotly_chart(comm_fig, width='stretch')

  # structural shifts
  shifts = data.get('structural_shifts', [])
  st.markdown('### Structural Shifts')
  if shifts:
      shifts_fig = build_structural_shifts_chart(data)
      st.plotly_chart(shifts_fig, width='stretch')

  # link changes
  st.markdown("<div class='section-header'> Link Changes Between Years</div>", unsafe_allow_html=True)

  changes = data.get('changes', {})
  change_records = []
  for period_key, c in changes.items():
      y1, y2 = period_key.split('_to_')
      change_records.append({
          'period':  f'{y1} to {y2}',
          'edges_added'  : c['edges_added'],
          'edges_removed'  : c['edges_removed'],
          'nodes_added'  : c['nodes_added'],
          'nodes_removed' : c['nodes_removed'],
          'new_hubs':  c.get('new_hubs', []),
          'lost_hubs' : c.get('lost_hubs', []),
          'sample_added' : c.get('sample_added_edges', []),
          'sample_removed' : c.get('sample_removed_edges', []),
      })
  if change_records:
      changes_fig = build_changes_chart(change_records)
      st.plotly_chart(changes_fig, width='stretch')

      # for per article changes
      st.markdown("#### Per Article Changes")
      period_labels=[r["period"] for r in change_records]
      sel_period=st.selectbox("Select Period", period_labels)
      sel_record = next(r for r in change_records if r["period"] == sel_period)

      col_a, col_b = st.columns(2)
      with col_a:
          st.metric('Nodes Added', sel_record['nodes_added'])
          st.metric('Edges Added', sel_record['edges_added'])
      with col_b:
          st.metric('Nodes Removed', sel_record['nodes_removed'])
          st.metric('Edges Removed', sel_record['edges_removed'])
      if sel_record['new_hubs'] or sel_record['lost_hubs']:
          h1, h2 = st.columns(2)
          with h1:
              st.markdown('**New Top Hubs:**')
              for hub in sel_record['new_hubs']:
                  st.markdown(f"<span style='color:#3fb950'>+ {hub}</span>", unsafe_allow_html=True)
          with h2:
              st.markdown('**Lost Top Hubs**')
              for hub in sel_record['lost_hubs']:
                st.markdown(f"<span style='color:#f85149'>− {hub}</span>", unsafe_allow_html=True)

      if sel_record['sample_added'] or sel_record['sample_removed']:
          with st.expander('Sample Edge Changes'):
              e1, e2 = st.columns(2)
              with e1:
                  st.markdown('**Sample Added Edges:**')
                  for edge in sel_record['sample_added'][:10]:
                      st.markdown(f"<span style='color:#3fb950'>+ {edge[0]} → {edge[1]}</span>", unsafe_allow_html=True)
              with e2:
                  st.markdown('**Sample Removed Edges:**')
                  for edge in sel_record['sample_removed'][:10]:
                      st.markdown(f"<span style='color:#f85149'>− {edge[0]} → {edge[1]}</span>", unsafe_allow_html=True)


  else:
      st.info("no link changes found for this period.")

    # footer
  st.markdown("---")
  st.markdown(
      "<p style='text-align:center; color:#8b949e; font-size:0.8rem'>DS3294 · Wikepedia Link Structure & Knowldedge Flow</p>",
      unsafe_allow_html=True
  )

if __name__ == "__main__":
  main()
