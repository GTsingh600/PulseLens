# PulseLens: notes for Claude Code

PulseLens is a capture-aware liveness layer for video-KYC (RBI V-CIP). A browser capture page sends one-time **pulses** (screen colour, camera setting, phone tilt, hand pass) and records frames and sensor data on **one client clock**. A Python service scores each **echo** against baselines for that device profile, plans which checks to run, fuses results by **evidence family**, and routes the session to `PASS`, `ADD_CHECKS`, `AGENT_CHALLENGE`, `ASSISTED_KYC` or `HOLD`. An agent and auditor console shows the evidence and lets the V-CIP agent fire a pulse.

This repo is the 48-hour prototype for the Amazon AI Cyber Security Hackathon finale (Challenge 03, team Mama Mia).

Read these before writing code:
- `docs/SPEC.md`: what to build, exact JSON shapes, algorithms, config
- `docs/BUILD_PLAN.md`: order of work, tasks, acceptance checks, gates
- `docs/STATUS.md`: what is done, what is blocked, what needs a human

## Commands

| What | Command |
|---|---|
| Setup everything | `make setup` (venv + server deps, `npm ci` in `client/`, `python scripts/fetch_models.py`) |
| Run server | `make server` (uvicorn `pulselens.api.main:app` on :8000) |
| Run client | `make client` (Vite on :5173, proxies `/api` and `/ws` to :8000) |
| HTTPS for phones | `make tunnel` (cloudflared quick tunnel to :5173) |
| Unit tests | `make test` (pytest) and `make test-client` (tsc + vitest) |
| End-to-end | `make e2e` (Playwright, Chromium with a fake camera) |
| Lint | `make lint` (ruff, eslint); `make format` to auto-fix |
| Regenerate `types.ts` | `make types` (after any change to `models.py`) |
| ML extras (ArcFace, CLIP) | `make setup-ml` |
| Analyse a session | `python -m pulselens.cli analyze data/sessions/<id> --plots` |
| Evaluation | `python -m eval.run --split eval/splits.json --out eval/out` |

Every `make <target>` is `python scripts/dev.py <target>`, so it also works on Windows without make.

## Rules that always apply

1. **One clock.** Every client timestamp is `performance.now()` in ms, or a `requestVideoFrameCallback` time in the same time domain. Never use `Date.now()` in echo maths. Server times are for audit only.
2. **Checks never throw on bad input.** They return a `CheckResult` with `status="abstain"`, a quality value and a plain-language reason. Abstaining is never a failure.
3. **Thresholds come only from genuine sessions in tuning set A.** Never read set B results until `eval/FROZEN` exists. The eval code enforces this. Do not weaken that check.
4. **No invented numbers.** Every number shown in the console or docs comes from a real session, or is labelled `EXAMPLE`, `SYNTHETIC` or `PROVISIONAL`.
5. **Privacy.** Never store heart rate or the pulse waveform; store only the coherence score. Session data lives under `data/` (gitignored). Person codes are pseudonymous (`P01`...). Volunteer data is deleted with `scripts/purge_volunteers.py` after the event.
6. **Attack tooling is out of scope for code.** A human records attack sessions with existing tools (OBS, Deep-Live-Cam, LivePortrait, Android Emulator), only on consenting teammates. Do not write code that generates, improves or disguises deepfakes, or that helps evade detection. Detectors, test fixtures, labelling and evaluation code are in scope.
7. No real public figures, no real bank or customer data, nothing confidential, no secrets in git (`.env` holds `PULSE_HMAC_SECRET`, `CONSOLE_PASSCODE` and `TEAM_CODES`).
8. **Set B stays unseen during development.** Gates, tuning and debugging use set A sessions only (`label.set` in `meta.json`).
9. **When a step needs a real phone, a human or a GPU you don't have,** stop. Write exact steps under "Needs a human" in `docs/STATUS.md`, then continue with the next task that doesn't depend on it.
10. **A task is done when its acceptance checks in `docs/BUILD_PLAN.md` pass.** Then tick it in `docs/STATUS.md` with a one-line note. If you change an interface, update `docs/SPEC.md` in the same commit.
11. Commit after each finished task with a message like `M2.3 capture integrity checks`.

## Code conventions

- Python 3.11 with type hints. Pydantic v2 models in `server/pulselens/models.py` are the source of truth for JSON. `client/src/shared/types.ts` is generated from them with `make types`; never edit it by hand (a test fails if it is stale).
- Analysis code is pure: numpy arrays in, dataclasses out. File and network I/O only in `store.py`, `cli.py` and the API layer.
- Each check module exposes `run(ctx: SessionContext) -> list[CheckResult]` and is registered in `planner/registry.py`.
- Unit tests use synthetic fixtures from `server/tests/fixtures/synth.py`. No network and no real faces in tests.
- Heavy models (MediaPipe, ArcFace, CLIP) load once per process through `vision/models.py`.
- Client is TypeScript with no UI framework: plain DOM modules, small and readable.
- UI text is short and plain. The applicant never sees a score.
