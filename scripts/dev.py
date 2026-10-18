"""Cross-platform task runner behind the Makefile.

`make <target>` calls `python scripts/dev.py <target>`. Teammates without make (plain Windows)
can run the same command directly. Only the standard library is used, so it runs before the venv exists.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
CLIENT = ROOT / "client"
VENV = ROOT / ".venv"
PY_VERSION = "3.11"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def tool(name: str, hint: str) -> str:
    path = shutil.which(name)
    if not path:
        sys.exit(f"'{name}' not found. {hint}")
    return path


def run(cmd: list[str | Path], cwd: Path = ROOT) -> None:
    printable = " ".join(str(c) for c in cmd)
    print(f"$ {printable}", flush=True)
    code = subprocess.call([str(c) for c in cmd], cwd=cwd)
    if code != 0:
        sys.exit(code)


def npm(*args: str) -> None:
    run([tool("npm", "Install Node.js 20+."), *args], cwd=CLIENT)


def need_venv() -> Path:
    py = venv_python()
    if not py.exists():
        sys.exit("No .venv yet: run `make setup` (or `python scripts/dev.py setup`).")
    return py


def pip_install(spec: str) -> None:
    py = venv_python()
    uv = shutil.which("uv")
    if uv:
        run([uv, "pip", "install", "--python", py, "-e", spec])
    else:
        run([py, "-m", "pip", "install", "-e", spec])


# -- targets ------------------------------------------------------------------


def setup(_: list[str]) -> None:
    if not venv_python().exists():
        uv = shutil.which("uv")
        if uv:
            run([uv, "venv", "--python", PY_VERSION, VENV])
        else:
            if sys.version_info[:2] != (3, 11):
                print(f"warning: using Python {sys.version.split()[0]}; the project targets {PY_VERSION}")
            run([sys.executable, "-m", "venv", VENV])
            run([venv_python(), "-m", "pip", "install", "--upgrade", "pip"])
    pip_install(f"{SERVER}[dev,vision]")
    npm("ci" if (CLIENT / "package-lock.json").exists() else "install")
    run([venv_python(), ROOT / "scripts" / "fetch_models.py"])
    print("\nSetup done. Copy .env.example to .env and fill in the secrets before running the server.")


def setup_ml(_: list[str]) -> None:
    need_venv()
    pip_install(f"{SERVER}[ml]")


def server(args: list[str]) -> None:
    py = need_venv()
    run([py, "-m", "uvicorn", "pulselens.api.main:app", "--port", "8000", "--reload",
         "--reload-dir", SERVER / "pulselens", *args])  # fmt: skip


def client(args: list[str]) -> None:
    npm("run", "dev", *(["--", *args] if args else []))


def tunnel(_: list[str]) -> None:
    exe = tool(
        "cloudflared",
        "Install it: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/",
    )
    run([exe, "tunnel", "--url", "http://localhost:5173"])


def test(args: list[str]) -> None:
    run([need_venv(), "-m", "pytest", *args], cwd=SERVER)


def test_client(_: list[str]) -> None:
    npm("run", "typecheck")
    npm("run", "test")


def e2e(args: list[str]) -> None:
    npm("exec", "--", "playwright", "install", "chromium")
    npm("run", "e2e", *(["--", *args] if args else []))


def lint(_: list[str]) -> None:
    py = need_venv()
    paths = [SERVER, ROOT / "scripts"]
    run([py, "-m", "ruff", "check", *paths])
    run([py, "-m", "ruff", "format", "--check", *paths])
    npm("run", "lint")


def fmt(_: list[str]) -> None:
    py = need_venv()
    paths = [SERVER, ROOT / "scripts"]
    run([py, "-m", "ruff", "check", "--fix", *paths])
    run([py, "-m", "ruff", "format", *paths])
    npm("run", "lint", "--", "--fix")


def types(_: list[str]) -> None:
    run([need_venv(), ROOT / "scripts" / "gen_types.py"])


TARGETS = {
    "setup": setup,
    "setup-ml": setup_ml,
    "server": server,
    "client": client,
    "tunnel": tunnel,
    "test": test,
    "test-client": test_client,
    "e2e": e2e,
    "lint": lint,
    "format": fmt,
    "types": types,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="extra args passed to the underlying tool",
    )
    ns = parser.parse_args()
    TARGETS[ns.target](ns.args)


if __name__ == "__main__":
    main()
