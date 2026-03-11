# COVID-19 Symptoms Trial Run: End-to-End Walkthrough

Welcome to the **Symptoms domain trial run** for our DSP Group Project! 

This folder contains a complete, functioning prototype of the Link Structure & Knowledge Flow Dashboard. We successfully built a pipeline to ingest, analyze, and visualize how the medical consensus around COVID-19 symptoms evolved on Wikipedia between 2020 and 2022.

Here is a detailed, step-by-step breakdown of how this trial was built, which you can use as a blueprint for the other domains (e.g., Treatments, Social Impact).

---

## The Tech Stack
*   **Data Ingestion:** `requests` (Wikimedia API)
*   **Data Processing:** `pandas`, `re` (Regex parsed Wikitext)
*   **Graph Mathematics:** `networkx`
*   **Interactive Visualization:** `streamlit`, `plotly`, `pyvis`

---

## Step-by-Step Methodology

### Step 1: Article Discovery (`step1_article_discovery.py`)
We needed a list of Wikipedia articles that belong strictly to the "COVID-19 Symptoms" domain. 
*   **How we did it:** We hit the Wikimedia API using the `query` action and `list=categorymembers`. We started at the root category (`Category:Symptoms_of_COVID-19`) and recursed downwards, pulling in ~3,800 distinct medical articles that form the core vocabulary for our network.
*   **Output:** `data/discovered_articles.csv`

### Step 2: Graph Construction (`step2_graph_construction.py`)
With our 3.8k nodes identified, we needed to find out how they interlink.
*   **How we did it:** We batched API requests to fetch all `prop=links` (outgoing internal Wikipedia links) for every single article in our list. We used `networkx` to build a directed graph (`DiGraph`), where an edge `(A -> B)` means Article A hyperlinks to Article B.
*   **Output:** `data/symptoms_edgelist.csv` (for database insertion) and `graphs/symptoms_graph.graphml` (for Python memory loading).

### Step 3: Graph Metrics (`step5_metrics.py`)
*(Note: Named step 5 to align with the prompt's rubric)*
We needed to mathematically prove which symptoms/articles were the most central to the pandemic.
*   **How we did it:** We loaded the `GraphML` file into memory and ran `nx.pagerank()` and `nx.degree()`. This proved mathematically that hubs like "Loss of smell" had massive structural importance in the network, as so many other COVID-19 pages routed to them.
*   **Output:** `data/network_metrics.csv`

### Step 4: Temporal Analysis (`step4_temporal.py`)
The live Wikipedia API only shows *current* links. We needed to prove our "Structural Shifts" requirement by looking at the past.
*   **How we did it:** Instead of tracking 84 individual months (which would take 300,000 API calls and get us rate-limited), we developed a **4-Phase Chronological Model** capturing major milestones:
    1.  `March 2020`: The "Classic Triad" (Cough, Fever) 
    2.  `July 2020`: The "Sensory Discovery" (Loss of Smell/Taste)
    3.  `March 2021`: The "Chronic Realization" (Long COVID emergence)
    4.  `Jan 2022`: The "Omicron Shift" 
*   For each timestamp, we used `prop=revisions` to download the raw historical WikiText, extracted the `[[internal links]]` using Regex, built 4 historical graphs, and calculated the delta in PageRank between them.
*   **Output:** `data/temporal_shifts.csv` and 4 historical `.graphml` files.

### Step 5: The Interactive Dashboard (`step6_dashboard.py`)
We needed a way to present this massive dataset interactively. 
*   **How we did it:** We built a local web app using `Streamlit`. 
    *   **Tab 1:** Uses `plotly` to show bar charts of the highest PageRank hubs.
    *   **Tab 2:** Uses `pyvis.network` running a custom Barnes-Hut physics simulation. We added Python UI sliders so the user can dynamically filter out "noise" and increase physics repulsion to declutter the graph. It also includes a **Timeline Slider** allowing you to watch the network topology morph across the 4 chronological phases.
    *   **Tab 3:** Plots the sequential PageRank shifts, proving our temporal hypotheses mathematically.

---

## How to Run It Yourself
We built a Windows batch script to make launching the dashboard effortless for the team. 
1. Open this project in your terminal.
2. Ensure you have the libraries installed: `pip install -r requirements.txt`
3. Run the batch script: `.\trial_run\symptoms\run_dashboard.bat` (or just double click it in File Explorer).
4. The dashboard will automatically open in your browser at `http://localhost:8501`.
