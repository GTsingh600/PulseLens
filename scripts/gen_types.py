"""Write client/src/shared/types.ts from server/pulselens/models.py. Run with `make types`."""

from pathlib import Path

from pulselens.tsgen import render

OUT = Path(__file__).resolve().parents[1] / "client" / "src" / "shared" / "types.ts"

if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")
