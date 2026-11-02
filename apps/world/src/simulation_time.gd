extends Node

class_name SimulationTime

signal simulation_ticked(tick: int, time: float)
signal simulation_paused()
signal simulation_resumed()
signal simulation_reset()
signal time_of_day_changed(hour: float)

@export_group("Simulation Time")
var simulation_time: float = 0.0
var simulation_tick: int = 0
var time_scale: float = 1.0
var is_paused: bool = false
var time_of_day_start_hour: float = 6.0
var day_cycle_duration_s: float = 300.0

var _last_reported_hour: float = -1.0

func tick(delta: float) -> void:
	if is_paused:
		return
	var scaled_delta: float = delta * time_scale
	simulation_time += scaled_delta
	simulation_tick += 1
	simulation_ticked.emit(simulation_tick, simulation_time)
	var hour: float = get_time_of_day()
	if abs(hour - _last_reported_hour) >= 0.5:
		_last_reported_hour = hour
		time_of_day_changed.emit(hour)

func get_time_of_day() -> float:
	if day_cycle_duration_s <= 0:
		return time_of_day_start_hour
	var cycle_position: float = fposmod(simulation_time / day_cycle_duration_s, 1.0)
	var hour: float = fposmod(time_of_day_start_hour + cycle_position * 24.0, 24.0)
	return hour

func pause() -> void:
	is_paused = true
	simulation_paused.emit()

func resume() -> void:
	is_paused = false
	simulation_resumed.emit()

func reset() -> void:
	simulation_time = 0.0
	simulation_tick = 0
	_last_reported_hour = -1.0
	simulation_reset.emit()

func get_simulation_time() -> float:
	return simulation_time

func set_time_scale(scale: float) -> void:
	time_scale = max(scale, 0.001)
