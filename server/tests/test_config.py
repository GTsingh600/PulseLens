import pytest
from pydantic import ValidationError

from pulselens.config import config_hash, config_path, load_config, load_secrets


def test_config_yaml_matches_spec_defaults():
    cfg = load_config()
    assert cfg.capture.desktop_size == (640, 480)
    assert cfg.capture.mobile_size == (480, 360)
    assert cfg.pulses.light.count == 8
    assert cfg.pulses.light.gap_ms == (700, 1300)
    assert cfg.pulses.light.colours == ["red", "green", "blue"]
    assert cfg.pulses.light.expires_in_ms == 300
    assert cfg.planner.active_seconds_cap == 25
    assert cfg.calibration.quantile == 0.975 and cfg.calibration.min_genuine == 10
    assert cfg.quality.min == 0.5
    assert cfg.physiology.enabled is False
    assert len(config_hash()) == 64


def test_light_pulse_spacing_respects_flash_limit():
    # At most 3 flashes in any second (SPEC 6.3, 16): duration + min gap must be >= 1000/3 ms.
    light = load_config().pulses.light
    assert light.duration_ms + light.gap_ms[0] >= 1000 / 3


def test_unknown_config_key_is_rejected(tmp_path):
    bad = tmp_path / "config.yaml"
    bad.write_text(config_path().read_text() + "\ntypo_section: {x: 1}\n")
    with pytest.raises(ValidationError):
        load_config(bad)


def test_secrets_from_env_file(tmp_path, monkeypatch):
    for k in ("PULSE_HMAC_SECRET", "CONSOLE_PASSCODE", "TEAM_CODES"):
        monkeypatch.setenv(k, "")  # records the original so load_dotenv's writes are undone
        monkeypatch.delenv(k)
    env = tmp_path / ".env"
    env.write_text("PULSE_HMAC_SECRET=abc\nCONSOLE_PASSCODE=\nTEAM_CODES=P01, P02\n")
    s = load_secrets(env)
    assert s.pulse_hmac_secret.get_secret_value() == "abc"
    assert s.console_passcode is None
    assert s.team_codes == ["P01", "P02"]
    assert "abc" not in repr(s)
