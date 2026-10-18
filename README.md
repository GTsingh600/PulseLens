# PulseLens

Capture-aware liveness layer for video-KYC (RBI V-CIP). 48-hour prototype for the Amazon AI Cyber Security Hackathon finale, Challenge 03, team Mama Mia.

- What to build: [docs/SPEC.md](docs/SPEC.md)
- Order of work: [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md)
- Where we are: [docs/STATUS.md](docs/STATUS.md)
- How the scaffold works and why: [docs/M1.1_EXPLAINED.md](docs/M1.1_EXPLAINED.md)

## Quick start

```sh
make setup          # Python 3.11 venv, server deps, npm ci, model files
cp .env.example .env  # then fill in the secrets
make server         # FastAPI on :8000
make client         # Vite on :5173, proxies /api and /ws
make test lint      # pytest, ruff, eslint
```

No make (plain Windows)? Run `python scripts/dev.py <target>` instead. The full README comes in task M5.3.
