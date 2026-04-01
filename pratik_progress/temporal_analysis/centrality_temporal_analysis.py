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
    report_lines.append("## 3. Interpretation & Structural Shifts")
    report_lines.append("- **Knowledge Redistribution:** By tracking the PageRank evolution from 2024 to 2026, we can observe whether knowledge distribution is consolidating into a few central pillar 'super-articles' or fragmenting into multiple specific sub-domain articles.")
    report_lines.append("- **Emerging Topics:** A rapid spike in Betweenness Centrality for an article from one year to the next indicates it has newly become a critical bridge. This often represents an emerging overarching topic that connects previously disjointed concepts.")

    report_path = "pratik_progress/centrality_interpretation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"[SUCCESS] Report generated at: {report_path}")

if __name__ == "__main__":
    generate_temporal_analysis_report()
