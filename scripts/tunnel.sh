#!/usr/bin/env bash
# HTTPS quick tunnel to the Vite dev server, so phones get camera and motion-sensor access.
# Same as `make tunnel`. Open the printed https://*.trycloudflare.com URL on the phone.
set -euo pipefail
command -v cloudflared >/dev/null || { echo "Install cloudflared first"; exit 1; }
exec cloudflared tunnel --url http://localhost:5173
