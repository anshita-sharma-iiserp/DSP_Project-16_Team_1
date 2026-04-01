# Temporal Analysis of Centrality Measures
*(Fulfilling 'Additional Tasks: Analyse how centrality measures change over time and interpret their meaning')*

## 1. Top Knowledge Hubs over time (PageRank)
PageRank measures global importance. An article with a high PageRank is linked to by other highly important articles, acting as a foundational pillar of the knowledge flow.

**2024 Top Hubs:**
- **Origin of COVID-19** (Score: 0.004072)
- **COVID-19 pandemic and animals** (Score: 0.004072)
- **Theobald Smith** (Score: 0.004072)
- **Paul W. Ewald** (Score: 0.004072)
- **2021–2023 global supply chain crisis** (Score: 0.004072)

**2025 Top Hubs:**
- **Digital object identifier** (Score: 0.002385)
- **Semantic Scholar** (Score: 0.002385)
- **ISSN** (Score: 0.002145)
- **PubMed** (Score: 0.002145)
- **World Health Organization** (Score: 0.002092)

**2026 Top Hubs:**
- **ISSN** (Score: 0.002320)
- **PubMed** (Score: 0.002320)
- **Semantic Scholar** (Score: 0.002249)
- **Digital object identifier** (Score: 0.002171)
- **PubMed Central** (Score: 0.002171)

## 2. Navigational Bottlenecks over time (Betweenness Centrality)
Betweenness Centrality reveals navigational 'bridges'. Articles with high betweenness connect disparate clusters of Wikipedia topics. If these articles were removed, navigating between different knowledge domains would become significantly harder.

**2024 Top Bridges:**
- **COVID-19** (Score: 0.002184)
- **Gendered impact of the COVID-19 pandemic** (Score: 0.000269)
- **Variants of SARS-CoV-2** (Score: 0.000220)
- **Ageusia** (Score: 0.000174)
- **COVID-19 pandemic** (Score: 0.000171)

**2025 Top Bridges:**
- **COVID-19** (Score: 0.001954)
- **The Washington Post** (Score: 0.000093)
- **World Health Organization** (Score: 0.000071)
- **Johns Hopkins University** (Score: 0.000071)
- **Transmission of COVID-19** (Score: 0.000071)

**2026 Top Bridges:**
- **COVID-19** (Score: 0.001982)
- **2002–2004 SARS outbreak** (Score: 0.000113)
- **Wayback Machine** (Score: 0.000096)
- **Treatment and management of COVID-19** (Score: 0.000093)
- **Symptoms of COVID-19** (Score: 0.000091)

## 3. Interpretation & Structural Context
### Why these specific articles?
- **The Maturation of PageRank (Hubs):** In early graphs (2024), the top hubs were dedicated to initial virus biology (e.g., *Origin of COVID-19*, evolutionary biologists) and immediate logistical fallouts (*global supply chain crisis*). However, by 2025 and 2026, the Wikipedia knowledge base had profoundly matured. The top hubs transitioned completely to referencing authorities (*Digital object identifier*, *PubMed*, *Semantic Scholar*, *WHO*). This indicates COVID-19 articles shifted from breaking news architectures to heavily cited, scientifically peer-reviewed architectures.
- **The Evolution of Bottlenecks (Bridges):** In 2024, Betweenness bridges focused on merging the biological virus with societal impacts (e.g., bridging *COVID-19* with *Gendered impact of the COVID-19 pandemic* or specific biological indicators like *Ageusia*). By 2025 and 2026, the bridges shifted toward institutional trackers (*Johns Hopkins University*), major journalistic pillars (*The Washington Post*), historical comparisons (*2002–2004 SARS outbreak*), and archival curation (*Wayback Machine*). The navigational flow thus shifted from 'what is happening now' to 'how we are actively tracking, managing, and archiving the pandemic historically'.