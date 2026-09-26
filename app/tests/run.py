#!/usr/bin/env python3
import pathlib, subprocess, sys

failed = []
for test in sorted(pathlib.Path(__file__).resolve().parent.glob("test_*.py")):
    r = subprocess.run([sys.executable, str(test)], capture_output=True, text=True)
    ok = r.returncode == 0 and r.stdout.strip().endswith("ok")
    print(("ok   " if ok else "FAIL ") + test.name)
    if not ok:
        failed.append(test.name)
        print(r.stdout + r.stderr)
sys.exit(1 if failed else 0)
