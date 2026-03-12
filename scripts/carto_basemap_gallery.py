"""Local CARTO basemap gallery.

This script is intentionally outside the deployed app. It serves a small local
Leaflet page so you can inspect the supported CARTO raster basemap styles side
by side without touching the frontend deployment.

Usage:
  python scripts/carto_basemap_gallery.py
  python scripts/carto_basemap_gallery.py --no-open
  python scripts/carto_basemap_gallery.py --check-only
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from textwrap import dedent
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

BASEMAP_STYLES = [
    "light_all",
    "dark_all",
    "light_nolabels",
    "light_only_labels",
    "dark_nolabels",
    "dark_only_labels",
    "rastertiles/voyager",
    "rastertiles/voyager_nolabels",
    "rastertiles/voyager_only_labels",
    "rastertiles/voyager_labels_under",
]

ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors '
    '&copy; <a href="https://carto.com/attributions">CARTO</a>'
)
TILE_URL_TEMPLATE = "https://{s}.basemaps.cartocdn.com/{style}/{z}/{x}/{y}{r}.png"
PREVIEW_TILE_COORDS = {"z": 12, "x": 1206, "y": 1540}
DEFAULT_CENTER = {"lat": 42.3601, "lng": -71.0589, "zoom": 12}


def build_tile_url(style: str) -> str:
    return TILE_URL_TEMPLATE.format(
        s="a",
        style=style,
        z=PREVIEW_TILE_COORDS["z"],
        x=PREVIEW_TILE_COORDS["x"],
        y=PREVIEW_TILE_COORDS["y"],
        r="",
    )


def check_styles() -> int:
    print("Checking sample CARTO tiles:\n")
    failures = 0
    for style in BASEMAP_STYLES:
        url = build_tile_url(style)
        request = urllib.request.Request(url, headers={"User-Agent": "crime-map-carto-gallery/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            status = exc.code
            content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        except urllib.error.URLError as exc:
            failures += 1
            print(f"[ERR] {style}\n      {exc.reason}\n      {url}\n")
            continue

        if status >= 400:
            failures += 1
            prefix = "BAD"
        else:
            prefix = "OK "

        print(f"[{prefix}] {style}\n      {status} {content_type}\n      {url}\n")

    return 1 if failures else 0


def build_html() -> str:
    styles_json = json.dumps(BASEMAP_STYLES)
    center_json = json.dumps(DEFAULT_CENTER)
    tile_url_template_json = json.dumps(TILE_URL_TEMPLATE)
    return dedent(
        f"""\
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>CARTO Basemap Gallery</title>
            <link
              rel="stylesheet"
              href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
              integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
              crossorigin=""
            />
            <style>
              :root {{
                color-scheme: light;
                --bg: #edf2f6;
                --panel: rgba(255, 255, 255, 0.92);
                --panel-line: rgba(24, 38, 52, 0.12);
                --ink: #16222d;
                --muted: #576675;
                --accent: #245b7b;
              }}

              * {{
                box-sizing: border-box;
              }}

              body {{
                margin: 0;
                font-family: "IBM Plex Sans", system-ui, sans-serif;
                color: var(--ink);
                background:
                  radial-gradient(circle at top left, rgba(71, 107, 134, 0.14), transparent 22%),
                  linear-gradient(180deg, #f8fafc 0%, var(--bg) 54%, #e3eaf1 100%);
              }}

              main {{
                width: min(1600px, calc(100vw - 32px));
                margin: 0 auto;
                padding: 24px 0 32px;
              }}

              header {{
                margin-bottom: 18px;
                padding-bottom: 16px;
                border-bottom: 1px solid var(--panel-line);
              }}

              h1 {{
                margin: 0 0 8px;
                font-size: clamp(2rem, 4vw, 3.2rem);
                line-height: 0.95;
                letter-spacing: -0.05em;
              }}

              p {{
                margin: 0;
                color: var(--muted);
                line-height: 1.6;
              }}

              code {{
                font-family: "IBM Plex Mono", ui-monospace, monospace;
                font-size: 0.92em;
              }}

              .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
                gap: 18px;
              }}

              .card {{
                overflow: hidden;
                border: 1px solid var(--panel-line);
                border-radius: 12px;
                background: var(--panel);
                box-shadow: 0 18px 36px rgba(27, 45, 62, 0.1);
              }}

              .card-copy {{
                padding: 14px 16px 12px;
                border-bottom: 1px solid var(--panel-line);
              }}

              .style-name {{
                margin: 0 0 8px;
                font-size: 0.82rem;
                font-weight: 700;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: var(--accent);
              }}

              .style-url {{
                display: block;
                overflow-wrap: anywhere;
                color: var(--ink);
              }}

              .map {{
                width: 100%;
                height: 260px;
                background: #e7edf2;
              }}

              .footer {{
                margin-top: 18px;
                font-size: 0.92rem;
              }}

              @media (max-width: 640px) {{
                main {{
                  width: min(100vw - 20px, 1600px);
                  padding-top: 18px;
                }}

                .map {{
                  height: 220px;
                }}
              }}
            </style>
          </head>
          <body>
            <main>
              <header>
                <h1>CARTO Raster Basemap Gallery</h1>
                <p>Standalone local viewer. Not used by the deployed crime map.</p>
                <p>Each panel uses the exact style string shown below it.</p>
              </header>

              <section class="grid" id="gallery"></section>

              <p class="footer">
                Tile pattern:
                <code>{TILE_URL_TEMPLATE}</code>
              </p>
            </main>

            <script
              src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
              integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
              crossorigin=""
            ></script>
            <script>
              const styles = {styles_json};
              const center = {center_json};
              const attribution = {json.dumps(ATTRIBUTION)};
              const tileUrlTemplate = {tile_url_template_json};
              const gallery = document.getElementById("gallery");

              styles.forEach((style, index) => {{
                const card = document.createElement("article");
                card.className = "card";

                const copy = document.createElement("div");
                copy.className = "card-copy";

                const title = document.createElement("p");
                title.className = "style-name";
                title.textContent = style;

                const url = document.createElement("code");
                url.className = "style-url";
                url.textContent = tileUrlTemplate.replace("{{style}}", style);

                copy.appendChild(title);
                copy.appendChild(url);

                const mapNode = document.createElement("div");
                mapNode.className = "map";
                mapNode.id = "map-" + index;

                card.appendChild(copy);
                card.appendChild(mapNode);
                gallery.appendChild(card);

                const map = L.map(mapNode.id, {{
                  zoomControl: true,
                  attributionControl: true,
                }}).setView([center.lat, center.lng], center.zoom);

                L.tileLayer(
                  tileUrlTemplate.replace("{{style}}", style),
                  {{ attribution, maxZoom: 20 }}
                ).addTo(map);
              }});
            </script>
          </body>
        </html>
        """
    )


class GalleryHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        if self.path not in {"/", "/index.html"}:
            self.send_error(404)
            return

        payload = build_html().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a local CARTO basemap gallery.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind. Default: 8765")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open a browser automatically after starting the server.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Fetch one sample tile per style and print the status instead of starting the gallery.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check_only:
        return check_styles()

    server = ThreadingHTTPServer((args.host, args.port), GalleryHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"Serving CARTO basemap gallery at {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
