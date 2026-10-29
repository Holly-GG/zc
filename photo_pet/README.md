## 手账新界面与相册

新增本地照片相册（第九页），支持导入图片、按日期归档、筛选、编辑日期与导出原图；不向API上传。根目录 `fonts/` 和 `Niangao-Fonts.zip` 提供三角色可替换字体及许可证。详见 [相册与字体说明](ALBUM_AND_FONTS.md)。原有八页及其数据/API行为保留。

# 年糕 · 手绘生活馆与照片桌宠

[直接下载 Windows EXE](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet.exe) · [ZIP 备用包](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet-windows.zip)

Windows 10/11 x64，先退出旧版再双击新版，无需安装 Python、Godot 或 Blender。[本次逐条修改与预览](LATEST.md)。

当前生活馆已移除 3D 空间，提供：总览、照料动作、独立商城、独立背包、专注待办、聊天、日记、性格设置。采用年糕特征的手绘纸张 UI，桌面角色仍保留照片姿态。

- 51 个商品实物图，背包和照料页的已拥有物品可拖到桌面；物品可继续拖动、点击使用、右键收回或一键清理。
- 水碗、猫耳自动饮水机具有水位/循环水流/补水效果；一键清理不删除桌面文件。
- 性格、习惯、喜恶、口吻等保存在用户目录。每次 API 请求强制附加最新档案、真实年龄与状态；聊天和 AI 日记均覆盖，更换 Key 也不能跳过。
- 20 秒不点击年糕或生活馆后，主动互动计划频率降至原来的 30%。不降低动画帧率或专注计时准确性。
- 原有透明区域鼠标穿透、置顶、拖动、滚轮缩放、窗口外边界避让、49 个动作 ID 与合成音效保留。[动作说明](MOTIONS.md)。
- 声音、全局按键活动、光标追逐、联网 AI 默认关闭。Key 用 Windows DPAPI 加密；开启 API 后会向所填服务发送角色档案。
- 保存目录 %APPDATA%/NiangaoPhotoPet/，兼容原有位置、金币、背包、任务和日记。旧 3D 源资产仅保留历史资料，不打入 EXE。

## 本次桌面扩展

- 同一尺寸下使用固定舞台、共用落脚线及逐动作头部尺度校准，不再把每个姿态单独铺满窗口。各姿态自然的宽高差异保留。
- 猫咪右键菜单或托盘选择“工作模式”：完整年糕的随机轻待机姿态；点击打开紧凑对话小窗，支持离线互动和主动启用的 API 聊天。工作模式暂停走动和主动气泡，低频随机理毛、歪头、舔爪、甩尾。轻待机与普通桌宠位置分别保存。
- 日记公历/中国农历覆盖 2020-01-01 至 2069-12-31；显示闰月、传统节日，事件使用中国标准时间 UTC+08:00。不是未来法定调休预测。
- 摆件支持重力、平台落地、球弹跳、老鼠跑动、激光模拟红点、心情随机接受/拒绝；拒绝不会消耗食物。右键物品可固定，Shift+右键冻干可打开菜单。
- 粮袋每份十二粒，冻干每份八颗，右键一次只掉一颗；小颗粒可掉落、被吃或收回。部分剩余会保存，清理不补满。首次升级赠送一套扩展用品，在背包中拖出即可。
- 隧道穿行、抓板磨爪、猫窝休息、地毯踩奶打滚、草地追逐等为二维照片/路径演出；猫树新增抓握及蹲守素材，未宣称完成三维骨骼攀爬、真实排泄或无瑕疵肢体接触。
- “专注与待办”增加可独立摆放的小窗。添加/完成任务及猫靠近时可响应任务关键词；只读取你填写的待办，不识别屏幕其他文字。
- 1000 条按 40 个场景组合编写的本地短句，最近八条避免重复；本地聊天按关键词选择，联网时仍强制读取最新档案。

## 桌面工作台

进入工作模式自动显示带“API 对话”和“应用搜索”的工作台。对话使用已保存的 API 配置，需勾选开关；本地回应会明确标注。应用搜索覆盖功能、物品、动作和待办，可点击跳转。点击猫咪或右键菜单可重新打开。设置页接口下拉框仅点击选择，滚轮不再误切换。

## 本地聊天与额度

聊天写入本地SQLite和逐会话JSON，可按日期回看与导出；临近各模型阈值自动摘要并开启承接会话。实时计数标注估算/保守预算，实际用量按API usage记账；每日额度覆盖聊天、摘要、测试与AI日记，额度不足则拦截。仅轻量思考，输出最多2,048 token。[完整说明与限制](CHAT_MEMORY.md)。

## 模型 API

支持 OpenAI Chat Completions / Responses、Claude Messages、Gemini 原生文本接口，提供 DeepSeek 等常见平台预设及“保存并测试连接”。真实模型 ID 由用户控制台决定；协议自测不能代替真实账户连接。Key 仅在应用密码框填写，勿发到聊天。[兼容范围与测试步骤](API_COMPATIBILITY.md)。

## 开发与构建

Python 3.12、lunar-python 1.4.8（MIT）、PySide6 6.8.3、PyInstaller 6.13.0、pytest 8.3.5。

    cd photo_pet
    python -m pip install -r requirements-build.txt
    python main.py
    python -m pytest -q
    python tools/build.py
    python tools/package.py

测试可设置 QT_QPA_PLATFORM=offscreen；正常桌面运行前移除此变量。Windows 原生交互验收会在独立配置下创建测试窗口并移动测试机鼠标：

    python tools/test_windows_desktop.py --exe dist/Niangao-PhotoPet.exe --output test-results/native

打包程序另提供 --smoke、--suite-smoke、--motion-smoke、--desktop-smoke、--expanded-smoke。Linux 有窗口管理器、合成器与 xdotool 时，可运行 tools/test_x11.py 和 tools/test_stationery_x11.py。

[资产来源](ASSET_PROVENANCE.md) · [最新逐条说明](LATEST.md) · licenses/ 内含依赖许可。照片动作经 AI 参考补全，不是完整骨骼动画；合成声音不是年糕真实录音。手绘面部保留识别特征，仍不能冒充照片级还原。
