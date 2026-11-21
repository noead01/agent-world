#!/usr/bin/env python3
"""Black-box acceptance tests for Room and EventRecorder persistence."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

WORLD_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORLD_DIR.parents[1] / "packages" / "contracts" / "src"))
from agent_world_contracts.run_record import RunRecord


def _hello_ack(hello):
    correlation = dict(hello.get("correlation", {}))
    return {
        "type": "HelloAck",
        "protocol_version": hello.get("protocol_version", "1.0.0"),
        "server_id": "acceptance-stub",
        "accepted_capabilities": hello.get("capabilities", []),
        "initial_world_revision": correlation.get("world_revision", 0),
        "correlation": correlation,
    }


class AgentServiceStub:
    """Minimal agent service: optionally complete the Hello handshake."""

    def __init__(self, acknowledge=True, disconnect_after_ack=False, port=0):
        self._acknowledge = acknowledge
        self._disconnect_after_ack = disconnect_after_ack
        self._port = port
        self._actual_port = None
        self._server = None
        self._thread = None

    def __enter__(self):
        from websockets.sync.server import serve
        import socket

        # Create a socket with SO_REUSEADDR to avoid TIME_WAIT issues
        # Use port 0 to let OS assign a free port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", 0))
        self._actual_port = sock.getsockname()[1]
        sock.listen()
        
        self._server = serve(self._handle, sock=sock)
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()
        return self
    
    @property
    def port(self) -> int:
        return self._actual_port

    def _handle(self, connection):
        # Godot closes abruptly when the run quits; that is expected here.
        from websockets.exceptions import ConnectionClosed

        try:
            for raw in connection:
                if not self._acknowledge:
                    continue
                message = json.loads(raw)
                if message.get("type") == "Hello":
                    connection.send(json.dumps(_hello_ack(message)))
                    if self._disconnect_after_ack:
                        # Accept the handshake once, then leave the world without
                        # an agent for the rest of the run.
                        self._acknowledge = False
                        connection.close()
                        return
        except ConnectionClosed:
            return

    def __exit__(self, *_):
        self._server.shutdown()
        self._thread.join(timeout=5)


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
        with AgentServiceStub() as stub:
            _run_godot(
                data_home, 
                "--fixed-fps", "60", "--quit-after", "900",
                extra_environment={"AGENT_SERVICE_URL": f"ws://localhost:{stub.port}"}
            )

        run_file = _only_run_file(data_home)
        record = RunRecord.load(str(run_file.parent))
        errors = record.validate()

        assert errors == [], f"Validation errors: {errors}"
        assert record.status == "completed"
        assert record.config_fingerprint
        assert record.get_events("run_started")
        assert record.get_events("run_ended")
        assert record.simulation_time_s == record.events[-1]["timestamp_s"]
        impulse_events = record.get_events("object_impulse_applied")
        assert len(impulse_events) == 1
        assert impulse_events[0]["metadata"]["impulse"] == {"x": 2.0, "y": 0.0, "z": 0.0}
        # Demo controls change physics and agent timing, so each executed
        # transition must be in the authoritative stream, in execution order.
        control_events = [
            event
            for event in record.events
            if event["event_type_id"].startswith("simulation_")
        ]
        assert [event["event_type_id"] for event in control_events] == [
            "simulation_paused",
            "simulation_resumed",
            "simulation_time_scale_changed",
            "simulation_reset",
        ]
        assert control_events[2]["metadata"]["time_scale"] == 2.0
        assert record.is_valid()
        assert all(
            current["timestamp_s"] >= previous["timestamp_s"]
            for previous, current in zip(record.events, record.events[1:])
        )


def test_run_without_agent_session_is_aborted():
    """An unavailable agent service must not produce a valid-looking run."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        with AgentServiceStub(acknowledge=False) as stub:
            _run_godot(
                data_home, 
                "--fixed-fps", "60", "--quit-after", "900",
                extra_environment={"AGENT_SERVICE_URL": f"ws://localhost:{stub.port}"}
            )

        run_file = _only_run_file(data_home)
        record = RunRecord.load(str(run_file.parent))

        assert record.validate() == []
        assert record.status == "aborted"
        assert record.get_final_validity() == "invalid"
        assert not record.is_valid()
        assert not record.get_events("run_ended")


def test_run_lost_after_handshake_is_aborted():
    """A session that disconnects after HelloAck must not yield a valid run."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        with AgentServiceStub(disconnect_after_ack=True) as stub:
            _run_godot(
                data_home, 
                "--fixed-fps", "60", "--quit-after", "900",
                extra_environment={"AGENT_SERVICE_URL": f"ws://localhost:{stub.port}"}
            )

        run_file = _only_run_file(data_home)
        record = RunRecord.load(str(run_file.parent))

        assert record.validate() == []
        assert record.status == "aborted"
        assert record.get_final_validity() == "invalid"
        assert not record.is_valid()
        assert record.get_events("run_started")
        assert not record.get_events("run_ended")


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


def test_recorder_rejects_decreasing_event_timestamps():
    """A reordered event must invalidate the run before it is persisted."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        runs_dir = Path(temp_dir) / "ordering-runs"
        _run_godot(
            data_home,
            "--script",
            "res://tests/acceptance/recorder_ordering_harness.gd",
            extra_environment={"AGENT_WORLD_TEST_RUNS_DIR": str(runs_dir)},
            timeout=15,
        )

        record = RunRecord.load(str(runs_dir / "run_ordering_test"))
        assert record.validate() == []
        assert record.status == "aborted"
        assert record.get_final_validity() == "invalid"
        assert not record.is_valid()
        assert [event["id"] for event in record.events] == ["evt_started"]


def test_recorder_rejects_duplicate_event_ids():
    """A reused event id must invalidate the run before it is persisted."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        runs_dir = Path(temp_dir) / "duplicate-id-runs"
        _run_godot(
            data_home,
            "--script",
            "res://tests/acceptance/recorder_duplicate_id_harness.gd",
            extra_environment={"AGENT_WORLD_TEST_RUNS_DIR": str(runs_dir)},
            timeout=15,
        )

        record = RunRecord.load(str(runs_dir / "run_duplicate_id_test"))
        assert record.validate() == []
        assert record.status == "aborted"
        assert record.get_final_validity() == "invalid"
        assert not record.is_valid()
        assert [event["id"] for event in record.events] == ["evt_repeated"]


def test_recorder_enforces_stream_boundaries_before_appending():
    """Lifecycle rules must reject bad streams before they are persisted."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        runs_dir = Path(temp_dir) / "boundary-runs"
        _run_godot(
            data_home,
            "--script",
            "res://tests/acceptance/recorder_boundary_harness.gd",
            extra_environment={"AGENT_WORLD_TEST_RUNS_DIR": str(runs_dir)},
            timeout=15,
        )

        first = RunRecord.load(str(runs_dir / "run_boundary_first_test"))
        assert first.status == "aborted"
        assert first.get_final_validity() == "invalid"
        assert first.events == []

        duplicate_start = RunRecord.load(
            str(runs_dir / "run_boundary_duplicate_start_test")
        )
        assert duplicate_start.validate() == []
        assert duplicate_start.status == "aborted"
        assert duplicate_start.get_final_validity() == "invalid"
        assert [event["id"] for event in duplicate_start.events] == ["evt_started"]

        after_end = RunRecord.load(str(runs_dir / "run_boundary_after_end_test"))
        assert after_end.status == "aborted"
        assert after_end.get_final_validity() == "invalid"
        assert [event["event_type_id"] for event in after_end.events] == [
            "run_started",
            "run_ended",
        ]

        missing_end = RunRecord.load(
            str(runs_dir / "run_boundary_missing_end_event_test")
        )
        assert missing_end.status == "aborted"
        assert missing_end.get_final_validity() == "invalid"
        assert [event["event_type_id"] for event in missing_end.events] == [
            "run_started"
        ]


if __name__ == "__main__":
    test_room_persists_a_complete_run()
    test_run_without_agent_session_is_aborted()
    test_run_lost_after_handshake_is_aborted()
    test_recorder_failure_is_persisted_as_invalid_run()
    test_recorder_rejects_decreasing_event_timestamps()
    test_recorder_rejects_duplicate_event_ids()
    test_recorder_enforces_stream_boundaries_before_appending()
    print("All run recording acceptance tests passed!")
