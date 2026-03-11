# COVID-19 Symptoms: Knowledge Flow Report
## Additional Tasks: Methodology and Limitations

### 1. Graph Storage Strategies: Adjacency Lists vs. Edge Tables
During the data ingestion phase (`step2_graph_construction.py`), we employed two distinct graph storage formats, each suited for different use-cases:

*   **Edge Tables (`symptoms_edgelist.csv`):** We saved the network as a flat CSV file where each row represents a directed link `(Source, Target)`. 
    *   *Pros:* Highly scalable, human-readable, and serves as an excellent intermediate format for bulk inserting into relational databases (like PostgreSQL) or graph databases (like Neo4j).
    *   *Cons:* Inefficient for complex graph traversal algorithms. To find all neighbors of a node, a full sequential scan (or indexed lookup) is required.
*   **GraphML (`symptoms_graph.graphml`):** We serialized the in-memory NetworkX objects into GraphML XML structures.
    *   *Pros:* Preserves graph-level attributes, node metadata, and edge directions perfectly. It allows us to instantly load the mathematical topology into Memory (RAM) for complex multi-hop algorithms like PageRank or Barnes-Hut physics simulations.
    *   *Cons:* XML overhead makes file sizes large. Loading the entire graph into memory limits the maximum size to the available RAM.

### 2. Data & Modelling Limitations
While this dashboard successfully tracks structural shifts in Wikipedia's consensus on COVID-19 Symptoms, the methodology carries innate data limitations:

*   **API Snapshot Limits (The Granularity Trade-off):** Fetching historical revisions via the Wikimedia API (`prop=revisions`) requires retrieving the raw wikitext and manually parsing it with Regular Expressions. Fetching every month for 4,000 articles equals ~300,000 API requests. To prevent rate-limiting and ensure reproducibility, we limited our temporal analysis to 4 distinct "Phases" across 386 core articles. This provides excellent macro-level narrative but loses micro-level granularity (we don't see the exact day a node surged).
*   **Redirect Handling & Semantics:** Wikipedia heavily utilizes `#REDIRECT` pages (e.g., "Loss of smell" -> "Anosmia"). While our scripts tracked major article names, a completely unified semantic analysis would require resolving every redirect link recursively. Additionally, our regex link extraction (`[[Target|Display Text]]`) treats all links identically, ignoring the semantic context (whether an article hyperlinks to a symptom because it *causes* it, or because it is a *misconception*).
*   **Incomplete Ground Truth:** Wikipedia is a secondary source written by volunteers. The "structural shifts" observed reflect when the *public/editors* integrated medical concepts, which usually trails true clinical discovery timelines by weeks or months.
