import urllib.request, urllib.error, json

BASE = 'http://127.0.0.1:8000'

def request(method, path, data=None, token=None):
    url = BASE + path
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers=headers,
        method=method
    )
    try:
        res = urllib.request.urlopen(req)
        return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

print("=== 1. TEST /seal/ WITHOUT TOKEN ===")
status, body = request('POST', '/seal/UP231000000001', {'declared_value_inr': 500000.0})
print(f"Status: {status} | Detail: {body.get('detail')}")
assert status == 401, f"Expected 401, got {status}"

print("\n=== 2. TEST /community/vote WITHOUT TOKEN ===")
status, body = request('POST', '/community/vote', {'action_id': 0, 'member_indices': [0, 1]})
print(f"Status: {status} | Detail: {body.get('detail')}")
assert status == 401, f"Expected 401, got {status}"

print("\n=== 3. LOGIN AS CITIZEN & ATTEMPT /seal/ (SHOULD BE 403) ===")
_, citizen_login = request('POST', '/auth/login', {'role': 'citizen'})
cit_token = citizen_login['access_token']
status, body = request('POST', '/seal/UP231000000001', {'declared_value_inr': 500000.0}, token=cit_token)
print(f"Status: {status} | Detail: {body.get('detail')}")
assert status == 403, f"Expected 403, got {status}"

print("\n=== 4. LOGIN AS BANK & ATTEMPT /community/vote (SHOULD BE 403) ===")
_, bank_login = request('POST', '/auth/login', {'role': 'bank'})
bank_token = bank_login['access_token']
status, body = request('POST', '/community/vote', {'action_id': 0, 'member_indices': [0, 1]}, token=bank_token)
print(f"Status: {status} | Detail: {body.get('detail')}")
assert status == 403, f"Expected 403, got {status}"

print("\n=== 5. LOGIN AS REGISTRAR & EXECUTE /seal/ (SHOULD BE 200) ===")
_, reg_login = request('POST', '/auth/login', {'role': 'registrar'})
reg_token = reg_login['access_token']
status, body = request('POST', '/seal/UP231000000001', {'declared_value_inr': 500000.0}, token=reg_token)
print(f"Status: {status} | Sealed: {body.get('sealed')} | On-Chain CID: {body.get('off_chain_cid')}")
assert status == 200, f"Expected 200, got {status}"

print("\n=== 6. READ-ONLY ENDPOINTS WITHOUT TOKEN ===")
read_endpoints = [
    '/parcels/?limit=5',
    '/parcels/UP231000000001',
    '/sealed/UP231000000001',
    '/pool/balance',
    '/community/info',
    '/community/gini',
    '/auth/roles',
]
for ep in read_endpoints:
    s, b = request('GET', ep)
    print(f"{ep:30} -> HTTP {s} OK (Open to public)")
    assert s == 200

print("\n>>> ALL TIER 1 LIVE RBAC VERIFICATIONS PASSED 100% <<<")
