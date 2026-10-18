"""Synthetic fixtures for unit tests. No network, no real faces.

Skeleton from M1.1. Track B extends it (ROI-mean echo signals for M1.4, textured shifts for M2.3)
and M1.5 adds `python -m tests.fixtures.synth --bundle <dir>` to write a full session bundle.
All times are client-clock ms, like `performance.now()`.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from pulselens.models import (
    ClientInfo,
    FrameRecord,
    GyroInfo,
    PulseRecord,
    ScreenInfo,
    SessionMeta,
)


def rng(seed: int = 0) -> np.random.Generator:
    return np.random.default_rng(seed)


def frame_times(
    n: int, fps: float = 30.0, jitter_ms: float = 0.0, start_ms: float = 1000.0, seed: int = 0
) -> np.ndarray:
    """n strictly increasing frame times at `fps` with uniform +/- jitter_ms."""
    period = 1000.0 / fps
    if jitter_ms >= period / 2:
        raise ValueError("jitter must be < half the frame period to keep times increasing")
    t = start_ms + period * np.arange(n, dtype=float)
    if jitter_ms > 0:
        t += rng(seed).uniform(-jitter_ms, jitter_ms, size=n)
    return t


def flat_frame(
    h: int = 360,
    w: int = 480,
    rgb: tuple[int, int, int] = (128, 128, 128),
    noise_sigma: float = 0.0,
    seed: int = 0,
) -> np.ndarray:
    """HxWx3 uint8 frame of one colour, with optional Gaussian sensor-like noise."""
    img = np.empty((h, w, 3), dtype=float)
    img[:] = rgb
    if noise_sigma > 0:
        img += rng(seed).normal(0.0, noise_sigma, size=img.shape)
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def textured_frame(h: int = 360, w: int = 480, block: int = 8, seed: int = 0) -> np.ndarray:
    """Random grey blocks: enough corners for optical-flow tracking."""
    small = rng(seed).integers(0, 256, size=(h // block + 1, w // block + 1), dtype=np.uint8)
    grey = np.kron(small, np.ones((block, block), dtype=np.uint8))[:h, :w]
    return np.repeat(grey[:, :, None], 3, axis=2)


def jpeg_bytes(frame: np.ndarray, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(frame).save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def frame_records(times: np.ndarray, w: int = 480, h: int = 360) -> list[FrameRecord]:
    return [
        FrameRecord(i=i, t=float(t), capture_time=float(t), presented_frames=i, w=w, h=h, file=f"{i:06d}.jpg")
        for i, t in enumerate(times)
    ]


def light_pulse(
    pulse_id: str, colour: str, painted: float, duration_ms: float = 400.0, source: str = "planner"
) -> PulseRecord:
    """A light pulse record with consistent received <= applied <= painted < ended."""
    return PulseRecord(
        pulse_id=pulse_id,
        kind="light",
        source=source,  # type: ignore[arg-type]
        params={"colour": colour, "duration_ms": duration_ms, "region": "fullscreen"},
        received=painted - 20.0,
        applied=painted - 16.7,
        painted=painted,
        ended=painted + duration_ms,
        ok=True,
    )


def client_info(mobile: bool = False, camera_label: str = "Integrated Camera") -> ClientInfo:
    return ClientInfo(
        user_agent="synthetic",
        ua_mobile=mobile,
        pointer_coarse=mobile,
        screen=ScreenInfo(w=412, h=915, dpr=2.6) if mobile else ScreenInfo(w=1920, h=1080, dpr=1.0),
        camera_label=camera_label,
        track_settings={"width": 480 if mobile else 640, "height": 360 if mobile else 480, "frameRate": 30},
        has_rvfc=True,
        clock_source="captureTime",
        gyro=GyroInfo(available=mobile, permission="granted" if mobile else "not_needed"),
    )


def session_meta(session_id: str = "s_20261024_143012_ab12", mobile: bool = False) -> SessionMeta:
    return SessionMeta(
        session_id=session_id,
        created_server_iso="2026-10-24T14:30:12+05:30",
        mode="live",
        product="instant_loan",
        client=client_info(mobile=mobile),
    )
