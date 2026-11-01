#!/usr/bin/env python3
"""Demonstrate the TODO-0002 Godot 4 project end-to-end.

User-visible feature: the Godot 4 world project opens without import or
configuration errors, runs its main scene, and reports the configured
physics engine (Jolt) and fixed timestep (60 Hz).

Usage:
    python3 tools/repository/demo_godot_project.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORLD_DIR = os.path.join(ROOT, "apps", "world")


def main() -> int:
    godot = shutil.which("godot")
    if not godot:
        print("ERROR: godot executable not found on PATH.")
        print("       Install Godot 4.x per CONTRIBUTING.md Prerequisites.")
        return 1

    print(f"Using Godot: {godot}")
    print(f"Project path: {WORLD_DIR}")
    print()

    print("== Running Godot headless against the world project ==")
    try:
        result = subprocess.run(
            [godot, "--headless", "--path", WORLD_DIR, "--quit-after", "1"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print("FAIL: Godot did not exit within 60 seconds.")
        return 1
    except OSError as exc:
        print(f"FAIL: Could not launch Godot: {exc}")
        return 1

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    all_pass = True

    # Acceptance criterion 1: project opens without import/config errors.
    has_error = "ERROR" in result.stdout or "ERROR" in result.stderr
    if has_error:
        all_pass = False
        print("  [FAIL] Project opened with errors")
    else:
        print("  [PASS] Project opens without import or configuration errors")

    # Acceptance criterion 2: Jolt selected + fixed timestep explicit.
    jolt_ok = "Physics engine: JoltPhysics" in result.stdout
    timestep_ok = "Fixed timestep: 60 Hz" in result.stdout
    if not jolt_ok:
        all_pass = False
        print("  [FAIL] Jolt physics not reported")
    else:
        print("  [PASS] Jolt selected for 3D physics")
    if not timestep_ok:
        all_pass = False
        print("  [FAIL] Fixed timestep not reported")
    else:
        print("  [PASS] Fixed timestep explicit (60 Hz)")

    # Acceptance criterion 3: main scene runs and reports versions.
    runtime_ok = "Runtime: Godot 4." in result.stdout
    if not runtime_ok:
        all_pass = False
        print("  [FAIL] Runtime version not reported")
    else:
        print("  [PASS] Main scene runs and reports runtime version")

    print()
    if all_pass:
        print("DEMONSTRATION PASSED: Godot project opens, runs, and reports Jolt + fixed timestep.")
        return 0
    print("DEMONSTRATION FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
