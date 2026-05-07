import csv

with open(r"Avance Del Proyecto\data\ferreterias.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

# Search partial words
tests = ["CERAMI", "CAREPA", "CHIGORODO", "MARRONE", "CONSTRURED",
         "FERKATIO", "FERCOL ZOMAC", "AGROFERRE", "VITALTEK", "INMDEKO"]
for t in tests:
    found = [r for r in rows if t.upper() in r["razon_social"].upper()]
    if found:
        print(f"FOUND '{t}': {found[0]['razon_social']} | NIT: {found[0]['nit']}")
    else:
        print(f"NOT FOUND: '{t}'")

# Show first 5 entries with camara_comercio = ORIENTE ANTIOQUENO
oriente = [r for r in rows if "ORIENTE" in r.get("camara_comercio","").upper()]
print(f"\nRows with ORIENTE ANTIOQUENO in camara_comercio: {len(oriente)}")
for r in oriente[:5]:
    print(f"  {r['razon_social']} | NIT: {r['nit']}")
