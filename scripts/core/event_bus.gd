extends Node
signal dispatched(event_id: StringName, payload: Dictionary)
const APP_STARTED = &"APP_STARTED"
const APP_EXITING = &"APP_EXITING"
const OWNER_RETURN_HOME = &"OWNER_RETURN_HOME"
const WORK_MODE_ENABLED = &"WORK_MODE_ENABLED"
const SLEEP_MODE_ENABLED = &"SLEEP_MODE_ENABLED"
const PET_CLICKED = &"PET_CLICKED"
const PET_HEAD_TOUCHED = &"PET_HEAD_TOUCHED"
const PET_NAME_CALLED = &"PET_NAME_CALLED"
const SNACK_REQUEST_STARTED = &"SNACK_REQUEST_STARTED"
const SNACK_GIVEN = &"SNACK_GIVEN"
const SNACK_REQUEST_TIMEOUT = &"SNACK_REQUEST_TIMEOUT"
const EVENTS = [APP_STARTED, APP_EXITING, OWNER_RETURN_HOME, WORK_MODE_ENABLED,
 SLEEP_MODE_ENABLED, PET_CLICKED, PET_HEAD_TOUCHED, PET_NAME_CALLED,
 SNACK_REQUEST_STARTED, SNACK_GIVEN, SNACK_REQUEST_TIMEOUT]
var last_event: String = "—"
var _listeners: Dictionary = {}

func register(event_id: StringName, callback: Callable) -> bool:
 if event_id not in EVENTS or not callback.is_valid():
  return false
 if not _listeners.has(event_id):
  _listeners[event_id] = []
 if callback not in _listeners[event_id]:
  _listeners[event_id].append(callback)
 return true

func unregister(event_id: StringName, callback: Callable) -> void:
 if _listeners.has(event_id):
  _listeners[event_id].erase(callback)

func dispatch(event_id: StringName, payload: Dictionary = {}) -> bool:
 if event_id not in EVENTS:
  push_warning("Unknown event: " + str(event_id))
  return false
 last_event = str(event_id)
 dispatched.emit(event_id, payload.duplicate(true))
 for callback in _listeners.get(event_id, []).duplicate():
  if callback.is_valid():
   callback.call(payload.duplicate(true))
 return true
