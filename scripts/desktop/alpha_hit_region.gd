class_name AlphaHitRegion
extends Node
## Windows also clips rendering outside this polygon. Capture the independent
## SubViewport, NEVER the already-clipped OS window, to avoid feedback erosion.
var source: SubViewport
var desktop: DesktopWindowController
var elapsed: float = 0.0
var polygon_count: int = 0
var last_polygon := PackedVector2Array()
var supported: bool = false
var reported_error: bool = false
var started_ms: int = 0

func _ready() -> void:
 supported = DisplayServer.get_name() in ["Windows", "X11"]
 started_ms = Time.get_ticks_msec()
 if not supported and DisplayServer.get_name() != "headless":
  desktop.window_mode = "UNSUPPORTED backend: full input"
  Log.error("Native mouse region unsupported on " + DisplayServer.get_name())

func _process(delta: float) -> void:
 if source == null or desktop == null or not supported:
  return
 elapsed += delta
 if elapsed < 0.1:
  return
 elapsed = 0.0
 if not desktop.passthrough_enabled or desktop.dragging:
  desktop.window.mouse_passthrough_polygon = PackedVector2Array()
  desktop.window_mode = "drag / full input" if desktop.dragging else "manual / full input"
  return
 var image = source.get_texture().get_image()
 if image == null or image.is_empty():
  return
 var polygons = polygons_from_image(image)
 polygon_count = polygons.size()
 if polygons.is_empty() and Time.get_ticks_msec() - started_ms < 2000:
  return # The first GPU frame may not be ready yet.
 if polygons.size() != 1:
  # Never silently use a bounding rectangle or convex hull as precise alpha hit testing.
  desktop.window.mouse_passthrough_polygon = PackedVector2Array()
  desktop.window_mode = "SAFE FALLBACK: full input; alpha mask invalid"
  if not reported_error:
   Log.error("Alpha silhouette must be one connected contour; got %d. Pass-through NOT active." % polygons.size())
   reported_error = true
  return
 var polygon: PackedVector2Array = polygons[0]
 var scale_factor = Vector2(desktop.window.size) / Vector2(image.get_size())
 for index in polygon.size():
  polygon[index] *= scale_factor
 last_polygon = polygon
 desktop.window.mouse_passthrough_polygon = polygon
 desktop.window_mode = "alpha polygon / " + DisplayServer.get_name()

static func polygons_from_image(image: Image) -> Array[PackedVector2Array]:
 var bitmap = BitMap.new()
 bitmap.create_from_image_alpha(image, 0.02)
 return bitmap.opaque_to_polygons(Rect2i(Vector2i.ZERO, image.get_size()), 0.5)
