from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import ssl
import os
from dotenv import load_dotenv
from rdflib import Graph

load_dotenv()

ssl._create_default_https_context = ssl._create_unverified_context

local_g = Graph()
local_g.parse("mechanization_data.ttl", format="turtle")

local_query = """
    PREFIX schema: <https://schema.org/>
    SELECT DISTINCT ?brandName WHERE {
        ?brand a schema:Organization ;
               schema:name ?brandName .
    }
"""
local_results = local_g.query(local_query)

brand_values_string = " ".join([f'"{row.brandName}"@en' for row in local_results])

sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.agent = os.getenv("USER_AGENT")

query_string = f"""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?brand_name ?hq_country WHERE {{
      VALUES ?brand_name {{ {brand_values_string} }}
      
      ?brand rdfs:label ?brand_name .
      ?brand wdt:P159 ?hq_city .
      ?hq_city wdt:P17 ?country .
      
      ?country rdfs:label ?hq_country .
      FILTER(LANG(?hq_country) = "en")
    }}
"""

sparql.setQuery(query_string)
sparql.setReturnFormat(JSON)

try:
    results = sparql.query().convert()
    
    data = []
    for result in results["results"]["bindings"]:
        brand = result["brand_name"]["value"]
        country = result["hq_country"]["value"]
        data.append({"Tractor Brand": brand, "Headquarters Country": country})
    
    df = pd.DataFrame(data)
    print(df.to_string(index=False))
    
except Exception as e:
    print(e)