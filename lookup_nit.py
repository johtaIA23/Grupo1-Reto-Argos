"""
Look up NIT for a list of companies via datos.gov.co RUES.
Queries in batches to avoid rate limits.
"""
import csv
import time
import unicodedata
import re
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import URLError

NAMES_PATH = r"c:\Users\Usuario\Documents\projects\Ferreterias Colombia\temp_names.txt"
OUT_PATH   = r"c:\Users\Usuario\Documents\projects\Ferreterias Colombia\nit_resultado.tsv"

RUES_URL = "https://www.datos.gov.co/resource/mc5k-hxq4.json"

def normalize(s: str) -> str:
    s = s.upper().strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip()

# Load query names — deduplicate, remove BOM
with open(NAMES_PATH, encoding='utf-8-sig') as f:
    query_names = list(dict.fromkeys([l.strip() for l in f if l.strip()]))

print(f"Companies to look up: {len(query_names)}")

results = []
not_found = []

BATCH = 5

for i in range(0, len(query_names), BATCH):
    batch = query_names[i:i+BATCH]
    # Build OR condition
    conditions = " OR ".join(
        f"upper(razon_social)='{normalize(n).replace(chr(39), chr(39)+chr(39))}'"
        for n in batch
    )
    params = {
        "$where": conditions,
        "$limit": str(BATCH * 3),
        "$select": "razon_social,nit,municipio,codigo_ciiu_principal,estado_matricula,fecha_matricula",
    }
    url = RUES_URL + "?" + "&".join(
        f"{k}={quote(str(v))}" for k, v in params.items()
    )

    found_names = set()
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for rec in data:
            name = rec.get("razon_social", "")
            nit  = rec.get("nit", "")
            city = rec.get("municipio", "")
            ciiu = rec.get("codigo_ciiu_principal", "")
            estado = rec.get("estado_matricula", "")
            # match back to query name
            matched = None
            for qn in batch:
                if normalize(qn) == normalize(name):
                    matched = qn
                    break
            if not matched:
                matched = name  # use returned name
            found_names.add(normalize(matched))
            results.append((matched, name, nit, city, ciiu, estado))
    except Exception as e:
        print(f"  Error batch {i//BATCH + 1}: {e}")

    for qn in batch:
        if normalize(qn) not in found_names:
            not_found.append(qn)

    if (i // BATCH + 1) % 5 == 0:
        print(f"  Processed {i+BATCH}/{len(query_names)}...")
    time.sleep(0.3)

# Write results
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("nombre_buscado\trazon_social_rues\tnit\tciudad\tciiu\testado_matricula\n")
    for r in results:
        f.write("\t".join(str(x) for x in r) + "\n")
    f.write(f"\n--- NO ENCONTRADOS ({len(not_found)}) ---\n")
    for n in not_found:
        f.write(f"  {n}\n")

print(f"\nEncontrados: {len(results)}")
print(f"No encontrados: {len(not_found)}")
print(f"Resultado en: {OUT_PATH}")
