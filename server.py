#!/usr/bin/env python3
"""Local dev server with CORS proxy for aircraft data."""
import http.server, urllib.request, json, os

# KIAD: 38.9445°N 77.4558°W — query 50nm radius
KIAD_LAT, KIAD_LON, RADIUS_NM = 38.9445, -77.4558, 50

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/aircraft"):
            self.proxy_aircraft()
        elif self.path in ("/", "/index.html"):
            self.serve_index()
        else:
            super().do_GET()

    def serve_index(self):
        """Serve index.html, injecting API keys from the environment at request time."""
        try:
            with open("index.html", "rb") as f:
                html = f.read().decode("utf-8")
        except OSError:
            self.send_error(404)
            return
        html = html.replace("__CESIUM_TOKEN__", os.environ.get("CESIUM_TOKEN", ""))
        html = html.replace("__GOOGLE_KEY__", os.environ.get("GOOGLE_KEY", ""))
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def proxy_aircraft(self):
        try:
            filtered = self._fetch_adsbx()
        except Exception as e1:
            # Fallback to OpenSky if adsb.lol fails
            try:
                filtered = self._fetch_opensky()
            except Exception as e2:
                self._send_json(502, {"error": f"adsbx: {e1}  opensky: {e2}"})
                return
        self._send_json(200, filtered)

    def _fetch_adsbx(self):
        """adsb.lol — ADS-B Exchange community feed, no auth, no rate limit."""
        url = f"https://api.adsb.lol/v2/lat/{KIAD_LAT}/lon/{KIAD_LON}/dist/{RADIUS_NM}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = json.loads(r.read())

        # adsb.lol format: {"ac": [{hex, flight, lat, lon, alt_baro, gs, track,
        #   baro_rate, squawk, type, r, t, on_ground, ...}, ...]}
        filtered = {}
        for ac in (raw.get("ac") or []):
            icao     = (ac.get("hex") or "").lower()
            callsign = (ac.get("flight") or "").strip()
            lat      = ac.get("lat")
            lon      = ac.get("lon")
            if lat is None or lon is None:
                continue
            alt_raw  = ac.get("alt_baro", 0)
            alt_ft   = 0 if alt_raw == "ground" else (int(alt_raw) if alt_raw else 0)
            speed_kt = round(ac.get("gs") or 0)
            heading  = round(ac.get("track") or 0)
            vrate    = round(ac.get("baro_rate") or 0)
            squawk   = ac.get("squawk") or ""
            ac_type  = ac.get("t") or ""
            reg      = ac.get("r") or ""
            on_ground= 1 if (alt_raw == "ground" or ac.get("on_ground")) else 0

            filtered[icao] = [
                icao, lat, lon, heading, alt_ft, speed_kt,
                squawk, "N/A", ac_type, reg, 0, "", "", callsign,
                on_ground, vrate, callsign
            ]
        return filtered

    def _fetch_opensky(self):
        """OpenSky Network fallback."""
        SOUTH, NORTH, WEST, EAST = 38.11, 39.78, -78.53, -76.39
        url = (f"https://opensky-network.org/api/states/all"
               f"?lamin={SOUTH}&lomin={WEST}&lamax={NORTH}&lomax={EAST}")
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = json.loads(r.read())

        filtered = {}
        for s in (raw.get("states") or []):
            icao     = s[0] or ""
            callsign = (s[1] or "").strip()
            lon      = s[5]; lat = s[6]; baro_m = s[7]
            on_ground= s[8]; speed_ms = s[9]; heading = s[10]; vrate_ms = s[11]
            squawk   = s[14] or ""
            if lat is None or lon is None:
                continue
            alt_ft   = round(baro_m * 3.28084) if baro_m else 0
            speed_kt = round(speed_ms * 1.94384) if speed_ms else 0
            vrate    = round(vrate_ms * 196.85) if vrate_ms else 0
            filtered[icao] = [
                icao, lat, lon, round(heading or 0), alt_ft, speed_kt,
                squawk, "N/A", "", "", 0, "", "", callsign,
                1 if on_ground else 0, vrate, callsign
            ]
        return filtered

    def _send_json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        if not self.path.startswith("/api"):
            super().log_message(fmt, *args)

def load_dotenv(path=".env"):
    """Load KEY=VALUE pairs from a local .env file (git-ignored) if present.
    Does not override variables already set in the environment."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv()
    port = int(os.environ.get("PORT", 8080))
    print(f"Server running at http://localhost:{port}")
    http.server.HTTPServer(("", port), Handler).serve_forever()
