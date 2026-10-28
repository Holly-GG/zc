extends Node
var desktop: DesktopWindowController
var home: HomeSceneController
var debug: DebugOverlay
var viewport: SubViewport
var character: Node3D
var region: AlphaHitRegion
var tray: int = -1
var menu: RID

func _ready() -> void:
 get_tree().auto_accept_quit = false
 get_window().title = "Niangao P0 PLACEHOLDER"
 get_window().transparent_bg = true
 viewport = SubViewport.new()
 viewport.name = "PetRender"
 viewport.size = Vector2i(360, 420)
 viewport.transparent_bg = true
 viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
 viewport.own_world_3d = true
 add_child(viewport)
 var camera = Camera3D.new()
 camera.projection = Camera3D.PROJECTION_ORTHOGONAL
 camera.size = 3.55
 camera.position = Vector3(0, 1.38, 6)
 viewport.add_child(camera)
 camera.current = true
 var light = DirectionalLight3D.new()
 light.rotation_degrees = Vector3(-25, -25, 0)
 light.light_energy = 1.15
 viewport.add_child(light)
 var environment = WorldEnvironment.new()
 var env = Environment.new()
 env.background_mode = Environment.BG_CLEAR_COLOR
 env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 env.ambient_light_color = Color.WHITE
 env.ambient_light_energy = 0.65
 environment.environment = env
 viewport.add_child(environment)
 character = preload("res://scenes/character.tscn").instantiate()
 viewport.add_child(character)
 var display = TextureRect.new()
 display.texture = viewport.get_texture()
 display.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 display.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
 display.mouse_filter = Control.MOUSE_FILTER_IGNORE
 add_child(display)
 home = HomeSceneController.new()
 add_child(home)
 desktop = DesktopWindowController.new()
 add_child(desktop)
 region = AlphaHitRegion.new()
 region.source = viewport
 region.desktop = desktop
 add_child(region)
 debug = DebugOverlay.new()
 debug.desktop = desktop
 debug.home = home
 debug.animation = character.controller
 add_child(debug)
 debug.hide()
 _setup_tray()
 desktop.window.visibility_changed.connect(func():
  if not desktop.window.visible and tray < 0:
   debug.show())
 if tray < 0 and DisplayServer.get_name() != "headless":
  debug.show()
  Log.error("System tray unavailable: keep debug window for restore/exit")
 if "--diagnostics" in OS.get_cmdline_user_args():
  var diagnostics = preload("res://scripts/debug/diagnostics.gd").new()
  diagnostics.desktop = desktop
  diagnostics.home = home
  diagnostics.region = region
  add_child(diagnostics)
 EventBus.dispatch(EventBus.APP_STARTED)
 if "--render-smoke" in OS.get_cmdline_user_args():
  _render_smoke.call_deferred()

func _input(event: InputEvent) -> void:
 if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F3:
  debug.visible = not debug.visible
 if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT:
  debug.show()
  debug.grab_focus()

func _setup_tray() -> void:
 if not DisplayServer.has_feature(DisplayServer.FEATURE_STATUS_INDICATOR):
  return
 var image = Image.create(32, 32, false, Image.FORMAT_RGBA8)
 image.fill(Color("49372f"))
 var icon = ImageTexture.create_from_image(image)
 tray = DisplayServer.create_status_indicator(icon, "Niangao P0 PLACEHOLDER", _tray_pressed)
 if tray >= 0 and NativeMenu.has_feature(NativeMenu.FEATURE_GLOBAL_MENU):
  menu = NativeMenu.create_menu()
  NativeMenu.add_item(menu, "Show pet", func(_tag): desktop.show_pet())
  NativeMenu.add_item(menu, "Hide pet", func(_tag): desktop.hide_pet())
  NativeMenu.add_item(menu, "Debug / settings", func(_tag): debug.show())
  NativeMenu.add_item(menu, "Exit", func(_tag): desktop.quit_app())
  DisplayServer.status_indicator_set_menu(tray, menu)

func _tray_pressed(_button: int, _position: Vector2i) -> void:
 desktop.show_pet()
 debug.show()

func _exit_tree() -> void:
 if tray >= 0:
  DisplayServer.delete_status_indicator(tray)
 if menu.is_valid():
  NativeMenu.free_menu(menu)

func _render_smoke() -> void:
 for frame in 10:
  await RenderingServer.frame_post_draw
 var image = viewport.get_texture().get_image()
 var polygons = AlphaHitRegion.polygons_from_image(image)
 var opaque = 0
 var transparent = 0
 for y in image.get_height():
  for x in image.get_width():
   if image.get_pixel(x, y).a > 0.02: opaque += 1
   else: transparent += 1
 image.save_png("user://render-smoke.png")
 print("RENDER_SMOKE opaque=%d transparent=%d polygons=%d" % [opaque, transparent, polygons.size()])
 get_tree().quit(0 if opaque > 1000 and transparent > 1000 and polygons.size() == 1 else 1)
