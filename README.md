# ***DSP Project***

***Data Source***

Pick wikipedia categories falling under the COVID-19 Wikipedia Article 

Categories chosen: 
- COVID-19 Testing (https://en.wikipedia.org/wiki/COVID-19_testing)
- Symptomps of COVID-19 (https://en.wikipedia.org/wiki/Symptoms_of_COVID-19)
- COVID-19 vaccine (https://en.wikipedia.org/wiki/COVID-19_vaccine)
- SARS-CoV-2 (https://en.wikipedia.org/wiki/SARS-CoV-2)

***Preprocessing Plan***

Ingest internal link data for the selected articles using requests (wikipedia API does not give revision history)

***Code Structure Plan***

* Data Ingestion: `requests` (Wikimedia API)
* Data Processing: `pandas`, `re` (Regex parsed Wikitext)
* Graph Mathematics: `networkx`
  * Construction of graph for four separate categories
  * Unification of graph 
* Interactive Visualisation: `streamlit`, `plotly`, `pyvis`


***Debugging Plan***

Add errors and exceptions to the code to make sure that the code can run for any other set of wikipedia articles.

