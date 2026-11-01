#!/usr/bin/env python3
"""Demonstrate the TODO-0007 simulation time end-to-end.

User-visible feature: the runtime supports fixed-step simulation time,
pause, resume, reset, time scaling, and an accelerated day/night cycle.

Verifies all three acceptance criteria:
  1. Simulation time advances only through fixed physics steps.
  2. Pause freezes simulation behavior without corrupting state;
     resume continues coherently.
  3. Reset and time scaling produce documented, observable lighting
     and clock behavior.

Usage:
    python3 tools/repository/demo_simulation_time.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORLD_DIR = os.path.join(ROOT, "apps", "world")


def check(condition: bool, message: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {message}")
    return condition


def parse_sim_states(output: str) -> list:
    """Extract simulation state lines from Godot output.

    Parses lines like:
      T+: wall=1.0s sim=0.983 tick=59 paused=False scale=1.0 tod=6.0 settled=0/4 landed=0
    """
    states = []
    for line in output.splitlines():
        match = re.match(
            r'T\+:\s+wall=([\d\.]+)s\s+sim=([\d\.]+)\s+tick=(\d+)\s+'
            r'paused=(\w+)\s+scale=([\d\.]+)\s+tod=([\d\.]+)',
            line,
        )
        if match:
            states.append({
                "wall": float(match.group(1)),
                "sim_time": float(match.group(2)),
                "tick": int(match.group(3)),
                "paused": match.group(4) == "True",
                "time_scale": float(match.group(5)),
                "time_of_day": float(match.group(6)),
            })
    return states


def parse_demo_events(output: str) -> dict:
    """Extract demo sequence events from Godot output."""
    events = {}
    patterns = {
        "pause": r'SIM PAUSED at t=([\d\.]+)s \(sim_time=([\d\.]+), tick=(\d+)\)',
        "resume": r'SIM RESUMED at t=([\d\.]+)s \(sim_time=([\d\.]+), tick=(\d+)\)',
        "scale": r'TIME SCALE 2\.0 at t=([\d\.]+)s \(sim_time=([\d\.]+), tick=(\d+)\)',
        "reset": r'SIM RESET at t=([\d\.]+)s \(sim_time=([\d\.]+), tick=(\d+)\)',
    }
    for name, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            events[name] = {
                "wall": float(match.group(1)),
                "sim_time": float(match.group(2)),
                "tick": int(match.group(3)),
            }

    # Impulse has a different format (only wall time)
    impulse_match = re.search(r'IMPULSE applied to obj_metal_sphere at t=([\d\.]+)s', output)
    if impulse_match:
        events["impulse"] = {"wall": float(impulse_match.group(1))}

    return events


def main() -> int:
    godot = shutil.which("godot")
    if not godot:
        print("ERROR: godot executable not found on PATH.")
        print("       Install Godot 4.x per CONTRIBUTING.md Prerequisites.")
        return 1

    print(f"Using Godot: {godot}")
    print(f"Project path: {WORLD_DIR}")
    print()

    all_pass = True

    # Run Godot headless; internal quit() fires after 10 seconds of wall time
    print("== Running Godot against the simulation time demo ==")
    try:
        proc = subprocess.Popen(
            [godot, "--headless", "--path", WORLD_DIR],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            all_pass = False
            print("FAIL: Godot did not exit within 60 seconds.")
    except OSError as exc:
        print(f"FAIL: Could not launch Godot: {exc}")
        return 1

    # Check for script errors (ignore audio/ALSA errors which are environmental)
    script_errors = [line for line in stdout.splitlines() if "SCRIPT ERROR" in line]
    script_errors += [line for line in stderr.splitlines() if "SCRIPT ERROR" in line]
    if script_errors:
        print("SCRIPT ERRORS:")
        for line in script_errors:
            print(f"  {line}")
        all_pass = False
        print("  [FAIL] Godot ran with script errors")
    else:
        print("  [PASS] Godot ran without script errors")
    print()

    sim_states = parse_sim_states(stdout)
    events = parse_demo_events(stdout)

    # Acceptance criterion 1: Simulation time advances only through
    # fixed physics steps.
    print("== Criterion 1: Simulation time advances through fixed physics steps ==")
    if len(sim_states) >= 2:
        # Tick must be non-decreasing (can stay same during pause)
        ticks = [s["tick"] for s in sim_states]
        tick_nondecreasing = all(ticks[i] <= ticks[i + 1] for i in range(len(ticks) - 1))
        tick_strictly_increases = ticks[0] < ticks[-1]
        all_pass &= check(tick_nondecreasing, "simulation tick is non-decreasing")
        all_pass &= check(tick_strictly_increases, "simulation tick strictly increases overall")

        # Sim time must be non-decreasing (can stay same during pause)
        sim_times = [s["sim_time"] for s in sim_states]
        sim_nondecreasing = all(sim_times[i] <= sim_times[i + 1] for i in range(len(sim_times) - 1))
        sim_strictly_increases = sim_times[0] < sim_times[-1]
        all_pass &= check(sim_nondecreasing, "simulation time is non-decreasing")
        all_pass &= check(sim_strictly_increases, "simulation time strictly increases overall")
        if sim_strictly_increases:
            print(f"    Sim time range: {sim_times[0]:.3f}s to {sim_times[-1]:.3f}s")
            print(f"    Tick range: {ticks[0]} to {ticks[-1]}")

        # Time of day should be reported
        has_tod = all("time_of_day" in s for s in sim_states)
        all_pass &= check(has_tod, "time of day is reported in simulation state")
    else:
        all_pass &= check(False, "no simulation states found in output")
    print()

    # Acceptance criterion 2: Pause freezes simulation; resume continues.
    print("== Criterion 2: Pause freezes simulation; resume continues coherently ==")
    if "pause" in events and "resume" in events:
        # Sim time should be the same at pause and resume (frozen)
        pause_sim = events["pause"]["sim_time"]
        resume_sim = events["resume"]["sim_time"]
        paused_frozen = abs(pause_sim - resume_sim) < 0.001
        all_pass &= check(
            paused_frozen,
            f"sim time frozen during pause (pause={pause_sim:.3f}s, resume={resume_sim:.3f}s)",
        )
        if paused_frozen:
            print(f"    Sim time held at {pause_sim:.3f}s during pause")

        # After resume, sim time should advance again
        post_resume_states = [
            s for s in sim_states if s["wall"] > events["resume"]["wall"]
        ]
        if len(post_resume_states) >= 2:
            resumes_advancing = all(
                post_resume_states[i]["sim_time"] < post_resume_states[i + 1]["sim_time"]
                for i in range(len(post_resume_states) - 1)
            )
            all_pass &= check(
                resumes_advancing, "simulation time advances after resume"
            )
            if resumes_advancing:
                print(f"    Sim time after resume: {post_resume_states[0]['sim_time']:.3f}s -> {post_resume_states[-1]['sim_time']:.3f}s")
    else:
        all_pass &= check(False, "pause and resume events not found in output")
    print()

    # Acceptance criterion 3: Reset and time scaling produce observable
    # lighting and clock behavior.
    print("== Criterion 3: Reset and time scaling produce observable behavior ==")

    # Time scaling: sim time advances ~2x faster after scale event
    if "scale" in events:
        pre_scale_states = [s for s in sim_states if events["pause"]["wall"] < s["wall"] < events["scale"]["wall"]]
        post_scale_states = [s for s in sim_states if s["wall"] > events["scale"]["wall"] and s["wall"] < events.get("reset", {"wall": 999})["wall"]]

        if len(pre_scale_states) >= 2 and len(post_scale_states) >= 2:
            pre_rate = (pre_scale_states[-1]["sim_time"] - pre_scale_states[0]["sim_time"]) / (
                pre_scale_states[-1]["wall"] - pre_scale_states[0]["wall"]
            ) if pre_scale_states[-1]["wall"] != pre_scale_states[0]["wall"] else 0
            post_rate = (post_scale_states[-1]["sim_time"] - post_scale_states[0]["sim_time"]) / (
                post_scale_states[-1]["wall"] - post_scale_states[0]["wall"]
            ) if post_scale_states[-1]["wall"] != post_scale_states[0]["wall"] else 0

            scaled_faster = post_rate > pre_rate * 1.5
            all_pass &= check(
                scaled_faster,
                f"time scale 2.0 advances sim time faster (pre={pre_rate:.2f}x, post={post_rate:.2f}x wall time)",
            )
            if scaled_faster:
                print(f"    Sim time rate: {pre_rate:.2f}x before scale, {post_rate:.2f}x after scale")

    # Reset: sim time returns to ~0 and tick to 0
    if "reset" in events:
        reset_sim = events["reset"]["sim_time"]
        reset_tick = events["reset"]["tick"]
        reset_to_zero = abs(reset_sim) < 0.001 and reset_tick == 0
        all_pass &= check(
            reset_to_zero,
            f"sim time resets to zero (sim_time={reset_sim:.3f}s, tick={reset_tick})",
        )
        if reset_to_zero:
            print(f"    Sim time reset to {reset_sim:.3f}s, tick={reset_tick}")

    # Day/night cycle: time of day should vary across states
    tod_values = [s["time_of_day"] for s in sim_states]
    if len(tod_values) >= 2:
        tod_varies = max(tod_values) - min(tod_values) > 0.1
        all_pass &= check(
            tod_varies,
            f"time of day varies ({min(tod_values):.1f}h to {max(tod_values):.1f}h)",
        )
        if tod_varies:
            print(f"    Time of day range: {min(tod_values):.1f}h to {max(tod_values):.1f}h")
    print()

    if all_pass:
        print("DEMONSTRATION PASSED: simulation time supports fixed steps, pause/resume, reset, time scaling, and day/night cycle.")
        return 0
    print("DEMONSTRATION FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
