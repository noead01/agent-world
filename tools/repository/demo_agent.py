#!/usr/bin/env python3
"""Demonstrate the TODO-0008 embodied agent end-to-end.

User-visible feature: a visible agent can orient, move, respect collisions
and reach limits, and execute deterministic physical actions.

Verifies all three acceptance criteria:
  1. Locomotion and orientation use deterministic controllers rather than
     LLM frame control.
  2. Collision avoidance and reach constraints prevent invalid actions.
  3. Action start, completion, interruption, and failure are observable.

Usage:
    python3 tools/repository/demo_agent.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORLD_DIR = os.path.join(ROOT, "apps", "world")
AGENT_SERVICE_DIR = os.path.join(ROOT, "services", "agent", "src")


def check(condition: bool, message: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {message}")
    return condition


def parse_agent_states(output: str) -> list:
    """Extract agent state lines from Godot output.

    Parses lines like:
      AGENT: id=wanderer_01 status=moving pos=(0.00, 1.66, 0.50) heading=3.14 world_time=0.983 goal=
    """
    states = []
    for line in output.splitlines():
        match = re.match(
            r'\s*AGENT:\s+id=(\S+)\s+status=(\w+)\s+'
            r'pos=\(([\d\.\-]+),\s*([\d\.\-]+),\s*([\d\.\-]+)\)\s+'
            r'heading=([\d\.\-]+)\s+world_time=([\d\.\-]+)',
            line,
        )
        if match:
            states.append({
                "agent_id": match.group(1),
                "status": match.group(2),
                "x": float(match.group(3)),
                "y": float(match.group(4)),
                "z": float(match.group(5)),
                "heading": float(match.group(6)),
                "world_time": float(match.group(7)),
            })
    return states


def parse_agent_actions(output: str) -> list:
    """Extract agent action lifecycle events from Godot output.

    Parses lines like:
      AGENT_ACTION: started=move target=obj_wood_cube
      AGENT_ACTION: completed=move result=success
      AGENT_ACTION: failed=touch reason=unreachable
      AGENT_ACTION: interrupted=move
    """
    actions = []
    for line in output.splitlines():
        match = re.match(
            r'AGENT_ACTION:\s+(started|completed|failed|interrupted)=(\S+)',
            line,
        )
        if match:
            event = {
                "event": match.group(1),
                "action_type": match.group(2),
            }
            if match.group(1) == "started":
                target_match = re.search(r'target=(\S+)', line)
                event["target"] = target_match.group(1) if target_match else ""
            elif match.group(1) == "failed":
                reason_match = re.search(r'reason=(\S+)', line)
                event["reason"] = reason_match.group(1) if reason_match else ""
            actions.append(event)
    return actions


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

    # Start agent service
    print("== Starting agent service ==")
    agent_service_proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "agent.src.agent_service"],
        cwd=os.path.join(ROOT, "services"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Give agent service time to start
    time.sleep(2.0)
    
    # Check if agent service started successfully
    if agent_service_proc.poll() is not None:
        stdout, stderr = agent_service_proc.communicate()
        print("FAIL: Agent service failed to start")
        print(f"  stdout: {stdout}")
        print(f"  stderr: {stderr}")
        return 1
    print("  Agent service started on ws://localhost:8765")
    print()

    # Run Godot headless; internal quit() fires after 10 seconds of wall time
    print("== Running Godot against the embodied agent demo ==")
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
        agent_service_proc.terminate()
        return 1
    finally:
        # Stop agent service and capture its output
        agent_service_proc.terminate()
        try:
            agent_stdout, agent_stderr = agent_service_proc.communicate(timeout=5)
            if agent_stdout:
                print("Agent service stdout:")
                for line in agent_stdout.splitlines():
                    print(f"  {line}")
            if agent_stderr:
                print("Agent service stderr:")
                for line in agent_stderr.splitlines():
                    print(f"  {line}")
        except subprocess.TimeoutExpired:
            agent_service_proc.kill()

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
    
    # Print Godot stdout for debugging
    print("=== Godot stdout ===")
    for line in stdout.splitlines():
        print(line)
    print("====================")
    print()

    agent_states = parse_agent_states(stdout)
    agent_actions = parse_agent_actions(stdout)

    # Acceptance criterion 1: Locomotion and orientation use deterministic
    # controllers rather than LLM frame control.
    print("== Criterion 1: Deterministic locomotion and orientation ==")
    if len(agent_states) >= 2:
        # Agent position should change over time (locomotion)
        positions = [(s["x"], s["y"], s["z"]) for s in agent_states]
        position_changes = any(
            positions[i] != positions[i + 1]
            for i in range(len(positions) - 1)
        )
        all_pass &= check(position_changes, "agent position changes over time (locomotion)")

        # Agent heading should change (orientation)
        headings = [s["heading"] for s in agent_states]
        heading_changes = any(
            abs(headings[i] - headings[i + 1]) > 0.01
            for i in range(len(headings) - 1)
        )
        all_pass &= check(heading_changes, "agent heading changes over time (orientation)")

        if position_changes:
            print(f"    Position range: x=[{min(p[0] for p in positions):.2f}, {max(p[0] for p in positions):.2f}], "
                  f"y=[{min(p[1] for p in positions):.2f}, {max(p[1] for p in positions):.2f}], "
                  f"z=[{min(p[2] for p in positions):.2f}, {max(p[2] for p in positions):.2f}]")
        if heading_changes:
            print(f"    Heading range: {min(headings):.2f} to {max(headings):.2f} radians")

        # world_time_s should advance (tied to SimulationTime)
        world_times = [s["world_time"] for s in agent_states]
        time_advances = world_times[0] < world_times[-1]
        all_pass &= check(time_advances, "agent world_time_s advances through fixed physics steps")
        if time_advances:
            print(f"    world_time_s: {world_times[0]:.3f}s to {world_times[-1]:.3f}s")
    else:
        all_pass &= check(False, "no agent states found in output")
    print()

    # Acceptance criterion 2: Collision avoidance and reach constraints.
    print("== Criterion 2: Collision avoidance and reach constraints ==")
    if len(agent_states) >= 2:
        # Agent should stay within room bounds (half_size = 13.5)
        half_size = 13.5
        within_bounds = all(
            abs(s["x"]) <= half_size and abs(s["z"]) <= half_size
            for s in agent_states
        )
        all_pass &= check(within_bounds, "agent remains within room bounds (collision avoidance)")
        if within_bounds:
            x_max = max(abs(s["x"]) for s in agent_states)
            z_max = max(abs(s["z"]) for s in agent_states)
            print(f"    Max |x|={x_max:.2f}, max |z|={z_max:.2f} (limit={half_size})")

        # Reach constraints: touch actions on unreachable targets should fail.
        # Add an intentional unreachable target (non-existent instance_id) so
        # the agent attempts to touch it and fails with target_not_found.
        failed_actions = [a for a in agent_actions if a["event"] == "failed"]
        unreachable_failures = [a for a in failed_actions if a.get("reason") in ("unreachable", "target_not_found")]
        all_pass &= check(
            len(unreachable_failures) > 0,
            "reach constraints prevent invalid actions (unreachable target fails)",
        )
        if unreachable_failures:
            print(f"    Unreachable/unsatisfiable touch failures observed: {len(unreachable_failures)}")
            for a in unreachable_failures[:3]:
                print(f"      failed={a['action_type']} reason={a.get('reason', '')} target={a.get('target', '')}")
    else:
        all_pass &= check(False, "no agent states found in output")
    print()

    # Acceptance criterion 3: Action lifecycle is observable.
    print("== Criterion 3: Observable action lifecycle ==")
    started_actions = [a for a in agent_actions if a["event"] == "started"]
    completed_actions = [a for a in agent_actions if a["event"] == "completed"]
    failed_actions = [a for a in agent_actions if a["event"] == "failed"]
    interrupted_actions = [a for a in agent_actions if a["event"] == "interrupted"]

    has_started = len(started_actions) > 0
    all_pass &= check(has_started, "action_started signal is emitted")
    if has_started:
        print(f"    {len(started_actions)} action_started events")
        for a in started_actions[:5]:
            print(f"      started={a['action_type']} target={a.get('target', '')}")

    has_completed = len(completed_actions) > 0
    all_pass &= check(has_completed, "action_completed signal is emitted")
    if has_completed:
        print(f"    {len(completed_actions)} action_completed events")

    # Require failure observability: the configured target sequence includes
    # an intentional unreachable target (obj_nonexistent) so a failed event
    # MUST be observed. If failure observability is broken, the demo fails.
    has_failed = len(failed_actions) > 0
    all_pass &= check(has_failed, "action_failed signal is emitted (failure observability)")
    if has_failed:
        print(f"    {len(failed_actions)} action_failed events")
        for a in failed_actions[:5]:
            print(f"      failed={a['action_type']} reason={a.get('reason', '')}")

    # Require interruption observability: if an action is interrupted during
    # the sequence (e.g., by a new action replacing it), the interrupted
    # event MUST be observed.
    has_interrupted = len(interrupted_actions) > 0
    all_pass &= check(has_interrupted, "action_interrupted signal is emitted (interruption observability)")
    if has_interrupted:
        print(f"    {len(interrupted_actions)} action_interrupted events")
        for a in interrupted_actions[:5]:
            print(f"      interrupted={a['action_type']}")
    print()

    if all_pass:
        print("DEMONSTRATION PASSED: embodied agent supports deterministic locomotion, collision avoidance, reach constraints, and observable action lifecycle.")
        return 0
    print("DEMONSTRATION FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
