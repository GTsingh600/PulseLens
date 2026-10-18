"""Download the model files PulseLens needs into models/ (gitignored).

Idempotent: files already present are kept. Writes models/MANIFEST.json with the URL, size and
sha256 of each file so a session can record exactly which model produced its results.

ArcFace (insightface buffalo_l) and CLIP (open_clip ViT-B-32) are fetched by their own libraries
on first use via `pulselens/vision/models.py`, after `make setup-ml`.

Usage: python scripts/fetch_models.py [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
BASE = "https://storage.googleapis.com/mediapipe-models"

FILES = {
    # Server: SPEC 8.1 face.py and hand.py
    "face_landmarker.task": f"{BASE}/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
    "hand_landmarker.task": f"{BASE}/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    # Client: SPEC 6.4 coaching FaceDetector (served locally so the venue Wi-Fi isn't a dependency)
    "blaze_face_short_range.tflite": (
        f"{BASE}/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.replace(dest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="only report which files are present")
    args = parser.parse_args()

    MODELS.mkdir(exist_ok=True)
    manifest: dict[str, dict[str, object]] = {}
    failed = []
    for name, url in FILES.items():
        dest = MODELS / name
        if not dest.exists() and not args.check:
            print(f"downloading {name} ...", flush=True)
            try:
                download(url, dest)
            except OSError as e:
                print(f"  FAILED: {e}")
                failed.append(name)
                continue
        if dest.exists():
            manifest[name] = {
                "url": url,
                "bytes": dest.stat().st_size,
                "sha256": sha256(dest),
            }
            print(f"ok      {name}  {manifest[name]['bytes']} bytes")
        else:
            print(f"missing {name}")
            failed.append(name)

    if not args.check:
        (MODELS / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if failed:
        print(f"\n{len(failed)} model file(s) missing. Checks that need them abstain until you re-run this.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
