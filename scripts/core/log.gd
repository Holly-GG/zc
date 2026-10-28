extends Node
signal changed
var errors: Array[String] = []
func error(message: String) -> void:
 errors.append(Time.get_datetime_string_from_system() + " " + message)
 if errors.size() > 30:
  errors.pop_front()
 push_warning(message)
 changed.emit()
