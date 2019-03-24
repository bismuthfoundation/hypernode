import json
from tornado.httpclient import HTTPClient, HTTPError

url = "https://hyper.bisafe.net/regs/5/1/5176.json"

http_client = HTTPClient()
try:
    response = http_client.fetch(url)
    if type(response.body) is bytes:
        obj = json.loads(response.body.decode('utf-8'))
        print(obj)
except HTTPError as e:
    # HTTPError is raised for non-200 responses; the response
    # can be found in e.response.
    print("Error: " + str(e))
except Exception as e:
    # Other errors are possible, such as IOError.
    print("Error: " + str(e))
http_client.close()
