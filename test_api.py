"""Test datos.gov.co RUES API - new endpoint"""
import http.client, json, ssl

# New endpoint
host = "www.datos.gov.co"
path = "/resource/c82u-588k.json?$limit=2"

ctx = ssl.create_default_context()
conn = http.client.HTTPSConnection(host, context=ctx, timeout=15)
try:
    conn.request("GET", path, headers={"Accept": "application/json"})
    resp = conn.getresponse()
    body = resp.read().decode("utf-8", errors="replace")
    print("Status:", resp.status)
    print("Body:", body[:1000])
except Exception as e:
    print("Error:", type(e).__name__, e)
finally:
    conn.close()

# Test name search
print("\n--- Search for VITALTEK ---")
conn2 = http.client.HTTPSConnection(host, context=ctx, timeout=15)
try:
    conn2.request("GET", "/resource/c82u-588k.json?$where=upper(razon_social)%20like%20'%25VITALTEK%25'&$limit=5",
                  headers={"Accept": "application/json"})
    resp2 = conn2.getresponse()
    body2 = resp2.read().decode("utf-8", errors="replace")
    print("Status:", resp2.status)
    print("Body:", body2[:1000])
except Exception as e:
    print("Error:", type(e).__name__, e)
finally:
    conn2.close()
