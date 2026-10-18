# PulseLens status

Tick a task only when its acceptance checks in `BUILD_PLAN.md` pass. One line per task on what was done.

## Progress

### M1 Capture and probe (H0–6)
- [x] **M1.1 [all] Scaffold.** Makefile (via `scripts/dev.py`), `config.yaml` with typed loader, `.env.example`, FastAPI `/api/health`, Vite client with 3 pages, all §4/§5 JSON shapes as pydantic models with generated `types.ts`, `store.py` (folders + SQLite), `synth.py` skeleton, `.gitignore`. Checks: `make setup` ok, `make test` 27 passed, `make lint` clean, `/api/health` 200 (direct and through the Vite proxy), `npm run build` ok; extra: `make test-client` 2 passed, `make e2e` 3 passed.
- [ ] M1.2 [C] Session API and client WebSocket
- [ ] M1.3 [A] Capture page
- [ ] M1.4 [B] Vision base and light echo
- [ ] M1.5 [B] Analysis CLI
- [ ] GATE G1 (H6) [HUMAN]

### M2 Evidence checks (H6–18)
- [ ] M2.1 [A] Recorder page and superset mode
- [ ] M2.2 [A] Sensors and tilt prompt
- [ ] M2.3 [B] Motion check
- [ ] M2.4 [B] Capture integrity
- [ ] M2.5 [A+B] Hand pulse
- [ ] M2.6 [B] CLIP probe (cut if datasets not on disk by H6)
- [ ] M2.7 [A+B] Lens pulse
- [ ] M2.8 [B] Calibration
- [ ] M2.9 [C] Labels and separation report
- [ ] M2.10 [B] Physiology (only if ahead)
- [ ] GATE G2 (H14) [HUMAN + C]

### M3 Plan, decide, console (H18–28)
- [ ] M3.1 [C] Registry and planner
- [ ] M3.2 [C] Fusion, routing and reasons
- [ ] M3.3 [C] Live orchestrator
- [ ] M3.4 [A] Console
- [ ] M3.5 [C] Evidence chain and zip
- [ ] M3.6 [C] Rig radar demo
- [ ] GATE G3 (H24)

### M4 Measure (H28–38)
- [ ] M4.1 [C] Splits
- [ ] M4.2 [B] Calibrate on set A
- [ ] M4.3 [C] Freeze and run the policies
- [ ] M4.4 [C] Slices and intervals
- [ ] GATE G4 (H38)

### M5 Polish and rehearse (H38–48)
- [ ] M5.1 [A+C] Demo mode
- [ ] M5.2 [A] Robustness
- [ ] M5.3 [C] README
- [ ] M5.4 [C] Purge script
- [ ] M5.5 [HUMAN] Rehearsals

## Needs a human

1. **Create `.env`** on each machine that runs the server: `cp .env.example .env`, then set `PULSE_HMAC_SECRET` to the output of `python -c "import secrets; print(secrets.token_hex(32))"`, pick a `CONSOLE_PASSCODE`, and list the team's person codes in `TEAM_CODES`. Needed before M1.2's WebSocket signing runs outside tests.
2. **Write `docs/consent_form.md`** (BUILD_PLAN section 0 and 5). It is referenced by the plan but doesn't exist yet. It needs a human: it is a consent document for volunteers and must state the purge date. Print 20 copies.
3. **Windows teammates:** install GNU make with `winget install ezwinports.make` and open a new terminal, or skip make and run `python scripts/dev.py <target>`. Install `uv` (`winget install astral-sh.uv`) so `make setup` can fetch Python 3.11 by itself; without uv it uses whichever Python runs the script and warns if it isn't 3.11.
4. **Install cloudflared** for `make tunnel` (`winget install Cloudflare.cloudflared`, `brew install cloudflared`) and test a quick tunnel from a phone on mobile data (BUILD_PLAN section 0).
5. **Before-event items still open** from BUILD_PLAN section 0: dataset access requests (FaceForensics++, Celeb-DF v2), devices, attack laptop setup, the paper name-to-code sheet.

## Decisions

- **M1.1:** `client/src/shared/types.ts` is generated from `models.py` (`make types`), and `test_types_sync.py` fails if it is stale. Reason: three tracks edit shared shapes in parallel; a generator removes drift.
- **M1.1:** `models.py` already holds every JSON shape from SPEC §4 and §5 (bundle records, REST bodies, WebSocket messages), not just §4.6, so tracks A, B and C build against one contract from the first hour.
- **M1.1:** added `client.accessibility_route` (bool, default false) to `meta.json`; SPEC §6.1 step 7 and §10 use it but §4.2 had no field. SPEC updated.
- **M1.1:** `make setup` installs `[dev,vision]` extras (mediapipe, scipy, matplotlib). ArcFace and CLIP deps (`[ml]`: torch, insightface, open_clip) are opt-in with `make setup-ml`, because they are large and insightface may need a C++ toolchain on Windows. mediapipe brings `opencv-contrib-python`; never add a second OpenCV package (they overwrite each other's `cv2`).
- **M1.1:** `fetch_models.py` also downloads `blaze_face_short_range.tflite` for the client coaching FaceDetector (SPEC §6.4), so the capture page doesn't depend on a CDN at the venue. It writes `models/MANIFEST.json` with sha256 per file.

## Device log (gate G1)

| Device | Browser | clock_source | captureTime? | Camera capabilities | Gyro permission | fps | Echo on ≥ 6/8? |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Tool versions (attack recordings)

| Tool | Version | Notes |
|---|---|---|
| | | |
