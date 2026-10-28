# 年糕 · 手绘生活馆与照片桌宠

[直接下载 Windows EXE](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet.exe) · [ZIP 备用包](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet-windows.zip)

Windows 10/11 x64，先退出旧版再双击新版，无需安装 Python、Godot 或 Blender。[本次逐条修改与预览](LATEST.md)。

当前生活馆已移除 3D 空间，提供：总览、照料动作、独立商城、独立背包、专注待办、聊天、日记、性格设置。采用年糕特征的手绘纸张 UI，桌面角色仍保留照片姿态。

- 44 个商品实物图，背包和照料页的已拥有物品可拖到桌面；物品可继续拖动、点击使用、右键收回或一键清理。
- 水碗、猫耳自动饮水机具有水位/循环水流/补水效果；一键清理不删除桌面文件。
- 性格、习惯、喜恶、口吻等保存在用户目录。每次 API 请求强制附加最新档案、真实年龄与状态；聊天和 AI 日记均覆盖，更换 Key 也不能跳过。
- 20 秒不点击年糕或生活馆后，主动互动计划频率降至原来的 30%。不降低动画帧率或专注计时准确性。
- 原有透明区域鼠标穿透、置顶、拖动、滚轮缩放、窗口外边界避让、47 个动作 ID 与合成音效保留。[动作说明](MOTIONS.md)。
- 声音、全局按键活动、光标追逐、联网 AI 默认关闭。Key 用 Windows DPAPI 加密；开启 API 后会向所填服务发送角色档案。
- 保存目录 %APPDATA%/NiangaoPhotoPet/，兼容原有位置、金币、背包、任务和日记。旧 3D 源资产仅保留历史资料，不打入 EXE。

## 开发与构建

Python 3.12、PySide6 6.8.3、PyInstaller 6.13.0、pytest 8.3.5。

    cd photo_pet
    python -m pip install -r requirements-build.txt
    python main.py
    python -m pytest -q
    python tools/build.py
    python tools/package.py

测试可设置 QT_QPA_PLATFORM=offscreen；正常桌面运行前移除此变量。Windows 原生交互验收会在独立配置下创建测试窗口并移动测试机鼠标：

    python tools/test_windows_desktop.py --exe dist/Niangao-PhotoPet.exe --output test-results/native

打包程序另提供 --smoke、--suite-smoke、--motion-smoke、--desktop-smoke。Linux 有窗口管理器、合成器与 xdotool 时，可运行 tools/test_x11.py 和 tools/test_stationery_x11.py。

[资产来源](ASSET_PROVENANCE.md) · [最新逐条说明](LATEST.md) · licenses/ 内含依赖许可。照片动作经 AI 参考补全，不是完整骨骼动画；合成声音不是年糕真实录音。手绘面部保留识别特征，仍不能冒充照片级还原。
