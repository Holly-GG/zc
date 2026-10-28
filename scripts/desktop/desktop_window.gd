class_name DesktopWindowController
extends Node
var window: Window
var dragging: bool = false
var drag_offset: Vector2i
var drag_start: Vector2i
var pressed: bool = false
var passthrough_enabled: bool = true
var window_mode: String = "initializing"
var _check_elapsed: float = 0.0
var _last_size: Vector2i

func _ready() -> void:
 window = get_window()
 window.transparent = true
 window.transparent_bg = true
 window.borderless = true
 window.always_on_top = Config.data.window.always_on_top
 window.unresizable = true
 window.min_size = Vector2i(1, 1)
 passthrough_enabled = Config.data.window.mouse_passthrough
 if DisplayServer.get_name() == "headless":
  window_mode = "headless (NO native desktop validation)"
  return
 window.size = Vector2i(360, 420)
 restore_position()
 window.close_requested.connect(quit_app)
 window_mode = "alpha silhouette / pending first frame"

func screen_area(screen: int) -> Rect2i:
 return DisplayServer.screen_get_usable_rect(screen)

func restore_position() -> void:
 var primary = DisplayServer.get_primary_screen()
 var area = screen_area(primary)
 var saved: Array = Config.data.window.position
 if saved.size() == 2:
  var position = Vector2i(int(saved[0]), int(saved[1]))
  var best = _nearest_screen(position)
  _fit(best)
  window.position = WindowGeometry.clamp_to_area(position, window.size, screen_area(best))
 else:
  _fit(primary)
  window.position = WindowGeometry.bottom_right(window.size, area)
 _last_size = window.size

func _fit(screen: int) -> void:
 var available = screen_area(screen).size - Vector2i(32, 32)
 var ratio = minf(1.0, minf(float(available.x) / 360.0, float(available.y) / 420.0))
 window.size = Vector2i(maxi(1, int(360 * ratio)), maxi(1, int(420 * ratio)))

func _nearest_screen(position: Vector2i) -> int:
 var best = DisplayServer.get_primary_screen()
 var distance = INF
 for screen in DisplayServer.get_screen_count():
  var area = screen_area(screen)
  var point = Vector2(clampi(position.x, area.position.x, area.end.x), clampi(position.y, area.position.y, area.end.y))
  var value = Vector2(position).distance_squared_to(point)
  if value < distance:
   distance = value
   best = screen
 return best

func _process(delta: float) -> void:
 if DisplayServer.get_name() == "headless":
  return
 if dragging:
  window.position = DisplayServer.mouse_get_position() - drag_offset
 _check_elapsed += delta
 if _check_elapsed >= 1.0 and not pressed:
  _check_elapsed = 0.0
  var screen = _nearest_screen(window.position)
  _fit(screen)
  window.position = WindowGeometry.clamp_to_area(window.position, window.size, screen_area(screen))

func _input(event: InputEvent) -> void:
 if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
  if event.pressed:
   pressed = true
   dragging = true
   drag_start = DisplayServer.mouse_get_position()
   drag_offset = drag_start - window.position
  else:
   var moved = DisplayServer.mouse_get_position().distance_to(drag_start)
   pressed = false
   dragging = false
   clamp_and_save()
   if moved < 6:
    EventBus.dispatch(EventBus.PET_CLICKED)
    if event.position.y / float(window.size.y) < 0.45:
     EventBus.dispatch(EventBus.PET_HEAD_TOUCHED)
 if event is InputEventKey and event.pressed and not event.echo:
  match event.keycode:
   KEY_ESCAPE: quit_app()
   KEY_H: hide_pet()
   KEY_T:
    window.always_on_top = not window.always_on_top
    Config.data.window.always_on_top = window.always_on_top
    save()

func clamp_and_save() -> void:
 if DisplayServer.get_name() != "headless":
  var screen = _nearest_screen(window.position)
  window.position = WindowGeometry.clamp_to_area(window.position, window.size, screen_area(screen))
  Config.data.window.position = [window.position.x, window.position.y]
 save()

func save() -> void:
 if Config.save_config() != OK:
  Log.error("Cannot save user configuration")

func hide_pet() -> void:
 clamp_and_save()
 window.hide()

func show_pet() -> void:
 window.show()
 restore_position()

func quit_app() -> void:
 clamp_and_save()
 EventBus.dispatch(EventBus.APP_EXITING)
 get_tree().quit()
