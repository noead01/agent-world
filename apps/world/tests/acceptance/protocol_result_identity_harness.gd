extends SceneTree

const ProtocolHandlerScript = preload("res://src/protocol_handler.gd")

class FakeClient:
	func send_message(_message: Dictionary) -> void:
		pass

var _results: Array = []

func _initialize() -> void:
	call_deferred("_run_result_identity_cases")

func _run_result_identity_cases() -> void:
	var handler = ProtocolHandlerScript.new()
	handler.run_id = "run_test"
	handler.agent_id = "agent_test"
	handler.experiment_id = "exp_test"
	handler.scenario_id = "scenario_test"
	handler.scenario_version = "1.0.0"
	handler._websocket_client = FakeClient.new()
	handler.action_result_received.connect(func(result): _results.append(result))
	handler._pending_requests["act_test"] = {"type": "action"}

	# A foreign run_id with an otherwise matching correlation must not clear the
	# pending request or surface a successful result to the session.
	handler._on_message_received(_result("act_test", "run_foreign"))
	if not handler._pending_requests.has("act_test"):
		quit(1)
		return
	if not _results.is_empty():
		quit(1)
		return

	# A matching top-level identity with a foreign correlation is also foreign.
	handler._on_message_received(
		_result("act_test", "run_test", "run_foreign")
	)
	if not handler._pending_requests.has("act_test"):
		quit(1)
		return
	if not _results.is_empty():
		quit(1)
		return

	# The registered session's own result still completes the request.
	handler._on_message_received(_result("act_test"))
	if handler._pending_requests.has("act_test"):
		quit(1)
		return
	if _results.size() != 1:
		quit(1)
		return
	quit(0)

func _result(
	request_id: String,
	run_id: String = "run_test",
	correlation_run_id: String = "run_test"
) -> Dictionary:
	return {
		"type": "Action",
		"id": request_id,
		"run_id": run_id,
		"agent_id": "agent_test",
		"timestamp_s": 1.0,
		"version": "1.0.0",
		"action_type_id": "touch",
		"result": "success",
		"correlation": {
			"experiment_id": "exp_test",
			"scenario_id": "scenario_test",
			"scenario_version": "1.0.0",
			"run_id": correlation_run_id,
			"agent_id": "agent_test",
			"world_revision": 1,
			"simulation_tick": 1,
			"simulation_time": 1.0,
			"component": "world",
		},
	}
