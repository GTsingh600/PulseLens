import pytest
from pydantic import ValidationError

from pulselens.models import ApplicantResponse, CheckResult, PulseRecord, SessionMeta
from tests.fixtures import synth


def test_abstain_helper_never_scores():
    r = CheckResult.abstain(
        "optical.light.delay", "light", "optical", "Not enough clear light pulses", quality=1.7
    )
    assert r.status == "abstain"
    assert r.score is None and r.threshold is None and r.threshold_source is None
    assert r.quality == 1.0  # clamped into 0..1
    assert r.reason


def test_check_result_rejects_quality_out_of_range():
    with pytest.raises(ValidationError):
        CheckResult(
            check_id="x", unit="light", family="optical", status="pass", score=0.1, threshold=0.2,
            threshold_source="rule", quality=1.5, features={}, reason="",
        )  # fmt: skip


def test_applicant_response_cannot_carry_scores():
    ApplicantResponse(state="continue", message="Thanks")
    with pytest.raises(ValidationError):
        ApplicantResponse.model_validate({"state": "continue", "message": "x", "score": 0.4})
    with pytest.raises(ValidationError):
        ApplicantResponse.model_validate({"state": "passed", "message": "x"})


def test_session_meta_round_trip():
    meta = synth.session_meta(mobile=True)
    again = SessionMeta.model_validate_json(meta.model_dump_json())
    assert again == meta
    assert again.client.accessibility_route is False


def test_pulse_record_matches_spec_example():
    line = (
        '{"pulse_id": "p_9f3", "kind": "light", "source": "planner",'
        ' "params": {"colour": "red", "duration_ms": 400, "region": "fullscreen"},'
        ' "released_server_iso": "2026-10-24T14:30:20+05:30", "received": 20011.2, "applied": 20012.0,'
        ' "painted": 20027.9, "ended": 20428.3, "ok": true, "error": null, "sig": "ab"}'
    )
    p = PulseRecord.model_validate_json(line)
    assert p.received <= p.applied <= p.painted < p.ended
