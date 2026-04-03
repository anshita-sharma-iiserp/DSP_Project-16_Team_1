# Link Structure & Knowledge Flow Dashboard (Wikipedia Internal Link Analysis)

![Status Completed](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python) ![NetworkX](https://img.shields.io/badge/NetworkX-Graph_Math-yellow?style=for-the-badge) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=for-the-badge&logo=streamlit)

##  Project Overview
This project models Wikipedia’s internal link structure as a temporal directed graph. We select the topic COVID-19, ingest historical link data via the Wikimedia API, and construct yearly time-snapshot graphs for the years 2020-2026. Using graph metrics such as degree centrality, PageRank, betweenness, and strongly connected components, we characterise structural properties and temporal changes between snapshots.

Our contributions are threefold: (1) a reproducible pipeline for extracting temporally consistent link neighborhoods, (2) a comparative analysis of graph storage strategies (adjacency lists, sparse matrices, GEXF), and (3) an interactive dashboard visualising the evolving link network with key hubs and bottlenecks.

---

##  Repository Structure & Pipeline Flow

The final compiled project is spread across four primary pipelines designed by our team, executed sequentially:

### 1. Data Extraction & Matrix Storage 
- Handles Wikipedia API ingestion extracting raw graph edges and nodes per year.
- Computes various data structuring formats comparing adjacency lists (`adj_lists.json`), edge lists ('edge_lists.json'), sparse matrices (`adj_matrix_YYYY_sparse.npz`), and the final standard Graph Exchange XML Formats (`COVID_19_YYYY.gexf`).
- **Output:** Staged `.gexf` files covering all temporal snapshots from 2020 to 2026.

### 2. Centrality Graph Mathematics 
- Executes massive topological calculations loading Nidhi's `COVID_19_YYYY.gexf` temporal snapshots.
- **`centrality_measure.py`:** Calculates mathematically complex metrics per node including:
  - PageRank (Global importance α=0.85).
  - Out/In-Degree Centrality (Immediate network dominance).
  - Betweenness Centrality (Approximation sampling $k=500$ to identify structural bottlenecks bridging topics securely).
  - Eigenvector Centrality.
- **Output:** Outputs the structured mathematical proof `centrality_master_export.csv` which perfectly aligns temporal features into dataframes for the application frontend.

### 3. Temporal Graph Level Analysis 
- Extracts macro-level architectural transitions over the timeline using the `updated gexf files`.
- **`Graph_math.py` & `take_in_gexf.py`:** Reads the historical snapshots and computes:
  - Strong/Weak Connected Components (SCC/WCC) to track network Consolidation and Fragmentation shifts.
  - Overall Density and Network Densification tracking.
  - Structural hub evolution delta changes (new hubs vs. lost hubs).
- **Output:** Autogenerates analytical graphs detailing connectivity transitions inside the `analysis_plots` directory.

### 4. Interactive Dashboard Frontend 
- The culminating Streamlit UI consolidating all raw mathematical data into intuitive visualization components.
- **`code/dashboard_code.py`** Streams the metrics (such as the `centrality_master_export.csv`) into interactive visual plots and temporal sliders. Enables interactive graph exploration without continuously halting the underlying heavy python simulations.

---

##  Tech Stack & Dependencies

- **Data Processing:** `pandas`, `json`, `numpy`, `re`
- **Mathematics & Algorithms:** `networkx`
- **Data Engineering Visualization:** `matplotlib`, `plotly`, `pyvis`
- **Application Web Framework:** `streamlit`

---

##  Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/anshita-sharma-iiserp/DSP_Project-16_Team_1.git
   cd DSP_Project-16_Team_1
   ```

2. **Install Required Libraries**
   Ensure you have a modern Python 3 instance running (virtual environments are recommended).
   ```bash
   pip install networkx pandas numpy matplotlib streamlit plotly pyvis
   ```

3. **Running the Application**
   Ensure the present working directory is `\\ DSP_Project-16_Team_1\Final_ready_to _run`
   To explore the timeline, launch the visual dashboard using:
   ```bash
   python Anshita_progress/take_in_gexf
   streamlit run aadya_ashwin/code/dashboard_code.py
   ```
   *(The application will automatically boot in your browser at `http://localhost:8501`)*

---


##  Team Members & Specific Contributions
- **Nidhi Bhagwat:** Data collection, Wikimedia API integration, adjacency matrix
storage, GEXF generation, storage strategy comparison, report writing (Results,
Conclusion, Algorithms)
- **Pratik Kumar Sahoo:** Graph mathematics, centrality measures (PageRank, be
tweenness), report writing (Results, Conclusion)
- **Anshita Sharma:** Graph analysis, temporal metrics computation, structural shift
detection, report writing (Introduction, Related work, Methods, Results, Conclu
sion)
- **Aadya Ashwin:**  Enriched GEXF with node metadata, dashboard data preparation,
interactive dashboard development using Streamlit, visualization design, frontend
implementation, user interaction features, report writing (Results, Conclusion)
