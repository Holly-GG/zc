extends Node3D
## PLACEHOLDER: simple geometry, NOT a final reconstruction of Niangao.
var animation_player: AnimationPlayer
var controller: PetAnimationController
var visual: Node3D
var replacement: Node3D

func _ready() -> void:
 visual = Node3D.new()
 visual.name = "Visual"
 add_child(visual)
 var cream = Color("eee7df")
 var brown = Color("49372f")
 var white = Color("fff7ef")
 _ellipsoid("Body", Vector3(0, 0.95, 0), Vector3(0.66, 0.83, 0.48), cream)
 for x in [-0.40, 0.40]:
  _ellipsoid("HindLeg", Vector3(x, 0.34, 0.03), Vector3(0.27, 0.34, 0.30), cream)
  _ellipsoid("HindPaw", Vector3(x, 0.13, 0.23), Vector3(0.25, 0.14, 0.30), white)
 for x in [-0.22, 0.22]:
  _ellipsoid("FrontLeg", Vector3(x, 0.53, 0.35), Vector3(0.16, 0.45, 0.18), cream)
  _ellipsoid("FrontPaw", Vector3(x, 0.12, 0.48), Vector3(0.18, 0.13, 0.25), white)
 _ellipsoid("Neck", Vector3(0, 1.59, 0.0), Vector3(0.39, 0.32, 0.35), white)
 _ellipsoid("Head", Vector3(0, 1.98, 0.05), Vector3(0.62, 0.52, 0.45), brown)
 for x in [-0.39, 0.39]:
  var ear = MeshInstance3D.new()
  var cone = CylinderMesh.new()
  cone.top_radius = 0.0
  cone.bottom_radius = 0.24
  cone.height = 0.54
  cone.radial_segments = 3
  ear.mesh = cone
  ear.position = Vector3(x, 2.44, 0.02)
  ear.rotation.z = -sign(x) * 0.23
  ear.material_override = _material(brown)
  visual.add_child(ear)
 _ellipsoid("Muzzle", Vector3(0, 1.84, 0.43), Vector3(0.33, 0.23, 0.12), white)
 _ellipsoid("WhiteBlaze_PLACEHOLDER", Vector3(-0.035, 2.08, 0.46), Vector3(0.105, 0.27, 0.045), white)
 for x in [-0.25, 0.25]:
  _ellipsoid("BlueEye", Vector3(x, 2.08, 0.455), Vector3(0.115, 0.10, 0.045), Color("4eafff"))
  _ellipsoid("Pupil", Vector3(x, 2.08, 0.496), Vector3(0.045, 0.07, 0.015), Color("142333"))
 _ellipsoid("PinkNose", Vector3(0, 1.94, 0.56), Vector3(0.075, 0.05, 0.035), Color("e49baf"))
 _ellipsoid("NoseSpot_PLACEHOLDER", Vector3(0.09, 1.91, 0.54), Vector3(0.04, 0.045, 0.025), brown)
 var tail = _ellipsoid("Tail", Vector3(0.72, 0.48, -0.13), Vector3(0.25, 0.64, 0.24), brown)
 tail.rotation.z = -0.7
 animation_player = AnimationPlayer.new()
 animation_player.name = "AnimationPlayer"
 add_child(animation_player)
 var animation = Animation.new()
 animation.length = 3.0
 animation.loop_mode = Animation.LOOP_LINEAR
 var track = animation.add_track(Animation.TYPE_VALUE)
 animation.track_set_path(track, NodePath("Visual:position:y"))
 animation.track_insert_key(track, 0.0, 0.0)
 animation.track_insert_key(track, 1.5, 0.035)
 animation.track_insert_key(track, 3.0, 0.0)
 var library = AnimationLibrary.new()
 library.add_animation("idle", animation)
 animation_player.add_animation_library("", library)
 controller = PetAnimationController.new()
 add_child(controller)
 controller.configure(animation_player, Config.data.actions)
 controller.action_unavailable.connect(func(id, reason): Log.error(id + ": " + reason))
 controller.play("idle")

func _material(color: Color) -> StandardMaterial3D:
 var material = StandardMaterial3D.new()
 material.albedo_color = color
 material.roughness = 0.85
 return material

func _ellipsoid(label: String, pos: Vector3, size: Vector3, color: Color) -> MeshInstance3D:
 var mesh = MeshInstance3D.new()
 mesh.name = label
 var sphere = SphereMesh.new()
 sphere.height = 2.0
 sphere.radius = 1.0
 sphere.radial_segments = 16
 sphere.rings = 8
 mesh.mesh = sphere
 mesh.position = pos
 mesh.scale = size
 mesh.material_override = _material(color)
 visual.add_child(mesh)
 return mesh

func replace_with_glb(scene: PackedScene, action_mapping: Dictionary = {}) -> bool:
 if scene == null:
  return false
 var instance = scene.instantiate()
 if not instance is Node3D:
  instance.free()
  return false
 if replacement != null:
  replacement.queue_free()
 replacement = instance
 add_child(replacement)
 visual.hide()
 controller.stop()
 var imported_player: AnimationPlayer
 var players = replacement.find_children("*", "AnimationPlayer", true, false)
 if not players.is_empty():
  imported_player = players[0] as AnimationPlayer
 else:
  imported_player = null
 controller.configure(imported_player as AnimationPlayer, action_mapping)
 return true
