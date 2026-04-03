import urllib.request, time, json

def post(url):
    req = urllib.request.Request(url, method='POST')
    with urllib.request.urlopen(req) as r:
        print('POST response:', r.read().decode())

print('Triggering failure...')
post('http://localhost:5000/api/trigger-failure')

for i in range(8):
    time.sleep(1)
    try:
        s = urllib.request.urlopen('http://localhost:5000/api/update-status').read().decode()
        print('POLL', i, s)
    except Exception as e:
        print('POLL ERR', e)
