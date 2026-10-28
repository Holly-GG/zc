# My Project

This project is being developed with Codex.


## 最新：年糕照片桌宠

[直接下载照片版 Windows ZIP](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet-windows.zip) · [照片版说明与源码](photo_pet/README.md)

照片版提供自动巡逻、Windows 应用窗口外边界互动、中文气泡、右键摸头/投喂/睡觉/大小/置顶/退出以及滚轮缩放。照片姿态经 AI 去背景与推测补全，鼻侧棕点为重点，不宣称不可见部分完全准确。原 Godot P0 保留在下方。

# 年糕 Niangao P0

Windows 10/11 x64 桌面宠物第一阶段工程，Godot **4.6.3 stable** / GDScript / Compatibility 3D / JSON。**几何猫咪为 PLACEHOLDER，不是最终年糕模型。** 无复杂 AI 或真实 3D 家园。

验证状态：42 项基础测试、7 项 X11 桌面检查通过；Windows exe 在 Wine 渲染通过，但 Wine 透明区域点击测试失败。Windows 10/11 原生验收尚未执行，不能宣称 Windows 穿透全部完成。

验证状态：42 项基础测试、7 项 X11 桌面检查通过；Windows exe 在 Wine 渲染通过，但 Wine 透明区域点击测试失败。Windows 10/11 原生验收尚未执行，不能宣称 Windows 穿透全部完成。

## 直接运行 exe

`exports/windows/Niangao-P0.exe` 是内嵌 PCK 的独立 Windows x64 程序，不需要安装 Godot 或 Blender。未签名；无安装器。显卡需支持 OpenGL 3.3，Windows 需要可用的桌面合成环境。

拖动猫咪移动；点击猫咪派发事件；右键或 F3 打开/关闭调试窗口；T 切换置顶；H 隐藏；Esc 保存并退出。托盘提供显示、隐藏、调试和退出。无托盘的平台自动打开调试窗口提供恢复入口。关闭调试面板不会退出程序。

第一次在主屏幕可用工作区右下角启动；随后恢复用户位置。用户配置位于 `%APPDATA%/Godot/app_userdata/Niangao P0/config.json`，不会写回程序资源。显示器变化每秒检查工作区并修正越界。

## 开发运行

已有 Godot 4.6.3：

```powershell
godot --editor --path .
godot --path .
.\tools\run-tests.ps1 -Godot 'C:\path\Godot_v4.6.3-stable_win64_console.exe'
```

未安装 Godot：在 PowerShell 中运行 `./tools/bootstrap-windows.ps1`（下载官方编辑器和约 1.2 GB 导出模板，校验 SHA-512），然后执行 `./tools/run-tests.ps1`、`./tools/export-windows.ps1`。工具缓存保存在 LocalAppData，工程不依赖系统安装。Blender 仅 P1 美术制作需要；当前环境验证版本 4.3.2，可从 https://www.blender.org/download/ 安装，exe 运行不需要 Blender。

Linux：`bash tools/run-tests.sh`；有显示环境时 `godot --path . --audio-driver Dummy -- --render-smoke` 做透明 3D 渲染检查。`--headless` 只能测脚本，不能验证画面或操作系统穿透。

## Windows 导出

Godot 编辑器 → Editor → Manage Export Templates 安装 4.6.3 模板 → Project → Export → Windows Desktop → Export Project，或：

```powershell
./tools/export-windows.ps1 -Godot 'C:\path\Godot_v4.6.3-stable_win64_console.exe'
```

导出预设使用 x86_64、内嵌 PCK，不依赖 Blender、.NET、Python 或原生扩展。`application/modify_resources=false` 避免依赖 rcedit。正式签名和安装包属于后续发布任务。

## 目录

```text
project.godot / export_presets.cfg
scenes/                  main.tscn、character.tscn
scripts/core/            EventBus、Config、Log、主场景组装、家园流程接口
scripts/desktop/         窗口控制、位置算法、Alpha 输入区域
scripts/character/       PLACEHOLDER 几何猫、AnimationController
scripts/debug/           独立调试窗口、可选诊断日志
assets/models/           后续 GLB（当前由脚本生成模型）
assets/animations/       动画资源说明
assets/textures/ audio/ references/
data/                    默认 JSON
 tests/                  基础测试、下层输入测试场景
 tools/                  安装、测试、导出、Windows 验收脚本
 docs/                   架构、验证结果、Windows 验收、P1 资产清单
 exports/windows/        exe、校验和
```

职责与技术限制见 [architecture.md](docs/architecture.md)；真实测试结果见 [validation.md](docs/validation.md)；Windows 真机验收见 [windows-validation.md](docs/windows-validation.md)；P1 资源见 [art-p1.md](docs/art-p1.md)。透明设置本身不是鼠标穿透，Windows 原生验收未执行前不能声称全部通过。

## GitHub 下载 Windows 程序

进入本仓库的 **Actions → Build Niangao Windows → 最新成功运行 → Artifacts → Niangao-P0-Windows-x64** 下载。登录 GitHub 后可下载 artifact；保留 30 天，到期可重新运行工作流。

先解压 artifact，再解压里面的 `Niangao-P0-windows.zip`，双击 `Niangao-P0.exe`。Windows 包内包含许可、已知问题和原生验收脚本。

工作流在 Windows runner 上安装经官方 SHA-512 校验的 Godot 4.6.3，运行基础测试并导出 exe。自动构建通过不代表 Windows 桌面鼠标穿透、DPI 或显示器热拔已通过验收。可手动使用 **Run workflow** 重新构建。
