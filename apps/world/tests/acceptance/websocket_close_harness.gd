extends SceneTree

const WebSocketClientScript = preload("res://src/websocket_client.gd")


class ProbeClient extends "res://src/websocket_client.gd":
	var reconnect_attempts: int = 0

	func connect_to_server() -> void:
		reconnect_attempts += 1
		super.connect_to_server()


func _initialize() -> void:
	call_deferred("_run_close_during_backoff")


func _run_close_during_backoff() -> void:
	var client = ProbeClient.new()
	root.add_child(client)
	# Schedule an exponential-backoff attempt, then shut the client down before
	# the timer fires. The attempt must not run against the released peer.
	client._schedule_reconnect()
	client.close()
	await create_timer(1.5).timeout
	if client.reconnect_attempts != 0:
		quit(1)
		return
	if client._peer != null:
		quit(1)
		return
	quit(0)
