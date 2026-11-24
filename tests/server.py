# A local web server for the tests: static files from argv[1], plus a stand-in passkey service at POST /svc.
# Passkey 'service-pass'; POST /svc/fail {"on": true} makes it refuse to record a completed task.
# © Computational Classnotes · CC BY-NC-SA 4.0
import http.server, json, sys, functools
DONE = {}; STATE = {'fail_complete': False}; SEEN_STATIONS = set()
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    def do_OPTIONS(self): self.send_response(204); self.cors(); self.end_headers()
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        if 'station' in b: SEEN_STATIONS.add(b['station'])
        if self.path == '/svc/fail': STATE['fail_complete'] = b.get('on', False); out = {'ok': True}
        elif b.get('passkey') != 'service-pass': out = {'ok': False}
        elif b.get('action') == 'signin': out = {'ok': True, 'done': DONE.get(b['page'], [])}
        elif b.get('action') == 'complete':
            out = {'ok': False, 'message': 'stand-in refused'} if STATE['fail_complete'] else (DONE.setdefault(b['page'], []).append(b['task']) or {'ok': True})
        else: out = {'ok': False}
        d = json.dumps(out).encode(); self.send_response(200); self.cors(); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(d)
http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(H, directory=sys.argv[1])).serve_forever()
