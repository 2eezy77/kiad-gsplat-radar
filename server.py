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
            # KIAD ~50nm bounding box
            SOUTH, NORTH, WEST, EAST = 38.11, 39.78, -78.53, -76.39
            # OpenSky Network — bbox actually works, no auth required for public data
            url = f"https://opensky-network.org/api/states/all?lamin={SOUTH}&lomin={WEST}&lamax={NORTH}&lomax={EAST}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = json.loads(r.read())

            # OpenSky format: states = list of [icao24, callsign, origin_country,
            #   time_position, last_contact, longitude, latitude, baro_altitude,
            #   on_ground, velocity, true_track, vertical_rate, sensors,
            #   geo_altitude, squawk, spi, position_source]
            # Convert to FR24-compatible format:
            # [icao, lat, lon, heading, alt_ft, speed, squawk, ...]
            filtered = {}
            for s in (raw.get("states") or []):
                icao     = s[0] or ""
                callsign = (s[1] or "").strip()
                lon      = s[5]
                lat      = s[6]
                baro_m   = s[7]   # meters, None if unknown
                on_ground= s[8]
                speed_ms = s[9]   # m/s
                heading  = s[10]  # degrees
                vrate_ms = s[11]  # m/s
                squawk   = s[14] or ""

                if lat is None or lon is None:
                    continue
                alt_ft   = round(baro_m * 3.28084) if baro_m else 0
                speed_kt = round(speed_ms * 1.94384) if speed_ms else 0
                vrate_fpm= round(vrate_ms * 196.85) if vrate_ms else 0

                # FR24-compatible array: [icao,lat,lon,heading,alt_ft,speed,squawk,
                #   radar,ac_type,reg,ts,origin,dest,flight,on_ground,vspeed,callsign]
                filtered[icao] = [
                    icao, lat, lon, round(heading or 0), alt_ft, speed_kt,
                    squawk, "N/A", "", "", 0, "", "", callsign,
                    1 if on_ground else 0, vrate_fpm, callsign
                ]

            data = json.dumps(filtered).encode()
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
    port = int(os.environ.get("PORT", 8080))
    print(f"Server running at http://localhost:{port}")
    http.server.HTTPServer(("", port), Handler).serve_forever()
