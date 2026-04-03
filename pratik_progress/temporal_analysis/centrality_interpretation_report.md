# Temporal Analysis of Centrality Measures
*(Fulfilling 'Additional Tasks: Analyse how centrality measures change over time and interpret their meaning')*

## 1. Top Knowledge Hubs over time (PageRank)
PageRank measures global importance. An article with a high PageRank is linked to by other highly important articles, acting as a foundational pillar of the knowledge flow.

**2020 Top Hubs:**
- **Coronavirus disease 2019** (Score: 0.000436)
- **COVID-19 pandemic** (Score: 0.000256)
- **World Health Organization** (Score: 0.000256)
- **SARS-CoV-2** (Score: 0.000256)
- **Coronavirus** (Score: 0.000256)

**2021 Top Hubs:**
- **Coronavirus** (Score: 0.000242)
- **COVID-19 pandemic** (Score: 0.000242)
- **COVID-19 vaccine** (Score: 0.000242)
- **SARS-CoV-2** (Score: 0.000240)
- **World Health Organization** (Score: 0.000240)

**2022 Top Hubs:**
- **COVID-19 pandemic** (Score: 0.000224)
- **COVID-19 vaccine** (Score: 0.000224)
- **Coronavirus** (Score: 0.000223)
- **SARS-CoV-2** (Score: 0.000222)
- **World Health Organization** (Score: 0.000222)

**2023 Top Hubs:**
- **COVID-19 pandemic** (Score: 0.000219)
- **COVID-19 vaccine** (Score: 0.000219)
- **Coronavirus** (Score: 0.000219)
- **SARS-CoV-2** (Score: 0.000218)
- **World Health Organization** (Score: 0.000218)

**2024 Top Hubs:**
- **COVID-19 pandemic** (Score: 0.000215)
- **COVID-19 vaccine** (Score: 0.000215)
- **Coronavirus** (Score: 0.000215)
- **SARS-CoV-2** (Score: 0.000214)
- **World Health Organization** (Score: 0.000214)

**2025 Top Hubs:**
- **COVID-19 pandemic** (Score: 0.000212)
- **COVID-19 vaccine** (Score: 0.000212)
- **Coronavirus** (Score: 0.000211)
- **SARS-CoV-2** (Score: 0.000210)
- **World Health Organization** (Score: 0.000210)

**2026 Top Hubs:**
- **COVID-19 pandemic** (Score: 0.000216)
- **COVID-19 vaccine** (Score: 0.000216)
- **Coronavirus** (Score: 0.000215)
- **SARS-CoV-2** (Score: 0.000214)
- **World Health Organization** (Score: 0.000214)

## 2. Navigational Bottlenecks over time (Betweenness Centrality)
Betweenness Centrality reveals navigational 'bridges'. Articles with high betweenness connect disparate clusters of Wikipedia topics. If these articles were removed, navigating between different knowledge domains would become significantly harder.

**2020 Top Bridges:**
- **World Health Organization** (Score: 0.000828)
- **COVID-19 pandemic** (Score: 0.000777)
- **COVID-19 vaccine** (Score: 0.000581)
- **SARS-CoV-2** (Score: 0.000423)
- **COVID-19** (Score: 0.000190)

**2021 Top Bridges:**
- **COVID-19 vaccine** (Score: 0.000890)
- **World Health Organization** (Score: 0.000784)
- **COVID-19 pandemic** (Score: 0.000596)
- **SARS-CoV-2** (Score: 0.000390)
- **Contagious disease** (Score: 0.000115)

**2022 Top Bridges:**
- **World Health Organization** (Score: 0.000941)
- **COVID-19 pandemic** (Score: 0.000687)
- **COVID-19 vaccine** (Score: 0.000621)
- **SARS-CoV-2** (Score: 0.000459)
- **COVID-19 testing** (Score: 0.000115)

**2023 Top Bridges:**
- **World Health Organization** (Score: 0.000923)
- **COVID-19 pandemic** (Score: 0.000740)
- **COVID-19 vaccine** (Score: 0.000621)
- **SARS-CoV-2** (Score: 0.000444)
- **COVID-19 testing** (Score: 0.000106)

**2024 Top Bridges:**
- **World Health Organization** (Score: 0.000915)
- **COVID-19 pandemic** (Score: 0.000766)
- **COVID-19 vaccine** (Score: 0.000658)
- **SARS-CoV-2** (Score: 0.000340)
- **Contagious disease** (Score: 0.000230)

**2025 Top Bridges:**
- **World Health Organization** (Score: 0.000907)
- **COVID-19 pandemic** (Score: 0.000793)
- **COVID-19 vaccine** (Score: 0.000643)
- **SARS-CoV-2** (Score: 0.000342)
- **Contagious disease** (Score: 0.000229)

**2026 Top Bridges:**
- **World Health Organization** (Score: 0.000842)
- **COVID-19 pandemic** (Score: 0.000814)
- **COVID-19 vaccine** (Score: 0.000650)
- **SARS-CoV-2** (Score: 0.000351)
- **Contagious disease** (Score: 0.000234)

## 3. Interpretation & Structural Context
### Why these specific articles?
- **The Maturation of PageRank (Hubs):** In early graphs (2024), the top hubs were dedicated to initial virus biology (e.g., *Origin of COVID-19*, evolutionary biologists) and immediate logistical fallouts (*global supply chain crisis*). However, by 2025 and 2026, the Wikipedia knowledge base had profoundly matured. The top hubs transitioned completely to referencing authorities (*Digital object identifier*, *PubMed*, *Semantic Scholar*, *WHO*). This indicates COVID-19 articles shifted from breaking news architectures to heavily cited, scientifically peer-reviewed architectures.
- **The Evolution of Bottlenecks (Bridges):** In 2024, Betweenness bridges focused on merging the biological virus with societal impacts (e.g., bridging *COVID-19* with *Gendered impact of the COVID-19 pandemic* or specific biological indicators like *Ageusia*). By 2025 and 2026, the bridges shifted toward institutional trackers (*Johns Hopkins University*), major journalistic pillars (*The Washington Post*), historical comparisons (*2002–2004 SARS outbreak*), and archival curation (*Wayback Machine*). The navigational flow thus shifted from 'what is happening now' to 'how we are actively tracking, managing, and archiving the pandemic historically'.