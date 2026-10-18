"""Typed loader for `config.yaml` (SPEC 17) and secrets from `.env`.

Unknown keys are rejected, so a typo in config.yaml fails at startup instead of being ignored.
"""

from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr

REPO_ROOT = Path(__file__).resolve().parents[2]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CaptureCfg(_Strict):
    desktop_size: tuple[int, int]
    mobile_size: tuple[int, int]
    jpeg_quality: float = Field(gt=0, le=1)
    upload_batch_ms: int
    queue_max: int


class LightCfg(_Strict):
    count: int
    duration_ms: int
    gap_ms: tuple[int, int]
    colours: list[str]
    desktop_border_frac: float
    expires_in_ms: int


class LensCfg(_Strict):
    steps: int
    ev_delta: float


class TiltCfg(_Strict):
    duration_ms: int
    min_peak_dps: float


class HandCfg(_Strict):
    duration_ms: int


class PulsesCfg(_Strict):
    light: LightCfg
    lens: LensCfg
    tilt: TiltCfg
    hand: HandCfg
    release_jitter_ms: tuple[int, int]
    agent_fire_delay_ms: tuple[int, int]


class ProfilesCfg(_Strict):
    fields: list[str]
    fps_bands: list[float]


class PlannerCfg(_Strict):
    active_seconds_cap: float
    max_rounds: int
    families_per_threat: int


class CalibrationCfg(_Strict):
    quantile: float
    min_genuine: int


class QualityCfg(_Strict):
    min: float
    min_face_frac: float
    luma_range: tuple[float, float]
    min_fps: float


class PhysiologyCfg(_Strict):
    enabled: bool


class RadarCfg(_Strict):
    room_sim: float
    other_sim: float


class Config(_Strict):
    capture: CaptureCfg
    pulses: PulsesCfg
    profiles: ProfilesCfg
    planner: PlannerCfg
    calibration: CalibrationCfg
    quality: QualityCfg
    physiology: PhysiologyCfg
    radar: RadarCfg


class Secrets(BaseModel):
    pulse_hmac_secret: SecretStr | None
    console_passcode: SecretStr | None
    team_codes: list[str]


def config_path() -> Path:
    return Path(os.environ.get("PULSELENS_CONFIG", REPO_ROOT / "config.yaml"))


def data_dir() -> Path:
    return Path(os.environ.get("PULSELENS_DATA", REPO_ROOT / "data"))


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    with open(path, encoding="utf-8") as f:
        return Config.model_validate(yaml.safe_load(f))


@lru_cache(maxsize=1)
def get_config() -> Config:
    return load_config()


def config_hash(path: Path | None = None) -> str:
    """sha256 of the raw config file; eval/freeze.py records it in eval/FROZEN."""
    return hashlib.sha256((path or config_path()).read_bytes()).hexdigest()


def load_secrets(env_file: Path | None = None) -> Secrets:
    """Read secrets from the environment, after loading `.env` if present. Missing values are None."""
    load_dotenv(env_file or REPO_ROOT / ".env", override=False)

    def _get(name: str) -> SecretStr | None:
        value = os.environ.get(name, "").strip()
        return SecretStr(value) if value else None

    codes = [c.strip() for c in os.environ.get("TEAM_CODES", "").split(",") if c.strip()]
    return Secrets(
        pulse_hmac_secret=_get("PULSE_HMAC_SECRET"),
        console_passcode=_get("CONSOLE_PASSCODE"),
        team_codes=codes,
    )
