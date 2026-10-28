# Windows 10 / 11 原生验收（尚未执行）

当前开发机为 Linux。已生成 Windows x64 exe，不能把导出成功或 Linux 输入测试说成 Windows 完整验收通过。附带自动测试需要在真实 Windows 交互桌面运行。

## 自动输入验收

关闭已有 Niangao 实例，在工程根目录 PowerShell 中执行：

```powershell
./tools/acceptance-windows.ps1 -ResetPosition
```

脚本将鼠标临时移动，创建独立不透明 WinForms 下层应用，再启动 exe。`-ResetPosition` 临时备份并移除已有用户配置，以验证首次启动位置；结束时恢复原配置。无该参数时保留用户设置，跳过首次位置断言。请让测试完成期间桌面不被其它窗口遮挡。

断言：首次右下角/工作区边距、透明角落点击到下层、角色身体点击仅到宠物 EventBus、角色矩形内头旁透明凹区能点击下层、拖动移动、WM_CLOSE 正常退出、配置保存和重启恢复。输入使用真实系统鼠标事件，不用直接给下层发送 WM_LBUTTONDOWN 伪造穿透。

结果写入 exports/windows/native-acceptance.txt，抛异常就是失败，部分 PASS 不能视为全部通过。诊断数据在 user://diagnostics.jsonl（仅 `-- --diagnostics` 启用）。脚本本身当前未经 Windows PowerShell 执行，需在 Windows 上验证；仅有状态记录不等于成功。

## 人工检查

- Windows 10、Windows 11 分别双击 exe；无黑色矩形，3D PLACEHOLDER 可见，Alpha 外能看见且操作下层应用。近边缘、耳间、身体旁、尾旁多点测试。
- 桌面置顶开关；拖到不同窗口上方；快速拖出角色轮廓后松手，避免卡住 dragging；点击头部确认 PET_HEAD_TOUCHED。
- 托盘显示/隐藏/调试/退出；F3 关闭 Debug Overlay；隐藏后仍能托盘恢复；关闭调试窗口不结束程序。
- 任务栏分别在底/左/右/顶、自动隐藏与普通模式；首次位置在可用工作区；在小屏和高 DPI 无越界。
- 100%、150%、200% DPI；双屏混合缩放、负坐标副屏；移动后保存退出，断开副屏后重启，窗口回到现存屏幕；运行中改分辨率和热拔，一秒内修正。
- 无托盘时调试窗口提供恢复，关闭调试窗口前若宠物隐藏则先显示宠物。
- 删除某动作映射/改动画名，不崩溃；Debug 归家按钮连续点击不重复开启活动请求；投喂或等待实际 60 秒恢复 autonomous。此过程仅调试接口，没有真实家园。
- 后续替换 GLB 后必须重新执行 Alpha 连通性与透点击检查，不能沿用占位猫测试结论。

## 技术限制

当前动态多边形只能表达一个无内部透明洞的连续外轮廓，边缘有 Alpha/轮廓简化/10Hz 更新近似。Windows 会裁剪多边形外的画面。多轮廓时会明确退回完整窗口输入并记录错误。复杂长毛需要原生 HRGN/GDExtension 或分层窗口方案。

exe 未进行代码签名，未提供安装器或自动更新；运行依赖 Windows 显卡 OpenGL 3.3 驱动。Windows on ARM、远程桌面、无桌面合成环境未验证。
