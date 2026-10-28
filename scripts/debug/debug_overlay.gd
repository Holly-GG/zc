class_name DebugOverlay
extends Window
var status: Label
var errors: TextEdit
var desktop: DesktopWindowController
var home: HomeSceneController
var animation: PetAnimationController
var entry_counter: int = 0

func _ready() -> void:
 title = "Niangao P0 • DEBUG • PLACEHOLDER"
 size = Vector2i(510, 570)
 unresizable = false
 always_on_top = true
 close_requested.connect(func():
  if desktop != null and not desktop.window.visible:
   desktop.show_pet()
  hide())
 var panel = VBoxContainer.new()
 panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 panel.offset_left = 16
 panel.offset_top = 12
 panel.offset_right = -16
 panel.offset_bottom = -12
 add_child(panel)
 var title_label = Label.new()
 title_label.text = "NIANGAO / P0 / PLACEHOLDER
F3: toggle debug • drag cat • right-click: debug
H: hide • T: topmost • Esc: save & quit"
 panel.add_child(title_label)
 status = Label.new()
 panel.add_child(status)
 _button(panel, "Simulate OWNER_RETURN_HOME (no 3D home)", func():
  entry_counter += 1
  EventBus.dispatch(EventBus.OWNER_RETURN_HOME, {"entry_id": "debug-%d-%d" % [Time.get_ticks_usec(), entry_counter]}))
 _button(panel, "Give snack", func(): EventBus.dispatch(EventBus.SNACK_GIVEN, {"entry_id": home.active_entry}))
 _button(panel, "Call name (animation UNIMPLEMENTED)", func():
  EventBus.dispatch(EventBus.PET_NAME_CALLED)
  animation.transition_to("name_response"))
 _button(panel, "Toggle work mode", func():
  Config.data.work_mode = not Config.data.work_mode
  desktop.save()
  EventBus.dispatch(EventBus.WORK_MODE_ENABLED, {"enabled": Config.data.work_mode}))
 _button(panel, "Toggle sleep mode", func():
  Config.data.sleep_mode = not Config.data.sleep_mode
  desktop.save()
  EventBus.dispatch(EventBus.SLEEP_MODE_ENABLED, {"enabled": Config.data.sleep_mode}))
 _button(panel, "Toggle always on top", func():
  desktop.window.always_on_top = not desktop.window.always_on_top
  Config.data.window.always_on_top = desktop.window.always_on_top
  desktop.save())
 _button(panel, "Toggle alpha pass-through (manual fallback)", func():
  desktop.passthrough_enabled = not desktop.passthrough_enabled
  Config.data.window.mouse_passthrough = desktop.passthrough_enabled
  desktop.save())
 _button(panel, "Hide / Show pet (this debug window remains)", func():
  if desktop.window.visible: desktop.hide_pet()
  else: desktop.show_pet())
 _button(panel, "Save & Exit", desktop.quit_app)
 errors = TextEdit.new()
 errors.editable = false
 errors.custom_minimum_size.y = 100
 errors.size_flags_vertical = Control.SIZE_EXPAND_FILL
 panel.add_child(errors)

func _button(parent: Node, caption: String, callback: Callable) -> void:
 var button = Button.new()
 button.text = caption
 button.pressed.connect(callback)
 parent.add_child(button)

func _process(_delta: float) -> void:
 if status == null or desktop == null:
  return
 status.text = "State: %s
Animation: %s | FPS: %d
Window: %s
Last event: %s
User config: %s" % [home.state, animation.get_current_action(), Engine.get_frames_per_second(), desktop.window_mode, EventBus.last_event, Config.USER_PATH]
 errors.text = "Error / unavailable log:
" + "
".join(Log.errors)

func _input(event: InputEvent) -> void:
 if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F3:
  if not desktop.window.visible:
   desktop.show_pet()
  hide()
