import mysql.connector
import urllib.parse
import os
from dotenv import load_dotenv
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD

load_dotenv()

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = db.cursor(dictionary=True)

query = """
SELECT b.name AS brand_name, m.name AS model_name, m.category, e.power_hp 
FROM tractor_model m
JOIN brand b ON m.brand_id = b.brand_id
JOIN engine_setup e ON m.model_id = e.model_id
"""
cursor.execute(query)
results = cursor.fetchall()

g = Graph()
schema = Namespace("https://schema.org/")
mech = Namespace("http://example.org/mechanization/")

g.bind("schema", schema)
g.bind("mech", mech)

print(f"Found {len(results)} rows in the database")

for row in results:
    safe_brand = urllib.parse.quote(row['brand_name'].replace(" ", "_"))
    safe_model = urllib.parse.quote(row['model_name'].replace(" ", "_"))
    
    brand_uri = URIRef(mech[f"brand/{safe_brand}"])
    model_uri = URIRef(mech[f"tractor/{safe_model}"])
    
    g.add((brand_uri, RDF.type, schema.Organization))
    g.add((brand_uri, schema.name, Literal(row['brand_name'], lang="en")))
    
    g.add((model_uri, RDF.type, schema.Vehicle))
    g.add((model_uri, schema.name, Literal(row['model_name'], lang="en")))
    
    g.add((model_uri, schema.manufacturer, brand_uri)) 
    
    if row['power_hp']:
        g.add((model_uri, mech.horsepower, Literal(row['power_hp'], datatype=XSD.integer)))

output_file = 'mechanization_data.ttl'
g.serialize(destination=output_file, format='turtle')

print(f"Triplification successful! {len(g)} triples are saved in '{output_file}'.")

cursor.close()
db.close()