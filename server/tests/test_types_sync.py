from pulselens.config import REPO_ROOT
from pulselens.tsgen import render

TYPES_TS = REPO_ROOT / "client" / "src" / "shared" / "types.ts"


def test_types_ts_matches_models():
    committed = TYPES_TS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert committed == render(), "client/src/shared/types.ts is stale: run `make types`"


def test_rendered_types_cover_core_shapes():
    ts = render()
    assert 'export type Route = "PASS" | "ADD_CHECKS" | "AGENT_CHALLENGE" | "ASSISTED_KYC" | "HOLD";' in ts
    assert "export interface CheckResult {" in ts
    assert "  score: number | null;" in ts
    assert "  evidence_frames?: number[];" in ts
    assert '  type?: "pulse";' in ts
