#!/usr/bin/env python3
"""Local dev server with CORS proxy for aircraft data."""
import http.server, urllib.request, json, os

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/aircraft"):
            self.proxy_aircraft()
        else:
            super().do_GET()

    def proxy_aircraft(self):
        try:
            bounds = "39.79,38.12,-76.38,-78.53"  # 50nm radius around KIAD
            url = f"https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds={bounds}&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=5) as r:
                data = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, fmt, *args):
        if not self.path.startswith("/api"):
            super().log_message(fmt, *args)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Server running at http://localhost:8080")
    http.server.HTTPServer(("", 8080), Handler).serve_forever()
