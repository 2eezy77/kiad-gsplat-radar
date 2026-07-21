# Real-time geospatial traffic visualization (KIAD)

**Author:** Jose I. Montero

A browser-based **real-time 3D visualization** system using aviation traffic around
**Washington Dulles (KIAD)** as the problem domain. It combines CesiumJS geospatial
rendering, Google Photorealistic 3D Tiles, a live ADS-B ingest pipeline, layered
airspace/procedure overlays, and a small UI for camera presets and conflict cues.

Built on [CesiumJS](https://cesium.com/platform/cesiumjs/) with a tiny Python proxy that
streams live ADS-B traffic to the client.

![KIAD scene — tower view of finals and ILS](docs/kiad-atc-ui.jpg)

*Oblique camera over KIAD with ILS approach funnels, live traffic, and overlay panels.
Photorealistic 3D tiles and Cesium terrain require `CESIUM_TOKEN` and `GOOGLE_KEY` in a local `.env` — see [Configuration](#configuration--api-keys).*

### Screenshots

| | |
|:--|:--|
| ![Final approach / ILS descent](docs/kiad-final-approach.jpg) | ![Class B upside-down cake](docs/kiad-class-b-cake.jpg) |
| *Aircraft on final with 3° ILS approach geometry* | *Shelved Class B “upside-down cake” rings* |
| ![Overlay layers panel](docs/kiad-layers.jpg) | ![Helicopters and mixed types](docs/kiad-aircraft-variety.jpg) |
| *Overlay Layers toggles (runways, ILS, Class B/D, traffic)* | *Helicopters and mixed airframe types around the field* |

---

## Features

- **Live data pipeline** — aircraft within 50 nm of KIAD, refreshed every 5 seconds, drawn as
  type-matched 3D models (Flightradar24 open GLB models).
- **Camera / layer presets** — switch viewpoint and visible layers for different ops views:
  - **RADAR · TRACON** — top-down, full Class B, all traffic
  - **TWR · Local** — oblique tower view, Class D + ILS finals
  - **GND · Surface** — overhead surface view of the airport
- **Geospatial overlays** — three parallel runways (01L/C/R ↔ 19R/C/L), ILS
  approach funnels and centerlines, shelved Class B rings, Class D, and arrival/departure routes.
- **Rule-based conflict cues** — flags loss of separation per FAA JO 7110.65
  (3 nm / 1000 ft radar separation, runway separation, and wake-turbulence advisories) with an
  on-screen banner and conflict lines between affected pairs.
- **Layered UI** — toggle individual overlay layers on/off.
- **Photorealistic base map** — Google Photorealistic 3D Tiles with automatic fallback to
  OpenStreetMap + Cesium World Terrain + Ion OSM buildings if unavailable.
- **Mobile support** — works on iPhone with a touch-friendly floating panel UI.
- **Cost-aware tile loading** — pauses tile requests when the window loses focus and throttles
  loads based on camera movement to limit Google Tiles usage.

## Tech stack

| Layer      | Technology                                                              |
| ---------- | ----------------------------------------------------------------------- |
| Rendering  | CesiumJS 1.115, Google Photorealistic 3D Tiles, Cesium Ion              |
| Live feed  | [adsb.lol](https://adsb.lol) (ADS-B Exchange feed) → OpenSky fallback   |
| 3D models  | Flightradar24 open-source GLB aircraft models                           |
| Backend    | Python 3.11 standard library (`http.server`) — static host + CORS proxy |
| Frontend   | Single self-contained `index.html` (no build step)                      |

## Project structure

```
index.html      Single-page app — Cesium scene, overlays, domain logic, UI
server.py       Static file server + /api/aircraft proxy (adsb.lol → OpenSky)
.env.example    Placeholder env vars (CESIUM_TOKEN, GOOGLE_KEY, optional PORT)
docs/           README screenshots
Procfile        Process definition for deployment (web: python3 server.py)
runtime.txt     Python version pin (python-3.11)
```

## Running locally

Requires **Python 3.11+**. No dependencies to install — the server uses only the standard library.

```bash
python3 server.py
```

Then open <http://localhost:8080> (or the `PORT` from your `.env`, often `8877`).

For a clean demo framing (tower view, conflict banner suppressed):

```text
http://localhost:8877/?portfolio=1
```

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

Copy `.env.example` to `.env` and fill in placeholders (`.env` is git-ignored):

```bash
cp .env.example .env
```

```env
CESIUM_TOKEN=your-cesium-ion-token
GOOGLE_KEY=your-google-maps-tiles-key
```

Restrict the Google key by HTTP referrer in the Google Cloud console, and treat both keys as
public once deployed (they are served to the browser). Rotate them if they are ever exposed.

## Notes

- Runway thresholds and ILS geometry are derived from FAA NASR data.
- Separation logic is an **educational visualization**, not an operational air-traffic tool, and must not
  be used for real traffic decisions.

## License

MIT — see [LICENSE](LICENSE).

---

*Real-time geospatial viz demo — aviation as the domain.*
