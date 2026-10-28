class_name WindowGeometry
extends RefCounted

static func clamp_to_area(position: Vector2i, size: Vector2i, area: Rect2i, margin: int = 16) -> Vector2i:
 var inset = Vector2i(margin, margin)
 var low = area.position + inset
 var high = area.end - size - inset
 return Vector2i(clampi(position.x, low.x, maxi(low.x, high.x)), clampi(position.y, low.y, maxi(low.y, high.y)))

static func bottom_right(size: Vector2i, area: Rect2i, margin: int = 16) -> Vector2i:
 return clamp_to_area(area.end - size - Vector2i(margin, margin), size, area, margin)
