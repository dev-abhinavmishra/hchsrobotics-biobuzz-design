# serve.py — local dev server for the viewer.
# `python -m http.server` lets the browser heuristically cache JS modules, which
# causes stale-code errors during development. This adds no-store headers.
# Usage:  python serve.py [port]   (default 8017)
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, *a):  # quiet
        pass

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8017
ThreadingHTTPServer(('127.0.0.1', port), NoCache).serve_forever()
