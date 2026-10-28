extends Node
var passed: int = 0
var failed: int = 0
var received: int = 0
var snack_count: int = 0
var timeout_count: int = 0
var ticks: int = 1000
var test_dir: String

func check(value: bool, message: String) -> void:
 if value:
  passed += 1
  print("PASS ", message)
 else:
  failed += 1
  push_error("FAIL " + message)

func _ready() -> void:
 _run.call_deferred()

func _run() -> void:
 test_dir = "user://p0-tests-%d" % Time.get_ticks_usec()
 DirAccess.make_dir_recursive_absolute(test_dir)
 Config.load_config("res://data/default_config.json")
 check(EventBus.EVENTS.size() == 11, "all 11 event IDs")
 check(EventBus.register(EventBus.PET_CLICKED, _event), "event registration")
 EventBus.register(EventBus.PET_CLICKED, _event)
 EventBus.dispatch(EventBus.PET_CLICKED, {"value": 42})
 check(received == 1, "dispatch once, duplicate registration ignored")
 EventBus.unregister(EventBus.PET_CLICKED, _event)
 EventBus.dispatch(EventBus.PET_CLICKED, {"value": 42})
 check(received == 1, "unregister")
 check(not EventBus.dispatch(&"INVALID"), "unknown event rejected")
 var area = Rect2i(0, 0, 1920, 1040)
 check(WindowGeometry.bottom_right(Vector2i(360, 420), area) == Vector2i(1544, 604), "bottom-right respects usable work area and margin")
 check(WindowGeometry.clamp_to_area(Vector2i(5000, -200), Vector2i(360, 420), area) == Vector2i(1544, 16), "off-screen position repaired")
 check(WindowGeometry.bottom_right(Vector2i(360, 420), Rect2i(-1920, 0, 1920, 1040)) == Vector2i(-376, 604), "negative-origin monitor")
 var original = Config.data.duplicate(true)
 Config.data.window.position = [123, 456]
 Config.data.volume = 0.25
 check(Config.save_config(test_dir.path_join("config.json")) == OK, "config saved in user directory")
 Config.data.window.position = []
 Config.load_config(test_dir.path_join("config.json"))
 check(Config.data.window.position.size() == 2 and int(Config.data.window.position[0]) == 123 and int(Config.data.window.position[1]) == 456 and is_equal_approx(Config.data.volume, 0.25), "config restored")
 var bad = FileAccess.open(test_dir.path_join("bad.json"), FileAccess.WRITE)
 bad.store_string('{"window":{"position":["bad",9],"always_on_top":"bad"},"volume":9.0}')
 bad.close()
 Config.load_config(test_dir.path_join("bad.json"))
 check(Config.data.window.position.is_empty(), "invalid saved coordinates rejected")
 check(Config.data.window.always_on_top == true and Config.data.volume == 1.0, "type validation and volume bounds")
 bad = FileAccess.open(test_dir.path_join("bad.json"), FileAccess.WRITE)
 bad.store_string('{invalid')
 bad.close()
 Config.load_config(test_dir.path_join("bad.json"))
 check(Config.data.character.name == "Niangao", "corrupt JSON falls back to defaults")
 Config.data = original
 var cat = preload("res://scenes/character.tscn").instantiate()
 add_child(cat)
 var animation: PetAnimationController = cat.controller
 check(animation.ACTIONS.size() == 6, "six action IDs")
 check(animation.is_action_available("idle"), "placeholder idle available")
 check(animation.get_current_action() == "idle", "idle started")
 check(animation.play("idle"), "play interface")
 check(animation.transition_to("idle"), "transition interface")
 for id in ["name_response", "head_pet", "play_bow", "wand_chase", "box_rest", "unknown"]:
  check(not animation.play(id) and animation.get_current_action() == "idle", "missing action safely rejected: " + id)
 animation.mapping["idle"]["animation"] = "missing_resource"
 check(not animation.is_action_available("idle"), "missing mapped resource guarded")
 animation.stop()
 check(animation.get_current_action().is_empty(), "stop interface")
 check(not cat.replace_with_glb(null), "null replacement rejected")
 var model_scene = PackedScene.new()
 var replacement_root = Node3D.new()
 model_scene.pack(replacement_root)
 replacement_root.free()
 check(cat.replace_with_glb(model_scene), "Node3D replacement accepted")
 check(not cat.visual.visible and not animation.is_action_available("idle"), "replacement hides placeholder and requires explicit animation mapping")
 var image = Image.create(100, 100, false, Image.FORMAT_RGBA8)
 image.fill(Color.TRANSPARENT)
 image.fill_rect(Rect2i(20, 20, 60, 60), Color.WHITE)
 image.fill_rect(Rect2i(60, 20, 20, 40), Color.TRANSPARENT)
 var polygons = AlphaHitRegion.polygons_from_image(image)
 check(polygons.size() == 1, "connected alpha contour")
 check(Geometry2D.is_point_in_polygon(Vector2(30, 30), polygons[0]), "opaque point inside input region")
 check(not Geometry2D.is_point_in_polygon(Vector2(70, 30), polygons[0]), "concave transparent cutout excluded (not bounding rectangle)")
 check(not Geometry2D.is_point_in_polygon(Vector2(5, 5), polygons[0]), "transparent corner excluded")
 var home = HomeSceneController.new()
 home.now = func(): return ticks
 add_child(home)
 EventBus.register(EventBus.SNACK_REQUEST_STARTED, _snack)
 EventBus.register(EventBus.SNACK_REQUEST_TIMEOUT, _timeout)
 EventBus.dispatch(EventBus.OWNER_RETURN_HOME)
 check(snack_count == 0, "entry ID mandatory")
 EventBus.dispatch(EventBus.OWNER_RETURN_HOME, {"entry_id": "a"})
 check(snack_count == 1 and home.state == "snack_wait_DEBUG", "one request on valid entry")
 EventBus.dispatch(EventBus.OWNER_RETURN_HOME, {"entry_id": "a"})
 EventBus.dispatch(EventBus.OWNER_RETURN_HOME, {"entry_id": "b"})
 check(snack_count == 1, "duplicate and concurrent entry do not reopen request")
 ticks = 60999
 home.poll_timeout()
 check(timeout_count == 0, "not expired before 60 actual seconds")
 ticks = 61000
 home.poll_timeout()
 check(timeout_count == 1 and home.state == "autonomous", "60s monotonic timeout without frame accumulation")
 home.poll_timeout()
 EventBus.dispatch(EventBus.OWNER_RETURN_HOME, {"entry_id": "a"})
 check(timeout_count == 1 and snack_count == 1, "expired entry cannot request twice")
 EventBus.dispatch(EventBus.OWNER_RETURN_HOME, {"entry_id": "b"})
 EventBus.dispatch(EventBus.SNACK_GIVEN, {"entry_id": "wrong"})
 check(home.active_entry == "b", "wrong entry feed ignored")
 EventBus.dispatch(EventBus.SNACK_GIVEN, {"entry_id": "b"})
 check(home.state == "autonomous" and home.active_entry.is_empty(), "feeding returns to autonomy")
 EventBus.dispatch(EventBus.OWNER_RETURN_HOME, {"entry_id": "c"})
 ticks += 60001
 EventBus.dispatch(EventBus.SNACK_GIVEN, {"entry_id": "c"})
 check(timeout_count == 2, "late feed respects elapsed-time deadline")
 home.free()
 cat.free()
 for path in [test_dir.path_join("config.json"), test_dir.path_join("bad.json")]:
  DirAccess.remove_absolute(path)
 DirAccess.remove_absolute(test_dir)
 print("TEST_RESULT passed=%d failed=%d" % [passed, failed])
 get_tree().quit(0 if failed == 0 else 1)

func _event(payload: Dictionary) -> void:
 if payload.get("value") == 42:
  received += 1
func _snack(_payload: Dictionary) -> void:
 snack_count += 1
func _timeout(_payload: Dictionary) -> void:
 timeout_count += 1
