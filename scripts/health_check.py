import urllib.request, json, sys

checks = [
    ("Hardhat (8545)", "http://127.0.0.1:8545"),
    ("Backend /health", "http://127.0.0.1:8000/health"),
    ("Frontend (5173)", "http://localhost:5173"),
]

all_ok = True
for name, url in checks:
    try:
        res = urllib.request.urlopen(url, timeout=5)
        body = res.read().decode()
        if "health" in url:
            data = json.loads(body)
            print(f"OK  {name}: HTTP {res.status} | parcels={data['parcel_count']} | mode={data['blockchain_mode']}")
        else:
            print(f"OK  {name}: HTTP {res.status}")
    except Exception as e:
        print(f"ERR {name}: {e}")
        all_ok = False

sys.exit(0 if all_ok else 1)
