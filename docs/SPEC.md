# PulseLens prototype: technical spec

This is the contract for the build. `BUILD_PLAN.md` says in what order to build it. If code and this spec disagree, fix one of them in the same commit.

---

## 1. Scope

**Built in the 48 hours**
- Browser capture page for mobile and desktop browsers: capability probe, coaching, frame capture with per-frame timestamps, motion-sensor log
- Pulses: light (all channels), motion tilt (phones and tablets), hand pass with head turn (all), lens (only where the browser exposes camera controls)
- Checks in four families: optical, motion, capture integrity, content. Physiology is behind a flag (stretch goal, gate G3).
- Per-profile calibration, adaptive planner (passive first, friction cap), family-level fusion and routing
- Agent and auditor console: live status, plain-language reasons, "Fire a pulse", approve or escalate, evidence pack with a hash chain
- Fixed-vs-adaptive evaluation harness on recorded sessions
- Rig radar shown with clearly labelled synthetic data only

**Out of scope (roadmap, say so if asked)**
- Native Android and iOS SDKs with device attestation (Play Integrity, App Attest)
- Lens pulse on browsers that don't expose camera controls
- Real rig radar on production data; retro-scan of past V-CIP recordings
- Integration with a real V-CIP vendor (prototype uses its own capture page)

---

## 2. Architecture

```
Applicant browser (client/)                 PulseLens service (server/)                  Console (client/console)
-----------------------------               ------------------------------               ------------------------
probe + coach  ── POST /probe ───────────►  sessions API + store (SQLite + files)  ◄──── REST + WS /ws/console
frame grabber  ── POST /frames (batches) ─► analysis worker (process pool)               live status, reasons,
sensor log     ── POST /sensors ─────────►    checks/* → CheckResult                     Fire a pulse, decide
pulse executor ◄── WS pulse (just in time)  orchestrator (per session)
               ── WS pulse_ack ──────────►    planner → fusion → route
                                            evidence chain, radar (synthetic)
```

All echo timing uses the client's `performance.now()` clock. The server never compares its own clock with client times.

---

## 3. Repo layout

```
CLAUDE.md
Makefile                     # thin aliases over scripts/dev.py (also runnable without make)
config.yaml                  # loaded and validated by pulselens/config.py (unknown keys rejected)
ruff.toml
.env.example                 # PULSE_HMAC_SECRET, CONSOLE_PASSCODE
docs/  SPEC.md  BUILD_PLAN.md  STATUS.md  consent_form.md
client/
  index.html                 # applicant capture page
  record.html                # operator page for labelled recording sessions
  console.html               # agent and auditor console
  src/shared/types.ts        # GENERATED from server models (make types)
  src/shared/{clock,api}.ts  # clock.now() is the one client clock; ESLint bans Date.now() in capture code
  src/capture/{probe,coach,grabber,sensors,session,ui}.ts
  src/capture/pulses/{light,lens,tilt,hand}.ts
  src/console/{main,session_view,timeline}.ts
  tests/                     # vitest unit tests, Playwright e2e
server/
  pulselens/
    api/{main,sessions,console,ws}.py
    models.py  tsgen.py  store.py  config.py  cli.py  orchestrator.py  fusion.py  reasons.py  evidence.py  radar.py
    vision/{models,frames,face,hand,flow,arcface,clip}.py
    checks/{base,optical_light,optical_lens,motion_tilt,capture,content_clip,content_hand,physiology_pos}.py
    planner/{registry,planner}.py   planner/policy.yaml
    calibration/{profiles,thresholds}.py   calibration/bootstrap.yaml
    train/clip_probe.py
  tests/  fixtures/synth.py  test_*.py
eval/  split.py  freeze.py  run.py  report.py  separation.py  labels.csv  people.csv
scripts/  dev.py  gen_types.py  fetch_models.py  seed_radar_demo.py  purge_volunteers.py  verify_evidence.py  tunnel.sh
data/  (gitignored)  sessions/<session_id>/...
models/ (gitignored)  face_landmarker.task  hand_landmarker.task  clip_probe.joblib  insightface/
```

---

## 4. Data model

### 4.1 Session bundle on disk: `data/sessions/<session_id>/`

| File | Content |
|---|---|
| `meta.json` | session info, probe, claimed and measured profile, plan, label (see 4.2) |
| `frames/000000.jpg ...` | JPEG frames, 640x480 max (480x360 on phones), quality 0.92 |
| `frames.jsonl` | one line per frame (4.3) |
| `pulses.jsonl` | one line per pulse or prompt (4.4) |
| `sensors.jsonl` | one line per `devicemotion` event (4.5) |
| `events.jsonl` | coaching tips, prompts, errors, reconnects |
| `results.json` | check results, family results, coverage, route, reasons (4.6) |
| `chain.json` | evidence hash chain (section 13) |

### 4.2 `meta.json`

```json
{
  "session_id": "s_20261024_143012_ab12",
  "created_server_iso": "2026-10-24T14:30:12+05:30",
  "mode": "live | superset",
  "product": "instant_loan | savings_account",
  "client": {
    "user_agent": "...", "ua_mobile": true, "pointer_coarse": true,
    "screen": {"w": 412, "h": 915, "dpr": 2.6},
    "camera_label": "Front Camera", "track_settings": {"width": 640, "height": 480, "frameRate": 30},
    "track_capabilities": {"exposureCompensation": {"min": -2, "max": 2, "step": 0.33}},
    "has_rvfc": true, "clock_source": "captureTime | rvfc_now | raf",
    "gyro": {"available": true, "permission": "granted | denied | not_needed"},
    "webgl_renderer": "...", "webdriver": false,
    "accessibility_route": false
  },
  "probe": {"face_frac": 0.11, "luma_mean": 132, "blur_lapvar": 210, "backlit": false, "fps_measured": 29.6, "coaching_rounds": 1},
  "profile_claimed": "mobile_browser|ge27",
  "profile_measured": "mobile_browser|ge27",
  "plan": {"rounds": [["capture", "content_clip", "tilt", "light"]], "route_hint": null, "active_seconds": 12},
  "label": {"person": "P07", "device": "D03", "light": "normal | dim", "kind": "genuine | attack",
            "attack_tool": null, "consent_ref": "C07", "skin_tone_mst": null, "set": "A | B"}
}
```

`client.accessibility_route` is true when the applicant opted out of bright flashes (6.1 step 7).

`label` is filled only for recorder-mode sessions. `skin_tone_mst` is an optional self-reported Monk Skin Tone band, never inferred.

### 4.3 `frames.jsonl`

```json
{"i": 412, "t": 18233.41, "capture_time": 18201.9, "presented_frames": 415, "media_time": 13.73, "w": 480, "h": 360, "file": "000412.jpg"}
```
`t` is the canonical frame time: `capture_time` if present, else the rVFC `now`, else the rAF time. `meta.client.clock_source` says which.

### 4.4 `pulses.jsonl`

```json
{"pulse_id": "p_9f3", "kind": "light", "source": "planner | agent | superset",
 "params": {"colour": "red", "duration_ms": 400, "region": "fullscreen | border"},
 "released_server_iso": "...", "received": 20011.2, "applied": 20012.0, "painted": 20027.9, "ended": 20428.3,
 "ok": true, "error": null, "sig": "hex"}
```
For prompts (`kind: "tilt" | "hand"`), `painted` is when the prompt became visible and `ended` when its timer ran out.
For `kind: "lens"`, `params` holds the constraint (for example `{"exposureCompensation": 1.0}`), `applied` is just before `applyConstraints()` and `painted` is when its promise resolved.

### 4.5 `sensors.jsonl`

```json
{"t": 20110.5, "rr": [0.4, 12.9, -3.1], "acc": [0.1, 9.7, 0.4], "interval": 16}
```
`rr` is `rotationRate` as `[alpha, beta, gamma]`. Units vary across devices; the motion check uses correlation, which ignores scale.

### 4.6 `CheckResult` and session results (pydantic, mirrored in TS)

Every JSON shape in sections 4 and 5 (bundle records, REST bodies, WebSocket messages) is a pydantic model in `server/pulselens/models.py`. `client/src/shared/types.ts` is generated from it with `make types`; `tests/test_types_sync.py` fails if the committed file is stale. `results.json` is `SessionResults {checks, families, decision}`. `CheckResult.abstain(...)` builds an abstaining result (rule: checks never throw).

```python
class CheckResult(BaseModel):
    check_id: str            # e.g. "optical.light.delay"
    unit: str                # planning unit, e.g. "light"
    family: Literal["optical", "motion", "capture", "content", "physiology"]
    status: Literal["pass", "fail", "abstain"]
    score: float | None      # higher = more suspicious
    threshold: float | None
    threshold_source: Literal["profile", "channel", "bootstrap", "rule"] | None
    quality: float           # 0..1
    features: dict[str, float]
    reason: str              # plain language, shown to the agent
    evidence_frames: list[int] = []

class FamilyResult(BaseModel):
    family: str
    status: Literal["pass", "fail", "abstain"]
    checks: list[str]

class SessionDecision(BaseModel):
    route: Literal["PASS", "ADD_CHECKS", "AGENT_CHALLENGE", "ASSISTED_KYC", "HOLD"]
    coverage: dict[str, list[str]]     # threat -> families with a strong pass
    failed_families: list[str]
    reasons: list[str]
    needs_human: bool
    provisional_thresholds: bool
```

---

## 5. Server API

All applicant endpoints return applicant-safe payloads only: `{"state": "continue | retry | assisted | under_review", "message": "..."}`. No scores, no check names.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/sessions` | `{mode, product, client}` | `{session_id, ws_url}` |
| POST | `/api/sessions/{id}/probe` | probe result | `{tips: [...], state}` |
| POST | `/api/sessions/{id}/frames` | multipart: `meta` (JSON lines) + JPEG parts | `{received}` |
| POST | `/api/sessions/{id}/sensors` | JSON lines | `{received}` |
| POST | `/api/sessions/{id}/finalize` | `{}` | applicant-safe state |
| GET | `/api/console/sessions` | | list with route and state |
| GET | `/api/console/sessions/{id}` | | meta, plan, results, decision, pulse timeline |
| POST | `/api/console/sessions/{id}/fire` | `{kind: "light" | "tilt"}` | `{pulse_id}` |
| POST | `/api/console/sessions/{id}/decision` | `{action: "approve" | "escalate" | "assisted", note}` | updated decision |
| GET | `/api/console/sessions/{id}/evidence.zip` | | zip (section 13) |

Console endpoints need header `X-Console-Passcode` (prototype-level access control; say so in the UI footer).

### WebSocket `/ws/client/{session_id}`

Server to client:
- `{"type": "prompt", "kind": "coach | tilt | hand | info", "text": "...", "duration_ms": 2500, "prompt_id": "..."}`
- `{"type": "pulse", "pulse_id": "...", "kind": "light | lens", "params": {...}, "expires_in_ms": 300, "sig": "..."}`
- `{"type": "done", "state": "...", "message": "..."}`

Client to server:
- `{"type": "pulse_ack", "pulse_id", "received", "applied", "painted", "ended", "ok", "error"}`
- `{"type": "prompt_ack", "prompt_id", "painted", "ended"}`
- `{"type": "heartbeat", "t"}`

Pulses are released one at a time at their scheduled moment, never as a schedule up front. A pulse not applied within `expires_in_ms` is logged `ok:false` and its echo abstains. `sig = HMAC_SHA256(PULSE_HMAC_SECRET, pulse_id|kind|params_json|session_id)`; the server rejects acks for unknown, expired or already-acked pulse IDs.

### WebSocket `/ws/console`

Server pushes `{"type": "session_update", "session_id", "state", "route", "results_delta", "snapshot_jpeg_b64"}` at most twice a second per session. Snapshots are the latest uploaded frame, downscaled to 320 px wide.

---

## 6. Client capture page

### 6.1 Startup
1. Secure context required (HTTPS via tunnel). If `!isSecureContext`, show "Open the https link".
2. `getUserMedia({video: {facingMode: "user", width: {ideal: 640}, height: {ideal: 480}, frameRate: {ideal: 30}}, audio: false})`.
3. Read `track.getSettings()`, `track.getCapabilities?.()` (wrap in try), `track.label`.
4. Channel: `mobile_browser` if `navigator.userAgentData?.mobile` or `matchMedia("(pointer:coarse)")` with a small screen, else `desktop_browser`.
5. Motion permission: on iOS, call `DeviceMotionEvent.requestPermission()` from the Start button's tap handler. Record the result.
6. WebGL renderer string via `WEBGL_debug_renderer_info` if available, and `navigator.webdriver`.
7. Show a flash notice: "The screen will change colour a few times. Tap here if bright flashes are a problem for you." That option sets `accessibility_route = true`, so the planner skips light pulses and routes to an agent challenge.

### 6.2 Frame grabber (`grabber.ts`)
- Prefer `video.requestVideoFrameCallback((now, md) => ...)`. Time is `md.captureTime ?? now`. Record `presented_frames` and `media_time`.
- Fallback: an rAF loop that grabs when `video.currentTime` changes; `clock_source = "raf"`.
- Draw to a canvas at 640x480 (desktop) or 480x360 (phones), `toBlob("image/jpeg", 0.92)`. Capture the timestamp in the callback, not when the blob resolves.
- Keep a bounded queue (max 90 frames). If it overflows, drop and log the drop with its `presented_frames` gap.
- Upload a batch every `upload_batch_ms` (default 1000) as multipart. Retry with backoff and never block capture.

### 6.3 Pulse executors
- **Light** (`light.ts`): a full-screen colour overlay on phones; a border of `desktop_border_frac` (default 0.18 of the shorter side) on desktops, with the self-view kept in the centre. On a `pulse` message, set `received`. In the next `requestAnimationFrame` set the colour and record `applied` = rAF timestamp. In the following rAF record `painted`. After `duration_ms` clear it and record `ended`. Never more than 3 flashes in any second.
- **Lens** (`lens.ts`): only if `getCapabilities()` lists `exposureCompensation`, `exposureTime` with `exposureMode: "manual"`, or `colorTemperature` with `whiteBalanceMode: "manual"`. Call `track.applyConstraints({advanced: [params]})`. Record `applied` before the call and `painted` when it resolves. Restore the original settings after the unit.
- **Tilt** (`tilt.ts`): show "Tilt your phone slightly forward and back, twice" for `duration_ms` (default 2500). Sensors are logged all session; the prompt just marks the window.
- **Hand** (`hand.ts`): show "Pass your hand slowly across your face, then turn your head left and right" for `duration_ms` (default 4000) with a simple animation.

### 6.4 Coaching (`coach.ts`)
The probe runs on 3 s of frames in the browser using `@mediapipe/tasks-vision` FaceDetector: face size as a fraction of the frame, mean luma, Laplacian variance (blur), face-vs-background luma (backlight), measured fps. Tips map: face_frac < 0.06 → "Move closer"; luma < 60 → "Turn towards a light"; backlit → "Light is behind you, turn around"; blur → "Hold still" or "Wipe the camera". Up to 2 coaching rounds, then continue anyway; checks abstain if quality stays low.

### 6.5 Browser support (expected; confirm on real devices at gate G1)

| Feature | Chrome Android | Safari iOS | Chrome / Edge desktop | Firefox |
|---|---|---|---|---|
| `requestVideoFrameCallback` | yes | yes (15.4+) | yes | check; rAF fallback |
| `captureTime` in metadata | check | check | check | n/a |
| `getCapabilities` with exposure or white balance | some devices | no | rarely | no |
| `devicemotion` | yes | yes, after permission | n/a | yes |

"check" means record what the device does; the code handles both cases.

---

## 7. Device profiles

`profile_key = f"{channel}|{fps_band}"` where `channel` is `mobile_browser` or `desktop_browser` (`app` is reserved for later) and `fps_band` is `lt20`, `20to27` or `ge27` from the median measured fps. That gives 6 cells.

- `profile_claimed` comes from what the client reports (track settings, label, UA).
- `profile_measured` comes from the frames the server receives. **Thresholds always use the measured profile.**
- Fallback chain for thresholds: `profile` → `channel` → (fixed baselines only) `global`. If a check has fewer than `min_genuine` genuine sessions at every level available to it, it is **not validated** for that profile: it still runs and is shown, but the planner doesn't count it toward coverage.
- Camera class and light band can be added to the key later; the code takes the key fields from `config.yaml`.

---

## 8. Checks

Every check returns `CheckResult`. Score orientation: **higher is more suspicious**. Unless marked `rule`, a check fails when `score > threshold` from calibration (section 9). Each check has a quality value in 0..1 and abstains below `quality.min` (default 0.5) with a reason.

Planning units and threat coverage (● strong, ○ partial, blank none). Threats: `replay` (video on a screen), `premade` (pre-made deepfake injected), `liveswap` (live face-swap relay), `emulator` (emulator or hooked camera).

| Unit | Family | Mode | Needs | Cost (s) | replay | premade | liveswap | emulator |
|---|---|---|---|---|---|---|---|---|
| `capture` | capture | passive | always | 0 | ○ | ● | ● | ● |
| `content_clip` | content | passive | model file present | 0 | ○ | ● | ○ | |
| `physiology` | physiology | passive | flag on, fps ≥ 24, ≥ 10 s | 0 | ○ | ● | ○ | |
| `light` | optical | active | screen, not accessibility route | 9 | ● | ● | ○ | ○ |
| `lens` | optical | active | lens capability | 4 | ● | ● | ○ | ○ |
| `tilt` | motion | active | gyro granted | 3 | ● | ● | ● | ● |
| `hand` | content | active | always | 4 | ○ | ● | ● | |

Every rating is a hypothesis until measured. The table lives in `planner/policy.yaml` so it can change without code changes.

### 8.1 Shared vision (`vision/`)
- `face.py`: MediaPipe FaceLandmarker in VIDEO mode (timestamps as int ms from `t`). Outputs per frame: 478 landmarks, bbox, a skin ROI mask (forehead and both cheeks from fixed landmark index sets; excludes eyes, brows and lips) and a background mask (frame minus the face bbox dilated 1.6x, minus a bottom-centre body block 50% wide and 40% tall).
- `hand.py`: MediaPipe HandLandmarker in VIDEO mode, up to 2 hands, convex hull mask dilated 15%.
- `flow.py`: Lucas-Kanade tracking of up to 200 Shi-Tomasi corners inside a mask, re-detecting every 10 frames.
- `arcface.py`: insightface `FaceAnalysis(name="buffalo_l")` on CPU with detection and recognition only. Normalised 512-d embeddings. (Research-only model licence; it's in the deck's disclosures.)
- `clip.py`: open_clip `ViT-B-32` with `laion2b_s34b_b79k`, image features of 224 px face crops with 1.3x margin.

All extractors accept a list of frames and return arrays aligned to frame index, so checks are pure functions of those arrays and can be tested with synthetic inputs.

### 8.2 `optical.light.*` (unit `light`)
Inputs: frame times `t[k]`, per-frame mean linear RGB of the skin ROI `F[k]` and background ROI `B[k]` (sRGB to linear with gamma 2.2), and light pulses from `pulses.jsonl`.

Per pulse with colour `c`:
1. Expected direction `d_c` = unit vector of (chromaticity of `c`) minus neutral (1/3, 1/3, 1/3). Pulse colours are `red`, `green`, `blue`, with no colour repeated twice in a row.
2. Chromaticity `x[k] = F[k] / sum(F[k])`. Projected signal `p[k] = (x[k] - mean(x over [painted-300, painted))) · d_c`. Noise `σ` = std of `p` over that pre-window (floor 1e-4).
3. Onset: the first `k` with `t[k]` in `(painted, painted+700]` where `p[k]` and `p[k+1]` both exceed `max(4σ, a_min)`. Interpolate linearly between `k-1` and `k` to the threshold crossing. `delay = onset - painted`.
4. Amplitude `A_face` = mean `p` from `onset+50` to `ended`. Compute `A_bg` the same way on `B`. Reflectance ratio `ρ = A_face / max(A_bg, ε)`, clipped to [0.001, 1000].
5. Direction agreement: cosine between observed Δchromaticity and `d_c`.

A pulse is valid if face quality is fine through the window (skin ROI ≥ 2% of the frame, mean luma 40 to 220, < 5% clipped pixels, face centroid moves < 10% of face width) and the pulse `ok` is true.

Checks (need ≥ 5 valid pulses, else abstain with "Not enough clear light pulses"):
- `optical.light.delay`: score = `|median(delay) - center|`, where `center` is the genuine median for the profile from calibration. Pulses with no echo count as delay = 1000 ms. Reason examples: "Light echo late vs this device type on 7 of 8 pulses", "No light echo on 6 of 8 pulses".
- `optical.light.reflectance`: score = `-log(median ρ)` combined with `(1 - median direction cosine)`, summed. Reason: "Face and background reacted alike, like a flat screen".

Quality = valid pulses / total pulses, times a lighting factor (1 if the room is not too bright; reduce when `A_bg` is tiny relative to noise for all pulses).

### 8.3 `optical.lens.step` (unit `lens`)
Per lens step: global mean luma `L[k]`; detect the step onset after `applied` the same way as 8.2 (on `L`, with sign from the requested change). Score = `(1 - fraction of steps with an echo in the right direction) + |median(delay) - center| / 100`. Abstain if no lens capability (reason: "Camera controls not available on this browser", which is normal for many devices).

### 8.4 `motion.tilt.*` (unit `tilt`)
Inputs: background-masked frames in the tilt window plus 500 ms either side, and gyro samples.
1. Image speed `v[k]` = median LK feature displacement per frame divided by `Δt`, in px/s. Abstain if fewer than 30 tracked features (plain wall) with reason "Background has too little texture".
2. Gyro magnitude `w(t) = |rr|`. Abstain if peak `w` < `min_peak_dps` (the user didn't tilt) with reason "No tilt detected".
3. Resample both to 100 Hz on the overlap, z-normalise, and compute Pearson correlation for lags −300 to +300 ms in 10 ms steps (positive lag = video after gyro). Take `r_max` and `lag_at_max`.

Checks:
- `motion.tilt.corr`: score = `1 - r_max`. Reason: "Video motion did not follow the phone's motion sensor".
- `motion.tilt.lag`: score = `|lag_at_max - center|`. Reason: "Video lagged the motion sensor more than usual for this device".

### 8.5 `capture.*` (unit `capture`, passive)
- `capture.timing`: features from frame intervals: median fps, coefficient of variation, fraction within ±0.5 ms of the median interval, longest gap. Score = max robust z-score of the features vs genuine for the profile (`|x - median| / (1.4826 * MAD)`, from calibration). Reason names the feature, e.g. "Frame timing unusually even for this device type".
- `capture.duplicates`: 64-bit dHash per frame. Duplicate = Hamming distance 0 and mean absolute difference < 0.5 grey levels versus the previous frame. Score = duplicate fraction. Reason: "Repeated frames (12 of 300)".
- `capture.noise`: on every 5th frame, residual = grey − 3x3 median blur. In 16x16 blocks whose Sobel magnitude is in the lowest 30%, block σ = 1.4826·MAD(residual). Features: median σ, slope of σ vs block brightness. Score = max robust z vs genuine. Reason: "Almost no sensor noise for this kind of camera".
- `capture.label` (`rule`): fail if the camera label matches `/(obs|virtual|manycam|snap camera|xsplit|droidcam|iriun|e2esoft|camtwist|mmhmm)/i`. Reason: "Camera reports itself as a virtual camera". This is trivial to spoof; it only catches lazy attempts.
- `capture.env` (`rule`): fail if `navigator.webdriver` is true, or the WebGL renderer matches `/(swiftshader|llvmpipe|android emulator)/i`, or the UA matches `/(android sdk built for|emulator)/i`. Reason: "Browser shows emulator or automation signs".
- `capture.claim_mismatch` (`rule`, uses calibration stats): `claimed_low` = claimed fps ≤ 20, or claimed height ≤ 480 with a generic label and no camera controls. `measured_high` = noise σ below the genuine 2.5th percentile for the claimed profile and timing CV below the genuine 2.5th percentile, or measured fps > 1.2x claimed fps. Fail if both. Also sets `force_agent = true` in the decision. Reason: "Claimed a basic webcam, but the video is cleaner and steadier than one".
- `capture.attestation`: always abstains in the browser ("Attestation needs the native app").

### 8.6 `content.clip.probe` (unit `content_clip`, passive)
Sample 16 frames spread over the session, crop faces, compute CLIP features and apply the logistic-regression probe (`models/clip_probe.joblib`). Score = mean of the top 25% fake probabilities. Abstain if the model file is missing ("Visual detector not installed") or fewer than 8 usable face crops.

Training (`train/clip_probe.py`): FaceForensics++ (c23) and Celeb-DF v2 if available locally. 8 frames per video, 1.3x face crops. Logistic regression with C chosen by 5-fold grouped CV (grouped by source video). Report AUC on each dataset's test split in `models/clip_probe_report.md`. Never train on lab sessions.

### 8.7 `content.hand.*` (unit `hand`)
Window: hand prompt `painted` − 1000 ms to `ended` + 500 ms.
- **Overlap frames**: hand mask covers > 10% of the face bbox.
- `content.hand.response` (`rule`): fail if no overlap frame appears between the prompt's `painted` and `ended + 500 ms` while the face stays visible, or if the yaw range stays under 5°. A recording can't react to a prompt released at a random moment. Reason: "No hand pass or head turn after the prompt". This doesn't change the unit's ratings in section 8 until measured. In round 1 a genuine user who misread the prompt fails only this one family, which leads to `ADD_CHECKS`, never to a hold on its own.
- `content.hand.flicker`: for face-bbox pixels outside the hand mask in both frames `k-1` and `k`, the mean absolute difference of the high-pass image (grey − Gaussian blur σ=2), divided by the same measure averaged over the 1000 ms before the prompt. Score = 95th percentile of that ratio over overlap frames. Reason: "Face flickered around the hand".
- `content.hand.identity`: ArcFace embeddings at 10 fps over the window. Reference = normalised mean of embeddings in the pre-window. Score = `1 - p10(cosine to reference)` over frames with detection score > 0.6. Also record yaw range (from landmarks); abstain if yaw range < 15° ("Head turn too small"). Reason: "Face identity drifted during the hand pass and head turn".
- `content.hand.flicker` and `content.hand.identity` abstain if there are fewer than 5 overlap frames ("Hand didn't cross the face") or the face was lost in > 50% of window frames.

### 8.8 `physiology.pos.coherence` (unit `physiology`, behind `physiology.enabled`)
POS rPPG (Wang et al. 2017) on three ROIs (forehead, left cheek, right cheek) over ≥ 10 s, band-pass 0.7 to 3.0 Hz. Coherence = share of ROI pairs whose spectral peaks are within 0.1 Hz, multiplied by an SNR gate (peak power share > 0.3). Score = `1 - coherence`. **Do not store or return the heart rate or waveform.** Abstain if fps < 24, duration < 10 s, face too small, or luma variance too high. Known weakness (in the deck): good deepfakes can inherit the driver's pulse, and rPPG quality varies with skin tone and light.

---

## 9. Calibration (`calibration/`)

- Input: results of genuine sessions in tuning set A (from `eval/splits.json`), computed with `threshold=None`.
- For each `(check_id, level_key)` with at least `min_genuine` sessions (default 10):
  - one-sided checks: `threshold = quantile(scores, 0.975)` (linear interpolation)
  - centred checks (`*.delay`, `*.lag`): store `center = median(raw)`, recompute scores as `|raw - center|`, then take the 97.5th percentile
  - robust-z checks (`capture.timing`, `capture.noise`): store per-feature median and MAD, recompute scores, then take the 97.5th percentile
- Output: `calibration/thresholds.json` with `{check_id: {level_key: {threshold, center?, stats?, n}}}` plus a hash.
- At 97.5% each calibrated check falsely fails about 2.5% of genuine sessions on its own, before fusion. With n ≈ 10 to 20 per cell that estimate is rough; report n everywhere.
- **Bootstrap mode** (before calibration on set A is run): `calibration/bootstrap.yaml` holds hand-set provisional thresholds from the first set A genuine recordings. Every decision made with them sets `provisional_thresholds = true`, and the console shows "PROVISIONAL THRESHOLDS".

---

## 10. Planner (`planner/`)

Inputs: measured profile, client capabilities, `policy.yaml` (coverage table, unit costs, bar = 2 strong families per threat, `active_seconds_cap` default 25, `max_rounds` default 2), validated flags from calibration, and current results (for re-planning).

```
families_strong(threat, units) = { family(u) for u in units if strength(u, threat) == "●" and validated(u) }

plan_round(available, already_ran, results):
    units = all feasible passive units (always included)
    need[t] = 2 - |families with a strong PASS for t so far|   (round 1: count planned units)
    while any need[t] > 0 and active_seconds(units) < cap:
        candidates = feasible active units not yet planned this round
        gain(u) = sum over threats of 1 if (strength(u,t)=="●" and family(u) not already strong for t and need[t] > 0)
        pick u maximising gain(u) / cost(u); ties → lower cost, then fixed order [tilt, light, hand, lens]
        stop if best gain == 0
    route_hint = None if all need[t] <= 0 else "AGENT_CHALLENGE"
```

Notes:
- Passive units always run first and cost nothing.
- Abstained checks don't count. In round 2 the planner re-plans with actual statuses and may repeat an abstained unit after a coaching tip, within the cap.
- `accessibility_route` removes `light` and forces `AGENT_CHALLENGE` when coverage is short.
- With the default table, a desktop browser can't reach two strong families for `replay` and `emulator` (no motion sensor), so it plans light + hand and gets `route_hint = AGENT_CHALLENGE`. A mobile browser with a gyro plans `tilt` + `light`. Tests in `test_planner.py` pin these cases.

---

## 11. Fusion and routing (`fusion.py`)

1. Family status: `fail` if any check in the family failed; else `pass` if any passed; else `abstain`. Several failing checks in one family count as one failed family.
2. Coverage per threat: families with status `pass` whose units are ● for that threat.
3. Route:
   - failed families ≥ 2 → `HOLD` (needs_human)
   - failed families = 1 → `ADD_CHECKS` if rounds < `max_rounds` and active seconds < cap, targeting threats that family covered; otherwise `AGENT_CHALLENGE`
   - no failures and every threat has ≥ 2 strong families → `PASS`
   - no failures but coverage short → `ADD_CHECKS` if possible, else `AGENT_CHALLENGE`
   - `force_agent` (claim mismatch) → at least `AGENT_CHALLENGE`
   - after an agent challenge, coverage still short and no agent approval → `ASSISTED_KYC`
4. `AGENT_CHALLENGE` and `HOLD` never become `PASS` without an agent or auditor action logged in `events.jsonl` with a note.
5. Agent-fired pulses are scored by the same checks and added to the same families.

### Reasons (`reasons.py`)
Every non-pass check gives one sentence from a template with real counts ("on 7 of 8 pulses"). The decision lists at most 3 reasons, failed families first. The applicant sees only: continue, "Please try again in better light", "We need to verify you with an agent" or "Please visit a branch".

---

## 12. Agent and auditor console (`client/console.html`)

Layout follows deck slide 10:
- Header: session id, product, route chip, and `PROVISIONAL THRESHOLDS` or `SYNTHETIC` labels when relevant. Footer: "Prototype access control".
- Left: live snapshot (2 fps), a "Plan used" box (profile, claimed vs measured, units planned and skipped, with reasons) and a "Why held" box (top reasons).
- Middle: checks grouped by family with status chips (PASS, FAIL, ABSTAIN, MISMATCH) and reasons. Decision banner. Buttons: **Approve**, **Fire a pulse** (menu: light, tilt), **Send to assisted KYC**, **Escalate to fraud team**.
- Timeline (the "one clock" view): canvas plot of the light projection signal `p(t)` for face and background, vertical markers at each pulse `painted`, the detected onset, and the profile's genuine delay band shaded.
- Right: investigation lead panel (rig radar). Shows only synthetic leads, labelled `SYNTHETIC DEMO DATA`.
- Evidence tab: frames around each pulse onset, chain head hash, download evidence zip.

"Fire a pulse" releases the pulse after a random 300 to 1500 ms delay, so even the agent's click timing isn't the pulse time.

---

## 13. Evidence pack and hash chain (`evidence.py`)

When a session is decided, build `chain.json`: an ordered list of artifacts (`meta.json`, `pulses.jsonl`, `sensors.jsonl`, `results.json`, then ±3 frames around each pulse onset). Each entry is `{file, sha256, prev, link}` where `link = sha256(prev_link + sha256)` and the first `prev` is the session id. Store the head link in SQLite. `scripts/verify_evidence.py <zip>` recomputes the chain and reports the first mismatch. The evidence zip holds those files plus `chain.json`.

---

## 14. Rig radar (`radar.py`, synthetic demo only)

Fingerprint per session: timing vector (median light delay, frame-interval CV, median fps), camera vector (resolution, noise σ, noise slope) and a room embedding (CLIP image embedding of 5 frames with the face and body blocked out, averaged). Similarity: timing and camera use 1 − normalised L1; room uses cosine. A lead needs room similarity > 0.9 **and** timing or camera similarity > 0.8, across different applicant codes. `scripts/seed_radar_demo.py` creates two sessions flagged `synthetic: true` (codes `SYN-A`, `SYN-B`) by copying one attack session's fingerprint with small noise. The console must show `SYNTHETIC DEMO DATA` on any lead that involves a synthetic session. Leads are for review, never proof; shared kiosks and family devices look alike.

---

## 15. Evaluation protocol (`eval/`)

### 15.1 Superset recordings
Recorder mode (`record.html`): the operator enters person code, device code, light condition, label (genuine or attack), attack tool and consent reference, then hands over the device. The session runs **every feasible unit** in a shuffled order (light 8 pulses, tilt, hand, lens if supported) plus at least 12 s of plain video for passive checks. Every policy is then evaluated on the same recordings by choosing which units it may use.

### 15.2 Splits (decided at recording time, so set B is never looked at during development)
- **Genuine sessions: person-disjoint.** Each volunteer is assigned to set A (about 60%) or set B (about 40%) when they enrol, balanced by the devices they bring, and listed in `eval/people.csv`. The recorder page fills `label.set` from that file.
- **Attack sessions:** assigned when recorded, alternating A and B within each tool. One tool (default `liveportrait`) goes entirely to set B.
- All development work (gates G2 and G3, feature tuning, bootstrap thresholds) uses set A only. `eval/separation.py` and the CLI's batch modes refuse set B sessions.
- `eval/split.py` checks these rules (no person in both sets, held-out tool only in B) and writes `eval/splits.json` with a content hash.

### 15.3 Freeze
`eval/freeze.py` writes `eval/FROZEN` with hashes of `policy.yaml`, `calibration/thresholds.json`, `config.yaml` and `splits.json`. `eval/run.py` refuses to score set B if `FROZEN` is missing or any hash differs.

### 15.4 Policies (same set B sessions)
- **Fixed-light**: units `light` + `content_clip`, global thresholds (pooled set A genuine), HOLD if any check fails, else PASS.
- **Fixed-all**: every feasible unit, global thresholds, HOLD if any check fails, else PASS. No routing.
- **Adaptive**: planner on the measured profile, per-profile thresholds with fallback, family fusion and routing. `ADD_CHECKS` is simulated with the extra units present in the superset recording. `AGENT_CHALLENGE` is counted as "routed to a person", never as accepted.

### 15.5 Metrics (counts with denominators, plus 95% Wilson intervals)
- **Attacks accepted** (APCER): attack sessions ending in PASS, per attack tool and overall; also the worst tool.
- **Genuine held** (BPCER): genuine sessions ending in HOLD.
- **Genuine routed**: genuine sessions ending in ADD_CHECKS (second round), AGENT_CHALLENGE or ASSISTED_KYC, each counted.
- **Abstain rate**: share of planned checks that abstained.
- **Time**: median and 95th percentile of probe + coaching + recorded durations of the units the policy used.
- All of the above per profile (device tier) and per light condition; per self-reported skin-tone band only where volunteers chose to give it.

`eval/report.py` writes `eval/out/results.md`, `results.csv`, `per_profile.csv` and `table.png` (for the deck's slide 11).

### 15.6 Separation check for gate G2
`eval/separation.py --attack-tool deeplivecam --device <code>` prints per-feature AUC (genuine vs attack) with n for each side, for the light delay, reflectance, duplicates, timing, hand flicker and identity drift features. It reads set A sessions only.

---

## 16. Security and privacy (prototype level)

- HTTPS through the tunnel; CORS locked to the tunnel origin.
- Pulses signed, single-use, released just in time; the applicant API never returns scores or check names.
- Console behind a passcode from `.env`, shown as prototype-level in the UI.
- `data/` and `models/` gitignored. No faces in logs. Person codes only; names exist only on paper consent forms.
- `scripts/purge_volunteers.py` deletes every session whose person code is not in `TEAM_CODES` (from `.env`), plus derived files, and prints what it deleted. Run it after the event, by the date on the consent form.
- Flashes: at most 3 per second, saturation limited, and an opt-out that routes to an agent.

---

## 17. `config.yaml` defaults

```yaml
capture:  {desktop_size: [640, 480], mobile_size: [480, 360], jpeg_quality: 0.92, upload_batch_ms: 1000, queue_max: 90}
pulses:
  light:  {count: 8, duration_ms: 400, gap_ms: [700, 1300], colours: [red, green, blue], desktop_border_frac: 0.18, expires_in_ms: 300}
  lens:   {steps: 3, ev_delta: 1.0}
  tilt:   {duration_ms: 2500, min_peak_dps: 15}
  hand:   {duration_ms: 4000}
  release_jitter_ms: [0, 400]
  agent_fire_delay_ms: [300, 1500]
profiles: {fields: [channel, fps_band], fps_bands: [20, 27]}
planner:  {active_seconds_cap: 25, max_rounds: 2, families_per_threat: 2}
calibration: {quantile: 0.975, min_genuine: 10}
quality:  {min: 0.5, min_face_frac: 0.02, luma_range: [40, 220], min_fps: 12}
physiology: {enabled: false}
radar:    {room_sim: 0.9, other_sim: 0.8}
```
