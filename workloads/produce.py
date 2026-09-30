"""Generate real OTLP/HTTP metrics using only Python's standard library."""
import json
import sys
import time
import urllib.request

url, case = sys.argv[1:]
now = str(time.time_ns())
points = []
for i in range(20 if case == "cardinality" else 2):
    attributes = [{"key":"route","value":{"stringValue":f"/route/{i}"}}, {"key":"status","value":{"stringValue":"200"}}]
    if case == "unexpected_label":
        attributes.append({"key":"user_id","value":{"stringValue":"person-42"}})
    points.append({"attributes":attributes,"asInt":str(100+i),"timeUnixNano":now,"startTimeUnixNano":str(int(now)-1_000_000_000)})
metrics = [{"name":"lab_requests", "description":"Number of requests", "sum":{"isMonotonic":True,"aggregationTemporality":2,"dataPoints":points}}]
if case != "missing_metric":
    metrics.append({"name":"lab_queue_depth","gauge":{"dataPoints":[{"asInt":"3","timeUnixNano":now,"attributes":[{"key":"queue","value":{"stringValue":"default"}}]}]}})
payload = {"resourceMetrics":[{"resource":{"attributes":[{"key":"service.name","value":{"stringValue":"gate-producer"}}]},"scopeMetrics":[{"scope":{"name":"gate"},"metrics":metrics}]}]}
for attempt in range(30):
    try:
        req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=3) as response:
            print(response.status)
        break
    except OSError:
        if attempt == 29:
            raise
        time.sleep(0.5)
