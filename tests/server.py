# A local web server for the tests: static files from argv[1], plus a stand-in for the Wolfram service at POST /svc,
# speaking its wire: form field payload_b64 (base64 of UTF-8 JSON) in, {"reply_b64": …} out. Clicks are kept in CLICKS (GET /svc/clicks);
# POST /svc/offline {"on": true} makes /svc fail like a lost connection.
# Passkey 'service-pass'; POST /svc/fail {"on": true} makes it refuse to record a completed task.
# © Computational Classnotes · CC BY-NC-SA 4.0
import http.server, json, sys, functools, base64, urllib.parse
JOBS = {'SJ': {'id': 'SJ', 'name': 'Service job', 'specifics': '**From the service.**', 'subtasks': [{'id': 'SJ-01', 'text': 'First'}, {'id': 'SJ-02', 'text': 'Second'}]}}
DONE = {}; STATE = {'fail_complete': False, 'jobs': False, 'offline': False}; SEEN_STATIONS = set(); CLICKS = []
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    def do_OPTIONS(self): self.send_response(204); self.cors(); self.end_headers()
    def do_GET(self):
        if self.path == '/svc/clicks':
            d = json.dumps(CLICKS).encode(); self.send_response(200); self.cors(); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(d); return
        super().do_GET()
    def do_POST(self):
        raw = self.rfile.read(int(self.headers['Content-Length'] or 0))
        wire = self.path == '/svc'
        if wire:
            if STATE['offline']: self.send_response(503); self.cors(); self.end_headers(); return
            b = json.loads(base64.b64decode(urllib.parse.parse_qs(raw.decode())['payload_b64'][0]).decode('utf-8'))
        else: b = json.loads(raw or b'{}')
        if 'station' in b: SEEN_STATIONS.add(b['station'])
        if self.path == '/svc/offline': STATE['offline'] = b.get('on', False); out = {'ok': True}
        elif b.get('action') in ('tick', 'event'): CLICKS.append(b); out = {'ok': True}
        elif self.path == '/svc/fail': STATE['fail_complete'] = b.get('on', False); out = {'ok': True}
        elif self.path == '/svc/jobs': STATE['jobs'] = b.get('on', False); out = {'ok': True}
        elif b.get('passkey') != 'service-pass': out = {'ok': False}
        elif b.get('action') == 'signin': out = {'ok': True, 'done': DONE.get(b['page'], []), **({'jobs': [{'id': j['id'], 'name': j['name']} for j in JOBS.values()]} if STATE['jobs'] else {})}
        elif b.get('action') == 'job': out = {'ok': True, **JOBS[b['job']]} if b.get('job') in JOBS else {'ok': False, 'message': 'no such job'}
        elif b.get('action') == 'complete':
            out = {'ok': False, 'message': 'stand-in refused'} if STATE['fail_complete'] else (DONE.setdefault(b['page'], []).append(b.get('job') or b['task']) or {'ok': True})
        else: out = {'ok': False}
        if wire: out = {'reply_b64': base64.b64encode(json.dumps(out, ensure_ascii=False).encode('utf-8')).decode()}
        d = json.dumps(out).encode(); self.send_response(200); self.cors(); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(d)
http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(H, directory=sys.argv[1])).serve_forever()
