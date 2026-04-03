import urllib.request, time, json

def get(url):
    try:
        with urllib.request.urlopen(url) as r:
            return r.read().decode()
    except Exception as e:
        return f'ERROR: {e}'

print('Calling /api/set-state to set failed state...')
print(get('http://localhost:5000/api/set-state?state=failed&msg=simulated_test'))

for i in range(8):
    s = get('http://localhost:5000/api/update-status')
    try:
        obj = json.loads(s)
        print(f'POLL {i}:', json.dumps(obj, ensure_ascii=False))
    except Exception:
        print(f'POLL {i}:', s)
    time.sleep(1)
