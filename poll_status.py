import urllib.request, time
for i in range(8):
    time.sleep(1)
    try:
        s = urllib.request.urlopen('http://localhost:5000/api/update-status').read().decode()
        print('POLL', i, s)
    except Exception as e:
        print('ERR', e)
