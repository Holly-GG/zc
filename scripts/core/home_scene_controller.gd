class_name HomeSceneController
extends Node
## Debug flow only: no implemented 3D home, greeting or following animations.
signal state_changed(state: String)
const TIMEOUT_MS = 60000
var state: String = "autonomous"
var active_entry: String = ""
var seen_entries: Dictionary = {}
var deadline_ms: int = 0
var now: Callable = func(): return Time.get_ticks_msec()

func _ready() -> void:
 EventBus.register(EventBus.OWNER_RETURN_HOME, _on_home)
 EventBus.register(EventBus.SNACK_GIVEN, _on_snack)

func _exit_tree() -> void:
 EventBus.unregister(EventBus.OWNER_RETURN_HOME, _on_home)
 EventBus.unregister(EventBus.SNACK_GIVEN, _on_snack)

func _on_home(payload: Dictionary) -> void:
 var entry_id = str(payload.get("entry_id", ""))
 if entry_id.is_empty() or seen_entries.has(entry_id) or not active_entry.is_empty():
  return
 seen_entries[entry_id] = true
 active_entry = entry_id
 _set_state("greeting_INTERFACE_ONLY")
 _set_state("following_INTERFACE_ONLY")
 deadline_ms = int(now.call()) + TIMEOUT_MS
 _set_state("snack_wait_DEBUG")
 EventBus.dispatch(EventBus.SNACK_REQUEST_STARTED, {"entry_id": entry_id, "timeout_seconds": 60})

func _on_snack(payload: Dictionary) -> void:
 if not active_entry.is_empty() and str(payload.get("entry_id", "")) == active_entry:
  # A late feed cannot beat the real elapsed-time deadline.
  if int(now.call()) >= deadline_ms:
   _timeout()
  else:
   _finish()

func _process(_delta: float) -> void:
 poll_timeout()

func poll_timeout() -> void:
 if not active_entry.is_empty() and int(now.call()) >= deadline_ms:
  _timeout()

func _timeout() -> void:
 var entry_id = active_entry
 _finish()
 EventBus.dispatch(EventBus.SNACK_REQUEST_TIMEOUT, {"entry_id": entry_id})

func _finish() -> void:
 active_entry = ""
 deadline_ms = 0
 _set_state("autonomous")

func _set_state(value: String) -> void:
 state = value
 state_changed.emit(state)
