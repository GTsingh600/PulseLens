import io

import numpy as np
import pytest
from PIL import Image

from tests.fixtures import synth


def test_frame_times_strictly_increasing_with_jitter():
    t = synth.frame_times(300, fps=30, jitter_ms=3, seed=1)
    assert np.all(np.diff(t) > 0)
    assert abs(np.median(np.diff(t)) - 1000 / 30) < 1.0


def test_frame_times_rejects_jitter_that_could_reorder():
    with pytest.raises(ValueError):
        synth.frame_times(10, fps=30, jitter_ms=20)


def test_flat_frame_noise_level():
    clean = synth.flat_frame(noise_sigma=0)
    noisy = synth.flat_frame(noise_sigma=3, seed=2)
    assert clean.std() == 0
    assert 2.5 < noisy.astype(float).std() < 3.5


def test_jpeg_round_trip_size():
    img = Image.open(io.BytesIO(synth.jpeg_bytes(synth.textured_frame())))
    assert img.size == (480, 360)


def test_light_pulse_timing_order():
    p = synth.light_pulse("p_1", "red", painted=5000.0)
    assert p.received <= p.applied <= p.painted < p.ended
