class_name PetAnimationController
extends Node
signal action_changed(action_id: String)
signal action_unavailable(action_id: String, reason: String)
const ACTIONS = ["idle", "name_response", "head_pet", "play_bow", "wand_chase", "box_rest"]
var player: AnimationPlayer
var mapping: Dictionary = {}
var _current: String = ""

func configure(animation_player: AnimationPlayer, resource_mapping: Dictionary) -> void:
 player = animation_player
 mapping = resource_mapping.duplicate(true)

func is_action_available(action_id: String) -> bool:
 if action_id not in ACTIONS or player == null:
  return false
 var entry = mapping.get(action_id, {})
 return entry is Dictionary and entry.get("implemented", false) == true and player.has_animation(str(entry.get("animation", "")))

func play(action_id: String) -> bool:
 return _play(action_id, 0.0)

func transition_to(action_id: String) -> bool:
 return _play(action_id, 0.2)

func _play(action_id: String, blend: float) -> bool:
 if not is_action_available(action_id):
  action_unavailable.emit(action_id, "UNIMPLEMENTED or missing animation resource")
  return false
 player.play(str(mapping[action_id].animation), blend)
 _current = action_id
 action_changed.emit(action_id)
 return true

func stop() -> void:
 if player != null:
  player.stop()
 _current = ""
 action_changed.emit("")

func get_current_action() -> String:
 return _current
