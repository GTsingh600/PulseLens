# PulseLens build plan: 48-hour finale

How to use this file:
- Put `CLAUDE.md` at the repo root and `SPEC.md`, `BUILD_PLAN.md`, `STATUS.md` and `consent_form.md` in `docs/`.
- Start Claude Code in the repo and paste the prompts from section 8, one milestone at a time.
- Every task has acceptance checks. Claude Code runs them, fixes failures and ticks the task in `docs/STATUS.md`.
- Tasks marked **[HUMAN]** need a real phone, a person, a GPU or a decision. Claude Code writes the exact steps into `STATUS.md` and moves on.

---

## 0. Before the event

Check the hackathon rules first. If writing code before the finale isn't allowed, do only this non-code prep.

- [ ] **Request dataset access today.** FaceForensics++ and Celeb-DF v2 both need a request form, and approval can take days. Without them, `content_clip` is cut (the plan still works).
- [ ] **Devices:**
  - at least one Android phone with Chrome
  - at least one iPhone with Safari
  - a laptop with a built-in webcam
  - a cheap USB webcam (480p class)
  - a laptop with an NVIDIA GPU for Deep-Live-Cam
  - a phone stand
  - a phone hotspot as backup Wi-Fi
- [ ] **Attack laptop (human installs and tests once on a teammate):** OBS Studio with its virtual camera, Deep-Live-Cam, LivePortrait, and the Android Studio emulator.
- [ ] **Install cloudflared** and test a quick tunnel from a phone on mobile data. Phones need HTTPS for the camera and motion sensors.
- [ ] **Download the models:**
  - MediaPipe `face_landmarker.task` and `hand_landmarker.task`
  - insightface `buffalo_l`
  - open_clip `ViT-B-32` (`laion2b_s34b_b79k`)
  - the `@mediapipe/tasks-vision` wasm files
- [ ] **Paperwork:** print 20 copies of `docs/consent_form.md` and prepare a paper sheet mapping names to codes (`P01`...). The sheet never goes into the repo.

---

## 1. Team tracks

Do M1.1 together. Then split into three tracks, each teammate driving one Claude Code session in its own git worktree (`git worktree add ../pl-trackA -b trackA`). Merge to `main` at every gate.

| Track | Owns | Teammate |
|---|---|---|
| A: Client | capture page, pulses, recorder page, console UI | (assign) |
| B: Analysis | vision extractors, checks, calibration, CLIP probe | (assign) |
| C: Decision + eval | API, orchestrator, planner, fusion, evidence, radar, evaluation, data logistics | (assign) |

Keep at least one person awake and recording volunteers from H8 to H36.

---

## 2. Timeline and gates

| Hours | Milestone | Gate at the end |
|---|---|---|
| H0–6 | M1 Capture and probe | **G1 (H6):** light pulses and timing work on 3 real devices |
| H6–18 | M2 Evidence checks + recording starts | **G2 (H14):** live swap measurable? |
| H18–28 | M3 Plan, decide, console | **G3 (H24):** physiology go/no-go |
| H28–38 | M4 Measure | **G4 (H38):** results table filled |
| H38–48 | M5 Polish and rehearse | **Code freeze at H40** |

---

## 3. Milestones and tasks

Section numbers like §8.2 refer to `docs/SPEC.md`.

### M1 Capture and probe (H0–6)

**M1.1 [all] Scaffold.**
- **Build:**
  - Makefile targets from `CLAUDE.md`, `config.yaml` (§17), `.env.example`
  - FastAPI app with `/api/health`
  - Vite client with `index.html`, `record.html` and `console.html`
  - pydantic models (§4.6) mirrored in `types.ts`
  - `store.py` (session folders + SQLite `sessions` table), `server/tests/fixtures/synth.py` skeleton
  - `.gitignore` covering `data/`, `models/` and `.env`
- **Accept:** `make setup`, `make test` (at least one test), `make lint` clean, `GET /api/health` returns 200, `npm run build` succeeds.

**M1.2 [C] Session API and client WebSocket (§5).**
- **Build:**
  - endpoints for create, probe, frames (multipart), sensors and finalize
  - `/ws/client/{id}` with just-in-time pulse release, HMAC signing, single-use and expiry checks
  - an orchestrator stub that releases 8 light pulses with the configured gaps
- **Accept:**
  - `test_api.py`: create a session, upload 10 synthetic JPEGs plus `frames.jsonl`, and the files on disk match §4.1
  - `test_ws.py`: a pulse is sent; its first ack is accepted, a second ack is rejected, and a late ack is logged `ok:false`
  - applicant responses contain no `score` or `check` keys

**M1.3 [A] Capture page (§6.1 to §6.4).**
- **Build:**
  - startup checks, frame grabber with rVFC and rAF fallback, batched upload
  - light executor (full screen on phones, border on desktops), flash notice with opt-out
  - coaching with the tasks-vision FaceDetector
- **Accept:**
  - `make e2e` runs a full session in Chromium with `--use-fake-device-for-media-stream --use-fake-ui-for-media-stream`
  - at least 200 frames uploaded, with strictly increasing `t`
  - 8 pulse acks with `received ≤ applied ≤ painted < ended`
  - vitest covers channel detection and pulse spacing (≥ 700 ms gaps, ≤ 3 flashes per second)

**M1.4 [B] Vision base and light echo (§8.1, §8.2).**
- **Build:**
  - `frames.py` loader
  - `face.py` with skin and background masks
  - `checks/optical_light.py`, with the estimator as a pure function of ROI means and the pulse log
- **Accept (synthetic tests in `test_light.py`):**
  - delays of 60, 100, 150 and 250 ms at 30 fps with ±3 ms jitter are recovered within ±1 frame
  - amplitude 0 gives "no echo"
  - `A_face > A_bg` gives ρ > 1, and equal change gives ρ ≈ 1
  - direction cosine > 0.9 for the right colour
  - fewer than 5 valid pulses makes the check abstain

**M1.5 [B] Analysis CLI.**
- **Build:** `python -m pulselens.cli analyze <dir> --plots` writes `results.json` and `plots/light_<pulse_id>.png` (face and background signal, painted and onset markers). Add `synth.py --bundle <dir>` to generate a full synthetic session bundle.
- **Accept:** runs cleanly on the synthetic bundle (light echo found) and on an e2e fake-camera session (abstain is fine, crashing is not).

**GATE G1 (H6) [HUMAN]**
- **Test:** Android Chrome, iPhone Safari and a laptop with Chrome, normal room light, 2 sessions each, then `cli analyze`.
- **Go:**
  - echo found on ≥ 6 of 8 pulses in ≥ 4 of 6 sessions
  - frame rate ≥ 20 fps or the device maximum
- **Record in `STATUS.md`:** `clock_source`, capabilities and gyro permission for each device.
- **No-go fallbacks, in order:**
  1. pulse duration 600 ms, and full screen on desktops too
  2. stronger colours (blue and white only)
  3. if desktops still fail, set `light` to ○ for `desktop_browser` in `policy.yaml`. Desktop sessions then rely on hand, capture and the agent challenge; tell the deck owner.

### M2 Evidence checks (H6–18)

**M2.1 [A] Recorder page and superset mode (§15.1).**
- **Build:** operator form with person code, device code, light condition, genuine/attack, attack tool and consent reference. It runs every feasible unit in shuffled order plus 12 s of plain video. The set (A or B) comes from `eval/people.csv` for genuine sessions and alternates within each tool for attacks, with `liveportrait` always B (§15.2).
- **Accept:** e2e in superset mode records light and hand units with the label and set in `meta.json`. A unit test covers the set assignment rules.

**M2.2 [A] Sensors and tilt prompt (§6.1 step 5, §6.3).**
- **Build:** `devicemotion` logging, the iOS permission flow inside the Start tap, the tilt prompt, and the `sensors.jsonl` upload.
- **Accept:** vitest covers the permission state machine. **[HUMAN]** On Android and iPhone, `sensors.jsonl` shows ≥ 40 samples per second during the tilt.

**M2.3 [B] Motion check (§8.4) with `flow.py`.**
- **Accept (synthetic):**
  - a textured background shifted by the integral of a gyro signal with lag 40, 90 or 150 ms gives a lag within ±20 ms and `r_max` > 0.8
  - unrelated motion gives `r_max` < 0.4
  - no tilt abstains
  - a plain background abstains

**M2.4 [B] Capture integrity (§8.5).**
- **Accept:**
  - noise σ=3 vs σ=0 are separated
  - duplicates are counted exactly
  - jittered vs perfectly even timing give different features
  - unit tests for the label and environment regexes
  - truth-table test for `claim_mismatch`
  - `capture.attestation` always abstains in the browser

**M2.5 [A+B] Hand pulse (§6.3, §8.7).**
- **Build:** client prompt and animation, `hand.py`, `arcface.py`, and the `content.hand.response`, `.flicker` and `.identity` checks.
- **Accept:**
  - synthetic noise patches outside the hand mask during overlap give a flicker ratio > 3, while clean frames give about 1
  - a mocked embedding function with a cosine drop is detected
  - no hand after the prompt makes `response` fail
  - the abstain rules hold

**M2.6 [B] CLIP probe (§8.6).** Only if the datasets are on disk by H6; otherwise mark it CUT in `STATUS.md` and move on.
- **Accept:** `models/clip_probe_report.md` has AUC per dataset test split, and inference abstains cleanly when the model file is missing.

**M2.7 [A+B] Lens pulse (§6.3, §8.3), where supported.**
- **Accept:** a synthetic luminance-step test, and a client test showing lens is skipped when capabilities are missing.

**M2.8 [B] Calibration (§9).**
- **Build:** the thresholds writer, the fallback chain, validated flags, and `bootstrap.yaml` with provisional values.
- **Accept:** tests with fake score tables cover quantile, centred and robust-z checks, the fallback chain, `validated=false` below `min_genuine`, and `provisional_thresholds=true` in bootstrap mode.

**M2.9 [C] Labels and separation report (§15.6).**
- **Build:** `eval/labels.csv` synced from `meta.json`, and `eval/separation.py`.
- **Accept:** it runs on synthetic bundles, prints AUC with n for each side, and refuses set B sessions (test).

**M2.10 [B] Physiology (§8.8)**, only if the track is ahead, behind `physiology.enabled`.
- **Accept:**
  - a coherent 1.2 Hz signal in 3 ROIs gives coherence ≈ 1, and noise gives low coherence
  - a test asserts no heart rate or waveform appears in `results.json`

**[HUMAN] Recording starts:** genuine sessions from H8, attack sessions from H10. See section 5.

**GATE G2 (H14) [HUMAN + C]: is the live swap measurable?**
- **Test:** `eval/separation.py --attack-tool deeplivecam --device <laptop>`, with at least 5 attack and 10 genuine set A sessions on the same laptop.
- **Go:** any of light delay, hand flicker, identity drift, duplicates or frame timing reaches AUC ≥ 0.8.
- **No-go:**
  - the demo shows the live swap held by capture integrity, the hand pulse and the agent challenge, not by timing
  - drop "a relay adds delay" from the spoken pitch
  - the timing slide stays marked "illustrative"

### M3 Plan, decide, console (H18–28)

**M3.1 [C] Registry and planner (§8 table, §10, `policy.yaml`).**
- **Accept (`test_planner.py`):**
  - desktop browser plans `light` + `hand` with route hint `AGENT_CHALLENGE`
  - mobile browser with a gyro plans `tilt` + `light` with no hint
  - accessibility route drops `light`
  - the friction cap is respected
  - round 2 re-plans after abstentions
  - units with `validated=false` don't count toward coverage

**M3.2 [C] Fusion, routing and reasons (§11).**
- **Accept:** table-driven tests for every route rule, including:
  - family de-duplication
  - `force_agent`
  - `needs_human`
  - the provisional flag
  - "HOLD/AGENT never becomes PASS without a logged human action"
  - reason sentences carry real counts

**M3.3 [C] Live orchestrator.**
- **Build:**
  - flow: probe → coach → round 1 (pulses and prompts just in time) → incremental analysis in a process pool → fusion → round 2 or agent challenge → decided
  - the console "fire" endpoint with its random delay
  - applicant-safe messages only
- **Accept:**
  - an e2e live session with the fake camera reaches a route within 60 s
  - firing during a session writes a `source: "agent"` pulse
  - a test confirms applicant payloads never contain score or check keys

**M3.4 [A] Console (§12).**
- **Build:**
  - session list and detail view, with the one-clock timeline canvas
  - buttons, passcode, and the PROVISIONAL, SYNTHETIC and EXAMPLE labels
- **Accept:** Playwright opens the console, sees live updates, clicks "Fire a pulse" and the pulse appears in the timeline; approve and escalate are logged with a note.

**M3.5 [C] Evidence chain and zip (§13).**
- **Accept:** changing one byte in any file makes `verify_evidence.py` report that file.

**M3.6 [C] Rig radar demo (§14).**
- **Build:** `seed_radar_demo.py` and the console panel.
- **Accept:** a test confirms any lead involving a synthetic session renders with "SYNTHETIC DEMO DATA".

**GATE G3 (H24): physiology go/no-go.**
- **Go:** on set A recordings so far (genuine vs pre-made injection), coherence AUC ≥ 0.75 and phone abstain rate < 50%. Then turn the flag on. Never use LivePortrait sessions here: that tool is held out for set B.
- **Otherwise:** leave it off and call it roadmap. The deck already calls it a stretch goal.

### M4 Measure (H28–38)

**M4.1 [C] Splits.**
- **Build:** finish labels, run `split.py` to check the sets assigned at recording time, commit `splits.json`.
- **Accept:** no person appears in both sets, and the held-out tool appears only in set B.

**M4.2 [B] Calibrate on set A.**
- **Build:** produce `thresholds.json`, and the console stops showing PROVISIONAL.
- **Accept:** every threshold records its n, and cells below `min_genuine` fall back correctly.

**M4.3 [C] Freeze and run the policies.**
- **Build:** run `freeze.py`, then `run.py` for Fixed-light, Fixed-all and Adaptive on set B, then `report.py`.
- **Accept:** `run.py` refuses to run without `FROZEN` or after any config change (test), and `eval/out/` has `results.md`, `results.csv`, `per_profile.csv` and `table.png`.

**M4.4 [C] Slices and intervals.**
- **Build:** per-profile, per-light and optional per-skin-tone-band tables with Wilson intervals.
- **Accept:** every number is printed as "x of n".

**GATE G4 (H38): results table filled.** Whatever the numbers are, they go in the deck as measured, with denominators. If Adaptive doesn't keep attack acceptance at or below both baselines, show which family or rule let attacks through. That is what slide 11 promises.

### M5 Polish and rehearse (H38–48)

**M5.1 [A+C] Demo mode.** `DEMO=1` adds a reset button, loads the radar seed and shows a scenario checklist in the console.

**M5.2 [A] Robustness.** WebSocket reconnect and resume, upload retry, timeouts, and clear screens for no camera, permission denied and insecure context.

**M5.3 [C] README.** How to run it, the architecture diagram, and a list of what is measured vs illustrative.

**M5.4 [C] Purge script.** Tested on a copy of `data/`.

**M5.5 [HUMAN] Rehearsals.**
- Run the full demo 5 times.
- Run the judge replay 20 times. Keep it in the demo only if ≥ 18 of 20 are held and the genuine control passes each time.
- Record a fallback screen video of the whole demo by H44.

**H40: code freeze.** After this, only fixes for demo bugs.

**[HUMAN] Deck updates after G4:**
- slide 11 table from `eval/out/`
- optionally a real held-session screenshot on slide 10 (keep the EXAMPLE label if it isn't real)
- demo wording on slide 13 (see section 6)

---

## 4. Cut list (cut from the top when behind)

1. Physiology (already a stretch goal)
2. Lens pulse (few browsers support it anyway)
3. CLIP probe (if the datasets are late)
4. Rig radar panel (keep one static labelled screenshot instead)
5. Round-2 re-planning (route straight to the agent challenge instead)

Never cut: light pulse, tilt, hand pulse, capture integrity, planner, fusion, console with "Fire a pulse", evaluation on set B.

---

## 5. Data collection protocol [HUMAN]

**Consent first.** Every volunteer signs `docs/consent_form.md` before recording. Use codes only (`P01`, `D01`). Faces of volunteers are never used in attacks.

**Set assignment at enrolment.** When a volunteer gets a code, add them to `eval/people.csv` as set A or B (about 60/40, balancing phones and laptops across sets). Nobody looks at set B sessions until gate G4.

**Genuine sessions** (target ≥ 100; aim for ≥ 10 per profile cell where possible):
- 10 to 15 volunteers: teammates plus other participants who agree
- per person: their own phone (mobile browser), the team laptop's built-in webcam and the cheap USB webcam where possible
- normal light and dim light, 2 repeats each
- about 1 minute each in `record.html`; run two stations in parallel

**Attack sessions** (only on consenting teammates, swapping teammates' faces):

| Attack | How (human-operated) | Channel | Target | Set |
|---|---|---|---|---|
| Screen replay | teammate video played on a phone held up to the camera | desktop and mobile | 10 | A and B |
| Pre-made injection | OBS virtual camera playing a recorded teammate video | desktop | 10 | A and B |
| Single-photo fake | LivePortrait output fed through the OBS virtual camera | desktop | 8 | B only (held out) |
| Live face-swap | Deep-Live-Cam into the OBS virtual camera | desktop | 10 | A and B |
| Emulator injection | Android Studio emulator using the virtual camera as its webcam, Chrome inside it | mobile (emulated) | 6 | A and B |

The attacker follows the prompts (tilt, hand) the way a real attacker would. Record tool versions in `STATUS.md`. Everything stays on the team laptop and is purged after the event.

---

## 6. Demo script

1. **Phone, mobile browser:** a quick tilt and a few light pulses, then PASS in about 15 s.
2. **Desktop, cheap webcam, dim room:** coached, light and hand pulses. The planner asks for an agent challenge; the agent fires one pulse and approves.
3. **Live face-swap through a virtual camera posing as a weak webcam:** claim mismatch and capture integrity fail; the agent fires a pulse; the timeline shows the late echo and hand flicker; HOLD.
4. **A judge holds a replay up to the laptop camera on their own phone:** we expect no light echo and no response to the hand prompt, so HOLD. Only include it if rehearsal passed (M5.5).
5. Anything that fails on the day is shown openly, with its route.

**Deck fix needed:** v5 slide 13 says the phone "passes on passive checks alone" and the desktop "passes" after one hand pulse. With this planner, a phone needs a tilt and light pulses to cover replays, and a desktop on an instant loan always gets an agent challenge (deck slide 8 already says so). Reword steps 1 and 2 to match the script above.

---

## 7. Traceability: deck claim → code → proof

| Deck claim | Where in code | Evidence on the day |
|---|---|---|
| One-time pulses released just in time or fired by the agent | `orchestrator.py`, `api/ws.py`, `api/console.py` | `test_ws.py`, `pulses.jsonl` with `source` |
| One clock, calibrated per device | `grabber.ts`, `optical_light.py`, `calibration/` | timeline view, `thresholds.json` with n |
| Passive first, two families per threat, friction cap | `planner/` | `test_planner.py`, "Plan used" box |
| A weaker device never lowers the bar | `planner.py`, `capture.claim_mismatch` | demo step 3, `test_fusion.py` |
| A HOLD needs two failed families; never auto-reject | `fusion.py` | `test_fusion.py` |
| No score for the applicant | `api/sessions.py` | payload test in M3.3 |
| Evidence pack, hash-chained | `evidence.py` | `verify_evidence.py` tamper test |
| Fixed vs adaptive on a held-out set | `eval/` | `eval/out/results.md`, `FROZEN` |
| Rig radar leads | `radar.py` | labelled synthetic demo only |

---

## 8. Prompts for Claude Code

Paste one at a time. Each prompt assumes a fresh session in the repo root.

**M1 (together, then by track)**
```
Read CLAUDE.md, docs/SPEC.md and docs/BUILD_PLAN.md completely before writing code.
Do task M1.1 only. Run its acceptance checks, fix failures, tick it in docs/STATUS.md and commit.
Then stop and summarise what exists and what each track should start with.
```

**Track A, M1.3**
```
Read CLAUDE.md, docs/SPEC.md (sections 4, 5, 6) and docs/BUILD_PLAN.md (M1.3).
Build the capture page exactly as specified. Run make e2e and the vitest tests until they pass.
Tick M1.3 in docs/STATUS.md, commit, and write the real-device test steps for gate G1 under "Needs a human".
```

**Track B, M1.4 and M1.5**
```
Read CLAUDE.md, docs/SPEC.md (sections 4, 8.1, 8.2) and docs/BUILD_PLAN.md (M1.4, M1.5).
Write the synthetic tests first, then the estimator and extractors until the tests pass. Keep the estimator a pure
function of ROI means and the pulse log. Then build the analysis CLI and synthetic bundle generator.
Tick both tasks in docs/STATUS.md and commit after each.
```

**Track C, M1.2**
```
Read CLAUDE.md, docs/SPEC.md (sections 4, 5, 16) and docs/BUILD_PLAN.md (M1.2).
Build the session API and the client WebSocket with just-in-time signed pulses. Write test_api.py and test_ws.py
covering every acceptance check, including the no-scores-for-applicants rule. Tick M1.2 and commit.
```

**M2, M3, M4, M5 (per track)**
```
Read CLAUDE.md, docs/STATUS.md, and the parts of docs/SPEC.md referenced by tasks <IDs> in docs/BUILD_PLAN.md.
Do tasks <IDs> in order. For each: write the tests from its acceptance checks first, implement until they pass,
tick it in docs/STATUS.md, commit. If a task needs a device, a human or data we don't have, write exact steps under
"Needs a human" and continue with the next task. Do not change thresholds, policy.yaml ratings or splits unless the
task says so. Stop at the next gate and summarise the results the humans need to decide on.
```

**After a real-device test (paste results back in)**
```
Here are the gate G1 results from real devices: <paste STATUS table or analyze output>.
Read docs/BUILD_PLAN.md gate G1. Decide go or apply the no-go fallbacks in order, update config.yaml or
policy.yaml only as the fallback says, record the decision in docs/STATUS.md under "Decisions", and commit.
```

**Code review before freeze (H39)**
```
Review the repo against docs/SPEC.md and CLAUDE.md. List any place where: a number is shown without a source or label,
an applicant payload could leak a score, set B could be read before FROZEN, heart rate could be stored, or a check can
throw instead of abstaining. Fix what you find, with a test for each, and commit.
```
