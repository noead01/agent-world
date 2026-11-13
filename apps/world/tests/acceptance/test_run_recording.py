#!/usr/bin/env python3
"""Black-box acceptance tests for Room and EventRecorder persistence."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WORLD_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORLD_DIR.parents[1] / "packages" / "contracts" / "src"))
from agent_world_contracts.run_record import RunRecord


def _run_godot(data_home, *arguments, extra_environment=None, timeout=45):
    godot = shutil.which("godot")
    assert godot, "Godot 4 must be installed to run world acceptance tests"
    environment = os.environ.copy()
    environment["XDG_DATA_HOME"] = str(data_home)
    environment.update(extra_environment or {})
    return subprocess.run(
        [godot, "--headless", "--path", str(WORLD_DIR), *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=environment,
    )


def _only_run_file(root):
    run_files = list(Path(root).rglob("run.json"))
    assert len(run_files) == 1, f"Expected one recorded run, found {run_files}"
    return run_files[0]


def test_room_persists_a_complete_run():
    """Run the public world scene and validate its actual persisted records."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        _run_godot(data_home, "--fixed-fps", "60", "--quit-after", "900")

        run_file = _only_run_file(data_home)
        record = RunRecord.load(str(run_file.parent))
        errors = record.validate()

        assert errors == [], f"Validation errors: {errors}"
        assert record.status == "completed"
        assert record.config_fingerprint
        assert record.get_events("run_started")
        assert record.get_events("run_ended")
        assert record.is_valid()
        assert all(
            current["timestamp_s"] >= previous["timestamp_s"]
            for previous, current in zip(record.events, record.events[1:])
        )


def test_recorder_failure_is_persisted_as_invalid_run():
    """Drive EventRecorder through a real schema failure in Godot."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        runs_dir = Path(temp_dir) / "failure-runs"
        _run_godot(
            data_home,
            "--script",
            "res://tests/acceptance/recorder_failure_harness.gd",
            extra_environment={"AGENT_WORLD_TEST_RUNS_DIR": str(runs_dir)},
            timeout=15,
        )

        record = RunRecord.load(str(runs_dir / "run_failure_test"))
        assert record.validate() == []
        assert record.status == "aborted"
        assert record.get_final_validity() == "invalid"
        assert not record.is_valid()


if __name__ == "__main__":
    test_room_persists_a_complete_run()
    test_recorder_failure_is_persisted_as_invalid_run()
    print("All run recording acceptance tests passed!")
