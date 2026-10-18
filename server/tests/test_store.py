import json
import re

import pytest

from pulselens.models import CheckResult, SessionResults
from pulselens.store import InvalidSessionId, SessionStore, new_session_id
from tests.fixtures import synth


@pytest.fixture
def store(tmp_path):
    return SessionStore(tmp_path)


def test_new_session_id_format():
    assert re.fullmatch(r"s_\d{8}_\d{6}_[0-9a-f]{4}", new_session_id())


def test_create_makes_bundle_layout(store):
    meta = synth.session_meta()
    d = store.create(meta)
    assert (d / "frames").is_dir()
    for name in ("meta.json", "frames.jsonl", "pulses.jsonl", "sensors.jsonl", "events.jsonl"):
        assert (d / name).is_file(), name
    assert store.read_meta(meta.session_id) == meta
    row = store.get_row(meta.session_id)
    assert row["state"] == "created" and row["mode"] == "live"


def test_frames_and_jsonl(store):
    meta = synth.session_meta()
    store.create(meta)
    times = synth.frame_times(10, jitter_ms=3)
    jpeg = synth.jpeg_bytes(synth.flat_frame(noise_sigma=3))
    for rec in synth.frame_records(times):
        assert store.write_frame(meta.session_id, rec.i, jpeg) == rec.file
    assert store.append_jsonl(meta.session_id, "frames", synth.frame_records(times)) == 10
    lines = store.read_jsonl(meta.session_id, "frames")
    assert [x["i"] for x in lines] == list(range(10))
    assert all(a["t"] < b["t"] for a, b in zip(lines, lines[1:], strict=False))
    files = sorted(p.name for p in (store.session_dir(meta.session_id) / "frames").iterdir())
    assert files == [f"{i:06d}.jpg" for i in range(10)]


def test_results_round_trip(store):
    meta = synth.session_meta()
    store.create(meta)
    assert store.read_results(meta.session_id) is None
    res = SessionResults(
        checks=[CheckResult.abstain("capture.attestation", "capture", "capture", "Needs app")]
    )
    store.write_results(meta.session_id, res)
    assert store.read_results(meta.session_id) == res
    raw = json.loads((store.session_dir(meta.session_id) / "results.json").read_text())
    assert raw["checks"][0]["status"] == "abstain"


def test_update_and_list(store):
    meta = synth.session_meta()
    store.create(meta)
    store.update(meta.session_id, state="decided", route="HOLD")
    assert store.get_row(meta.session_id)["route"] == "HOLD"
    assert [r["session_id"] for r in store.list_sessions()] == [meta.session_id]
    with pytest.raises(ValueError):
        store.update(meta.session_id, mode="superset")


@pytest.mark.parametrize("bad", ["../etc", "s_1_2_3", "s_20261024_143012_AB12", "s_20261024_143012_ab12/.."])
def test_rejects_unsafe_session_ids(store, bad):
    with pytest.raises(InvalidSessionId):
        store.session_dir(bad)


def test_unknown_stream_rejected(store):
    meta = synth.session_meta()
    store.create(meta)
    with pytest.raises(ValueError):
        store.append_jsonl(meta.session_id, "results", [])
