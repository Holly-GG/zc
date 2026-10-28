extends Node
const DEFAULT_PATH = "res://data/default_config.json"
const USER_PATH = "user://config.json"
var data: Dictionary = {}

func _ready() -> void:
 load_config()

func load_config(path: String = USER_PATH) -> void:
 var defaults = JSON.parse_string(FileAccess.get_file_as_string(DEFAULT_PATH))
 data = defaults.duplicate(true)
 if FileAccess.file_exists(path):
  var parser = JSON.new()
  var parse_error = parser.parse(FileAccess.get_file_as_string(path))
  var parsed = parser.data if parse_error == OK else null
  if parsed is Dictionary:
   _merge(data, parsed)
  else:
   push_warning("Invalid user config; using defaults")
 _validate()

func _merge(target: Dictionary, source: Dictionary) -> void:
 for key in source:
  if target.has(key) and target[key] is Dictionary and source[key] is Dictionary:
   _merge(target[key], source[key])
  elif target.has(key):
   target[key] = source[key]

func _validate() -> void:
 var defaults: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DEFAULT_PATH))
 for key in defaults:
  if typeof(data.get(key)) != typeof(defaults[key]):
   data[key] = defaults[key]
 var w: Dictionary = data.window
 for key in defaults.window:
  if typeof(w.get(key)) != typeof(defaults.window[key]):
   w[key] = defaults.window[key]
 if w.position is Array and (w.position.size() != 2 or not _numbers(w.position)):
  w.position = []
 data.volume = clampf(float(data.volume), 0.0, 1.0)

func _numbers(values: Array) -> bool:
 for value in values:
  if not (value is float or value is int):
   return false
 return true

func save_config(path: String = USER_PATH) -> Error:
 var file = FileAccess.open(path + ".tmp", FileAccess.WRITE)
 if file == null:
  return FileAccess.get_open_error()
 file.store_string(JSON.stringify(data, "  "))
 file.close()
 var error = DirAccess.rename_absolute(path + ".tmp", path)
 if error != OK:
  push_warning("Config save failed: " + error_string(error))
 return error
