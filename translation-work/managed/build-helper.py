"""Explicit offline helper build; never installs files or approves a runtime profile."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
CECIL = "vendor/mono-cecil-0.11.6/Mono.Cecil.dll"
CECIL_SHA256 = "c41bdb9ffd3c5f6e17d2382c1012d73703e035e3f1100245fdd4e08c8dc6eb5b"
FILES = ["managed/GrammarTool.cs", "managed/Launcher.cs", "managed/GrammarTool.exe",
         "managed/engine-shapes.json", "managed/build-helper.py", "managed/build-helper.ps1", CECIL]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Recompile even when the pinned inputs match")
    args = parser.parse_args()
    repo = WORK.parent.resolve()
    if any((p / "StarDynasties.exe").exists() and (p / "StarDynasties_Data").is_dir()
           for p in [repo, *repo.parents]):
        raise ValueError("The game installation is read-only; use the translation repository")
    if sha(WORK / CECIL) != CECIL_SHA256:
        raise ValueError("Mono.Cecil does not match the pinned official package")
    for name in FILES:
        if name.endswith((".cs", ".py", ".ps1", ".json")):
            raw = (WORK / name).read_bytes()
            raw.decode("utf-8", errors="strict")
            if b"\r" in raw:
                raise ValueError("Engineering inputs must use canonical LF before hashing: " + name)
    lock_path = WORK / "managed/toolchain.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    fingerprints = {name: sha(WORK / name) for name in FILES}
    if not args.force and lock.get("files") == fingerprints and b"\r" not in lock_path.read_bytes():
        print("unchanged: helper and canonical LF source hashes match")
        return 0
    if os.name == "nt":
        compiler = Path(os.environ.get("WINDIR", "C:/Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        if not compiler.is_file():
            raise ValueError("Missing .NET Framework 4.x C# compiler")
        flags = ["/nologo", "/optimize+", "/target:exe", "/platform:anycpu", "/main:Launcher"]
        output_flag, reference_flag = "/out:", "/reference:"
    else:
        compiler = shutil.which("mcs")
        if not compiler:
            raise ValueError("Offline rebuilding requires the Mono mcs compiler (mono-devel)")
        flags = ["-nologo", "-optimize+", "-target:exe", "-platform:anycpu", "-main:Launcher"]
        output_flag, reference_flag = "-out:", "-r:"
    state = WORK / ".state"
    state.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="helper-build-", dir=state) as staging:
        output = Path(staging) / "GrammarTool.exe"
        command = [str(compiler), *flags, output_flag + str(output),
                   reference_flag + str(WORK / CECIL), reference_flag + "System.Web.Extensions.dll",
                   str(WORK / "managed/GrammarTool.cs"), str(WORK / "managed/Launcher.cs")]
        subprocess.run(command, check=True)
        os.replace(output, WORK / "managed/GrammarTool.exe")
    lock["compiler"] = "C# compiler (.NET Framework csc / Mono mcs); AnyCPU"
    lock["files"] = {name: sha(WORK / name) for name in FILES}
    lock_path.write_bytes((json.dumps(lock, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    print("Helper rebuilt with LF fingerprints. Run the tests and review runtime-support.json before a native build.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit("ERROR: " + str(error))
