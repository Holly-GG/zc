# 年糕 · 照片桌宠与生活馆

**[直接下载 EXE](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet.exe)** · [ZIP 备用包](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet-windows.zip)

EXE 下载后可直接双击；ZIP 包解压后双击 `Niangao-PhotoPet.exe`；Windows 10/11 x64，不需要安装 Python、Godot、Blender。与旧 Godot 几何 P0 是两个独立程序，请运行新的 PhotoPet exe。

新增八页生活馆：总览、照料动作、实验 3D 家园、商城背包、专注待办、聊天、日记和设置。右键猫咪或托盘可打开。[功能完成表与建模限制](FEATURES.md)。[Blender/GLB 下载](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-3D-source.zip)。

## 角色与使用

角色来自用户提供的布偶猫参考照片，经 AI 图像编辑生成透明资产、爬行动画和睡觉姿态。蓝眼睛、深棕面罩/耳朵、不对称白纹、白胸腹/爪子和**鼻侧棕色小点**为重点；未对角色做左右翻转，以免反转标记。不可见爪子、尾巴和新姿态是推测性补全，不是原照片逐像素抠图，也不能保证完全复原不可见细节。详见 ASSET_PROVENANCE.md。

- 默认透明、无边框、置顶；仅角色 Alpha 遮罩区域接收输入，透明区域传给下层应用。
- 自动在当前显示器的可用工作区巡逻；使用左右各四帧照片补全步态，随机停留、原地摆爪玩耍和显示中文气泡。
- Windows 原生 `EnumWindows` 每秒检测可见顶层应用的**外边界**；靠近边缘时绕行或停留玩耍。不会分析窗口内部按钮、图标或读取屏幕内容。最大化应用的内部仍可巡逻，边界才是障碍。
- 左键拖动，轻点摸头；滚轮缩放。右键菜单：摸摸头、喂吃的、让它睡觉/叫它起床、调整大小、置顶开关、自由巡逻开关、退出程序。
- 气泡使用独立透输入窗口，按上/右/左/下寻找不遮挡猫咪的位置；空间不足则不显示。
- 托盘可找到年糕、摸头、投喂、睡觉和退出。
- 配置保存在 `%APPDATA%/NiangaoPhotoPet/settings.json`，关闭时保存位置/大小/置顶/巡逻设置；启动与每秒巡检夹入现有显示器工作区。

UI 使用用户提供的色板：`#EFF6F1`、`#899F84`、`#8CCCCA`、`#40A387`、`#305E63`。

## 开发、测试、构建

```powershell
cd photo_pet
py -3.12 -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install -r requirements-build.txt
python main.py
$env:QT_QPA_PLATFORM='offscreen'
python -m pytest -q
python tools/build.py
python tools/package.py
```

正常桌面运行前删除测试用的 `QT_QPA_PLATFORM=offscreen`：`Remove-Item Env:QT_QPA_PLATFORM`。Windows 的原生验收：

```powershell
python tools/test_windows_desktop.py --exe dist/Niangao-PhotoPet.exe --output test-results/native
```

该脚本在独立测试配置下移动鼠标并创建下层测试窗口，应在空闲测试桌面执行。自动化使用真实系统鼠标事件，不直接向下层发送伪造点击。

依赖：Python 3.12、PySide6/Qt 6.8.3、PyInstaller 6.13.0；pytest 8.3.5 为测试依赖。exe 内嵌代码、图片和 Qt 动态库。许可见 licenses/；源码和构建脚本公开，可重新构建替换 Qt 库。默认不联网；联网 AI 须主动开启并提供密钥，不设置开机启动、不安装鼠标钩子。

## 模块

`config.py` 用户设置；`geometry.py` 工作区/DPI/边界/气泡算法；`behaviour.py` 单调时钟状态与自主移动；`windows.py` Win32 窗口边界；`art.py` 照片帧/Alpha 区域；`bubble.py` 色板与气泡；`dialogue.py` 随机中文文案；`pet.py` 交互与窗口；`main.py` 启动、崩溃日志与打包 smoke。

## 已知限制与验证范围

本次基础/Qt/养成/API 测试 44 项、Linux X11 的 8 项真实桌面输入检查，以及 Windows 构建机上的 10 项原生桌面检查已通过，记录见 validation/。Windows 工作流另外要求打包 exe smoke、真实 Win32 点击穿透/拖动/滚轮/菜单/窗口枚举/退出恢复检查通过，才发布新的直链包。CI 结果以对应运行日志为准。

自动化 Windows runner 不是用户的每一种桌面环境；Windows 10/11 不同版本、150%/200% 混合 DPI、运行中拔插显示器、自动隐藏任务栏、各种受保护/游戏/远程应用仍需实机回归。位置会使用当前工作区修复；Windows 窗口检测若系统拒绝访问，日志记录错误并保留屏幕内巡逻。

桌面形象是照片精灵动画；生活馆另有简化实验 3D 猫，无完整骨骼/布料/真实长毛物理。走路与睡觉是基于照片生成的推测姿态，鼻点在小尺寸下可能只有数个像素。Qt Alpha 二值输入区域会略裁掉低 Alpha 胡须/毛边。未知窗口内部元素不作为障碍；没有屏幕内容识别或点击第三方应用。

exe 尚未进行商业代码签名，没有自动更新或安装器。Qt/PySide LGPL 许可文本、依赖说明随包提供。

新增模块：life/engine.py 养成事务；age.py 年龄；catalog.py 商品；window.py 八页 UI；ai.py API/DPAPI；jobs.py 后台任务主线程回调；home3d.py 实时空间；glb.py 无骨骼 GLB 读取；layout.py 家具占地。Blender 4.3.2 构建模型，Qt3D 6.8.3 渲染；内嵌 OFL 中文字体子集。
