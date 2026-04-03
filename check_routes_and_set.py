import urllib.request, json, time

def get(url):
    try:
        with urllib.request.urlopen(url) as r:
            return r.read().decode()
    except Exception as e:
        return f'ERROR: {e}'

print('GET /api/list-routes')
print(get('http://localhost:5000/api/list-routes'))

print('\nGET /api/update-status')
print(get('http://localhost:5000/api/update-status'))

print('\nGET /api/set-state?state=failed&msg=manual_test')
print(get('http://localhost:5000/api/set-state?state=failed&msg=manual_test'))

print('\nPolling /api/update-status 6 times:')
for i in range(6):
    s = get('http://localhost:5000/api/update-status')
    try:
        print('POLL', i, json.loads(s))
    except:
        print('POLL', i, s)
    time.sleep(1)
