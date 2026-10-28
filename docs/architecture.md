# P0 架构与接口

`main.gd` 仅组装节点、独立 SubViewport、相机、灯光和托盘；不包含状态机或窗口算法。

| 模块 | 职责 |
|---|---|
| EventBus | 11 个事件常量、注册/注销、同步派发、重复注册保护、最近事件 |
| Config | 默认 JSON 与 user://config.json 合并、类型校验、临时文件后重命名保存 |
| DesktopWindowController / WindowGeometry | 无边框、透明、置顶、拖动、隐藏/恢复、退出、工作区定位与越界修正 |
| AlphaHitRegion | 独立 3D 视口 Alpha → 凹多边形 → OS 鼠标区域，每秒更新 10 次 |
| PLACEHOLDER_Cat | 头、身体、颈、四肢、耳、尾，程序生成的简单几何；idle 呼吸占位动画 |
| PetAnimationController | play、transition_to、stop、get_current_action、is_action_available；缺失资源返回 false |
| HomeSceneController | 仅家园流程接口/调试状态；以单调毫秒时钟计算 60 秒截止时间 |
| DebugOverlay / Log | 独立可关闭调试窗口、状态/FPS/事件/错误、模拟按钮 |
| diagnostics.gd | 可选 JSONL 诊断，便于外部输入验收，默认不启用 |

## 透明与鼠标穿透的技术边界

使用 Compatibility/OpenGL，主窗口 `transparent` + `transparent_bg` + per-pixel transparency；角色在透明 SubViewport 中渲染，再显示为纹理。透明设置只负责视觉。

`BitMap.create_from_image_alpha(image, 0.02)` 和 `opaque_to_polygons(..., 0.5)` 生成凹轮廓；赋予 `Window.mouse_passthrough_polygon`，轮廓外的鼠标由 OS 交给下层窗口。Windows 在该区域外也会裁剪绘制，因此轮廓必须取自**独立 SubViewport**，不能截取已裁剪窗口。拖动时临时清空 polygon，让拖动输入完整捕获；松开后恢复。没有设置全窗口 FLAG_MOUSE_PASSTHROUGH，因为那样角色也无法点击。

当前猫咪为单个连续轮廓。多片断开毛发、粒子、具有内部透明洞的 GLB 不可直接沿用此方案。检测到 0/多个轮廓时退回完整窗口输入并显示错误，**此时不宣称穿透有效**。Alpha 阈值、0.5 像素轮廓近似和 100ms 更新会使边缘像素有少量误差；不是逐像素即时命中。未来复杂模型应使用 GDExtension：Windows HRGN 多区域合并/扣洞，或原生 hit-test/双窗口方案，并保留独立 Alpha 渲染源。无需为目前单连通占位猫增加原生依赖。

已在 X11 下用独立下层应用实际测过透明角落、头旁透明凹区与身体点击；**Windows API 的代码路径必须在 Windows 10/11 验收**，Linux 测试不能替代。参见 windows-validation.md。

## 位置与 DPI

首次按 `screen_get_usable_rect(primary)` 右下角放置，16 逻辑坐标边距；工作区排除系统保留的任务栏。保存 DisplayServer 坐标到 user://，不自己乘除 DPI，以避免双重缩放。启动、拖动结束、每秒空闲检查时重新读取当前显示器工作区；断开的屏幕坐标映射到最近的现存屏幕，再夹入工作区。小工作区按比例缩小窗口。跨屏拖动期间不主动夹住窗口。实际混合 DPI、自动隐藏任务栏和显示器热拔仍列为 Windows 人工验收项。

## 动画与 GLB 替换

`idle` 为真实 AnimationPlayer 呼吸循环，占位美术；其它五个动作 UNIMPLEMENTED。JSON 中保留 resource、animation、implemented、status；未实现、未知 ID、资源名不存在时返回 false，发出 action_unavailable，不打断当前 idle。

`replace_with_glb(PackedScene, mapping)` 可替换视觉节点，导入场景必须是 Node3D，可含 AnimationPlayer；映射显式传入。艺术资产使用 Blender → glTF 2.0 .glb → assets/models/，1 单位=1 米，+Y 向上，正面 +Z；根中心靠近地面，先匹配当前相机视野，再检查 Alpha 连通性和动画路径。不将运行时文件写入 res://。

## 家园接口边界

入口派发 `OWNER_RETURN_HOME {entry_id: 唯一字符串}` → greeting_INTERFACE_ONLY → following_INTERFACE_ONLY → snack_wait_DEBUG → 投喂/超时 → autonomous。前两个状态仅接口标识，没有门口场景或跟随移动实现。

每个 entry_id 在当前会话只能开一次请求；请求进行中忽略新的进入事件。SNACK_GIVEN 必须匹配 active_entry。截止时间是 `Time.get_ticks_msec()+60000`，不累计帧 delta；超时后只发一次 TIMEOUT。启动新会话没有未完成请求，P0 不做跨进程家园状态持久化。
