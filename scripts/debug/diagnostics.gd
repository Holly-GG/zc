extends Node
## Opt-in: -- --diagnostics. Contains app state only, never environment data.
var desktop: DesktopWindowController
var home: HomeSceneController
var region: AlphaHitRegion
var file: FileAccess
var elapsed: float = 0.0
var counts: Dictionary = {}
func _ready() -> void:
 file = FileAccess.open("user://diagnostics.jsonl", FileAccess.WRITE)
 EventBus.dispatched.connect(_event)
func _event(id: StringName, _payload: Dictionary) -> void:
 counts[str(id)] = int(counts.get(str(id), 0)) + 1
 _record()
func _process(delta: float) -> void:
 elapsed += delta
 if elapsed >= 0.25:
  elapsed = 0
  _record()
func _record() -> void:
 if file == null or desktop == null:
  return
 var position = desktop.window.position
 var size = desktop.window.size
 file.store_line(JSON.stringify({"ticks_ms": Time.get_ticks_msec(), "position": [position.x, position.y], "size": [size.x, size.y], "window_mode": desktop.window_mode, "polygon_points": region.last_polygon.size(), "state": home.state, "events": counts}))
 file.flush()
