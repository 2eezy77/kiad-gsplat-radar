# KIAD ATC Visualization

A browser-based 3D air-traffic-control view of **Washington Dulles International Airport (KIAD)**.
It renders live aircraft over Google Photorealistic 3D Tiles and overlays the runway
environment, ILS approaches, Class B/D airspace, and FAA-style separation-conflict detection.

Built on [CesiumJS](https://cesium.com/platform/cesiumjs/) with a tiny Python proxy that
streams live ADS-B traffic.

---

## Features

- **Live traffic** — aircraft within 50 nm of KIAD, refreshed every 5 seconds, drawn as
  type-matched 3D models (Flightradar24 open GLB models).
- **Three ATC positions** — switch camera + visible layers to match a controller's job:
  - 📡 **RADAR · TRACON** — top-down, full Class B, all traffic
  - 🗼 **TWR · Local Control** — oblique tower view, Class D + ILS finals
  - 🛬 **GND · Ground Control** — overhead surface view of the airport
- **Airspace & procedures overlays** — three parallel runways (01L/C/R ↔ 19R/C/L), ILS
  approach funnels and centerlines, shelved Class B rings, Class D, and arrival/departure routes.
- **Separation-conflict detection** — flags loss of separation per FAA JO 7110.65
  (3 nm / 1000 ft radar separation, runway separation, and wake-turbulence advisories) with an
  on-screen banner and conflict lines between affected pairs.
- **Interactive legend** — toggle individual overlay layers on/off.
- **Photorealistic base map** — Google Photorealistic 3D Tiles with automatic fallback to
  OpenStreetMap + Cesium World Terrain + Ion OSM buildings if unavailable.
- **Mobile support** — works on iPhone with a touch-friendly floating panel UI.
- **Cost-aware tile loading** — pauses tile requests when the window loses focus and throttles
  loads based on camera movement to limit Google Tiles usage.

## Tech stack

| Layer      | Technology                                                              |
| ---------- | ----------------------------------------------------------------------- |
| Rendering  | CesiumJS 1.115, Google Photorealistic 3D Tiles, Cesium Ion              |
| Aircraft   | [adsb.lol](https://adsb.lol) (ADS-B Exchange feed) → OpenSky fallback   |
| 3D models  | Flightradar24 open-source GLB aircraft models                           |
| Backend    | Python 3.11 standard library (`http.server`) — static host + CORS proxy |
| Frontend   | Single self-contained `index.html` (no build step)                      |

## Project structure

```
index.html    Single-page app — Cesium scene, overlays, ATC logic, UI
server.py     Static file server + /api/aircraft proxy (adsb.lol → OpenSky)
Procfile      Process definition for deployment (web: python3 server.py)
runtime.txt   Python version pin (python-3.11)
```

## Running locally

Requires **Python 3.11+**. No dependencies to install — the server uses only the standard library.

```bash
python3 server.py
```

Then open <http://localhost:8080>.

The server listens on `PORT` if set (defaults to `8080`) and proxies live aircraft data at
`/api/aircraft`, so the browser is never blocked by CORS.

## How aircraft data works

`server.py` exposes `GET /api/aircraft`, which:

1. Queries **adsb.lol** for a 50 nm radius around KIAD (no auth, no rate limit).
2. Falls back to **OpenSky Network** (bounding-box query) if adsb.lol is unavailable.
3. Normalizes both sources into a single compact JSON shape the frontend consumes.

The frontend polls this endpoint every 5 seconds while the tab is active.

## Deployment

Configured for Railway / Heroku-style platforms via the `Procfile` and `runtime.txt`.
The `web` process runs `python3 server.py`, and the app binds to the platform-provided `PORT`.

## Configuration & API keys

The app needs a **Cesium Ion token** and a **Google Maps Tiles API key**. These are **not**
stored in the repo — `server.py` injects them into `index.html` at request time from environment
variables, so no secrets are committed.

Provide them either as real environment variables or via a git-ignored `.env` file in the project
root:

```env
CESIUM_TOKEN=your-cesium-ion-token
GOOGLE_KEY=your-google-maps-tiles-key
```

Restrict the Google key by HTTP referrer in the Google Cloud console, and treat both keys as
public once deployed (they are served to the browser). Rotate them if they are ever exposed.

## Notes

- Runway thresholds and ILS geometry are derived from FAA NASR data.
- Separation logic is an **educational visualization**, not an operational ATC tool, and must not
  be used for real air-traffic decisions.

---

*KIAD ATC Visualization — a personal aviation dataviz project.*
