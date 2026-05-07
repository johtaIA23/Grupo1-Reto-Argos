"""
Match company names to NIT from the ferreterias CSV.
Exact + normalized matching only — no false positives.
"""
import csv
import unicodedata
import re

CSV_PATH = r"c:\Users\Usuario\Documents\projects\Ferreterias Colombia\Avance Del Proyecto\data\ferreterias.csv"
NAMES_PATH = r"c:\Users\Usuario\Documents\projects\Ferreterias Colombia\temp_names.txt"
OUT_PATH  = r"c:\Users\Usuario\Documents\projects\Ferreterias Colombia\match_nit_result.tsv"

SUFFIXES = [
    ' SOCIEDAD POR ACCIONES SIMPLIFICADA', ' S.A.S.', ' S.A.S', ' SAS',
    ' S.A.', ' SA', ' LTDA.', ' LTDA', ' EU', ' E.U.', ' E.U',
    ' ZOMAC', ' - EN LIQUIDACION', ' EN LIQUIDACION',
    ' SIGLA MIDECOL LTDA.', ' SIGLA MIDECOL LTDA', ' SIGLA MIDECOL',
]

def normalize(s: str) -> str:
    s = s.upper().strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def strip_suffix(s: str) -> str:
    changed = True
    while changed:
        changed = False
        for suf in SUFFIXES:
            if s.endswith(suf):
                s = s[:-len(suf)].strip()
                changed = True
    return s

# Load CSV
rows = []
with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Build lookup dicts
lookup_full = {}   # full normalized name -> row
lookup_bare = {}   # normalized, no suffixes -> list[row]

for row in rows:
    name = row.get('razon_social', '') or ''
    full = normalize(name)
    bare = strip_suffix(full)
    if full and full not in lookup_full:
        lookup_full[full] = row
    if bare and len(bare) >= 5:
        lookup_bare.setdefault(bare, []).append(row)

# Load query names (unique)
with open(NAMES_PATH, encoding='utf-8') as f:
    query_names = [l.strip() for l in f if l.strip()]

results = []
no_match = []

for qname in query_names:
    qfull = normalize(qname)
    qbare = strip_suffix(qfull)

    row = None

    # 1. Exact full match
    if qfull in lookup_full:
        row = lookup_full[qfull]

    # 2. Bare match (no suffixes)
    if not row and qbare in lookup_bare:
        matches = lookup_bare[qbare]
        row = matches[0]

    if row:
        results.append((qname, row['razon_social'], row['nit'], row.get('camara_comercio', '')))
    else:
        no_match.append(qname)

# Write output as TSV UTF-8
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write("nombre_buscado\trazon_social_csv\tnit\tcamara_comercio\n")
    for r in results:
        f.write('\t'.join(str(x) for x in r) + '\n')
    f.write(f"\n--- SIN MATCH ({len(no_match)}) ---\n")
    for n in no_match:
        f.write(f"  {n}\n")
    f.write(f"\nTotal buscados: {len(query_names)}\n")
    f.write(f"Con NIT: {len(results)}\n")
    f.write(f"Sin match: {len(no_match)}\n")

print(f"Total buscados: {len(query_names)}")
print(f"Con NIT: {len(results)}")
print(f"Sin match: {len(no_match)}")
print(f"Resultado en: {OUT_PATH}")
