import pandas as pd
import os

def generate_temporal_analysis_report():
    print("Generating Temporal Centrality Analysis Report...")
    
    try:
        df = pd.read_csv("pratik_progress/centrality_master_export.csv")
    except FileNotFoundError:
        print("Error: centrality_master_export.csv not found.")
        return

    years = sorted(df['year'].unique())
    
    report_lines = []
    report_lines.append("# Temporal Analysis of Centrality Measures")
    report_lines.append("*(Fulfilling 'Additional Tasks: Analyse how centrality measures change over time and interpret their meaning')*\n")
    
    # 1. PAGERANK KNOWLEDGE HUBS
    report_lines.append("## 1. Top Knowledge Hubs over time (PageRank)")
    report_lines.append("PageRank measures global importance. An article with a high PageRank is linked to by other highly important articles, acting as a foundational pillar of the knowledge flow.\n")
    
    for year in years:
        top_pr = df[df['year'] == year].nlargest(5, 'pagerank')
        report_lines.append(f"**{year} Top Hubs:**")
        for _, row in top_pr.iterrows():
            report_lines.append(f"- **{row['article']}** (Score: {row['pagerank']:.6f})")
        report_lines.append("")
        
    # 2. BETWEENNESS BOTTLENECKS
    report_lines.append("## 2. Navigational Bottlenecks over time (Betweenness Centrality)")
    report_lines.append("Betweenness Centrality reveals navigational 'bridges'. Articles with high betweenness connect disparate clusters of Wikipedia topics. If these articles were removed, navigating between different knowledge domains would become significantly harder.\n")
    
    for year in years:
        top_bw = df[df['year'] == year].nlargest(5, 'betweenness')
        report_lines.append(f"**{year} Top Bridges:**")
        for _, row in top_bw.iterrows():
            report_lines.append(f"- **{row['article']}** (Score: {row['betweenness']:.6f})")
        report_lines.append("")
        
    # 3. INTERPRETATION
    report_lines.append("## 3. Interpretation & Structural Context")
    report_lines.append("### Why these specific articles?")
    report_lines.append("- **The Maturation of PageRank (Hubs):** In early graphs (2024), the top hubs were dedicated to initial virus biology (e.g., *Origin of COVID-19*, evolutionary biologists) and immediate logistical fallouts (*global supply chain crisis*). However, by 2025 and 2026, the Wikipedia knowledge base had profoundly matured. The top hubs transitioned completely to referencing authorities (*Digital object identifier*, *PubMed*, *Semantic Scholar*, *WHO*). This indicates COVID-19 articles shifted from breaking news architectures to heavily cited, scientifically peer-reviewed architectures.")
    report_lines.append("- **The Evolution of Bottlenecks (Bridges):** In 2024, Betweenness bridges focused on merging the biological virus with societal impacts (e.g., bridging *COVID-19* with *Gendered impact of the COVID-19 pandemic* or specific biological indicators like *Ageusia*). By 2025 and 2026, the bridges shifted toward institutional trackers (*Johns Hopkins University*), major journalistic pillars (*The Washington Post*), historical comparisons (*2002–2004 SARS outbreak*), and archival curation (*Wayback Machine*). The navigational flow thus shifted from 'what is happening now' to 'how we are actively tracking, managing, and archiving the pandemic historically'.")

    report_path = "pratik_progress/temporal_analysis/centrality_interpretation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"[SUCCESS] Report generated at: {report_path}")

if __name__ == "__main__":
    generate_temporal_analysis_report()
