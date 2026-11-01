#!/usr/bin/env python3
"""Demonstrate the TODO-0003 browser prototype retirement end-to-end.

User-visible feature: the Three.js prototype no longer creates ambiguity
about the active runtime, while useful reference material remains
accessible under an explicitly archived location.

Verifies all three acceptance criteria:
  1. Godot is the only documented active runtime.
  2. Prototype files are removed or isolated under an explicitly archived location.
  3. No active build or contributor instruction depends on the prototype.

Usage:
    python3 tools/repository/demo_prototype_retirement.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check(condition: bool, message: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {message}")
    return condition


def main() -> int:
    all_pass = True

    print("== TODO-0003: Browser prototype retirement demonstration ==")
    print()

    # Acceptance criterion 2: prototype files isolated under archive/.
    print("== Criterion 2: Prototype isolated under an explicitly archived location ==")
    archived = os.path.join(ROOT, "archive", "apps", "browser-prototype")
    active = os.path.join(ROOT, "apps", "browser-prototype")
    all_pass &= check(os.path.isdir(archived), "archive/apps/browser-prototype/ exists")
    all_pass &= check(os.path.isfile(os.path.join(archived, "README.md")), "archived prototype has a README")
    all_pass &= check(not os.path.exists(active), "apps/browser-prototype/ no longer exists under apps/")
    print()

    # Acceptance criterion 3: no active build or contributor instruction depends on prototype.
    print("== Criterion 3: No active build or contributor instruction depends on prototype ==")
    components_mk = os.path.join(ROOT, "build", "components.mk")
    components_text = open(components_mk, encoding="utf-8").read()
    all_pass &= check("browser-prototype" not in components_text, "prototype not in build/components.mk")

    contributing = os.path.join(ROOT, "CONTRIBUTING.md")
    contributing_text = open(contributing, encoding="utf-8").read()
    all_pass &= check("cd apps/browser-prototype" not in contributing_text, "CONTRIBUTING has no prototype run instructions")
    all_pass &= check("npm install" not in contributing_text, "CONTRIBUTING has no npm install for prototype")
    all_pass &= check("npm run dev" not in contributing_text, "CONTRIBUTING has no npm run dev for prototype")
    print()

    # Acceptance criterion 1: Godot is the only documented active runtime.
    print("== Criterion 1: Godot is the only documented active runtime ==")
    all_pass &= check("Godot 4 with Jolt is the supported world runtime" in contributing_text,
                      "CONTRIBUTING names Godot as the only active runtime")
    godot = shutil.which("godot")
    if godot:
        print(f"  Using Godot: {godot}")
        try:
            result = subprocess.run(
                [godot, "--headless", "--path", os.path.join(ROOT, "apps", "world"),
                 "--quit-after", "1"],
                capture_output=True, text=True, timeout=60,
            )
            output = result.stdout + result.stderr
            all_pass &= check("ERROR" not in output, "Godot project opens without import/config errors")
            all_pass &= check("Physics engine: JoltPhysics" in output, "Jolt physics selected")
            all_pass &= check("Fixed timestep: 60 Hz" in output, "Fixed timestep explicit")
            all_pass &= check("Runtime: Godot 4." in output, "Main scene runs and reports runtime version")
        except (subprocess.TimeoutExpired, OSError) as exc:
            all_pass = False
            print(f"  [FAIL] Could not run Godot headless: {exc}")
    else:
        print("  [SKIP] godot not on PATH; skipping runtime execution check")
        print("         Install Godot 4.x per CONTRIBUTING.md Prerequisites to run this check")
    print()

    # Repository layout summary.
    print("== Active component listing ==")
    try:
        result = subprocess.run(
            ["make", "--no-print-directory", "components"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        print(result.stdout)
        all_pass &= check("browser-prototype" not in result.stdout,
                          "prototype not listed as an active component")
    except FileNotFoundError:
        print("  [SKIP] make not available")
    print()

    if all_pass:
        print("DEMONSTRATION PASSED: prototype archived, Godot is the only active runtime.")
        return 0
    print("DEMONSTRATION FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
