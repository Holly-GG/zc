extends Control
var clicks: int = 0
func _ready() -> void:
 get_window().title = "Niangao Underlay Probe"
 get_window().transparent = false
 get_window().transparent_bg = false
 get_window().borderless = false
 get_window().always_on_top = false
 get_window().size = Vector2i(1100, 700)
 get_window().position = Vector2i(10, 30)
 var color = ColorRect.new()
 color.color = Color("274b68")
 color.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 color.mouse_filter = Control.MOUSE_FILTER_IGNORE
 add_child(color)
 var label = Label.new()
 label.text = "UNDERLAY INPUT PROBE - clicks must reach this window only outside the cat"
 label.position = Vector2(20, 20)
 add_child(label)
 _save()
func _input(event: InputEvent) -> void:
 if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
  clicks += 1
  _save()
func _save() -> void:
 var file = FileAccess.open("user://underlay-count.txt", FileAccess.WRITE)
 file.store_string(str(clicks))
