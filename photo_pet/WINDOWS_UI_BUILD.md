# Windows UI 构建 2026.10.30.1

此版本把当前独立PNG组件界面、真实字体、工作台与专注小窗布局修改打入Windows x64 GUI EXE；内嵌96个页面组件PNG、51个物件PNG及字体。

独立EXE可直接运行，无需另装Python或Qt。需要替换字体时，可将包中的 `fonts/` 放在EXE旁，在 `roles.json` 修改后重启。

本次本地构建使用官方Python NuGet 3.12.10、PySide6 6.8.3、PyInstaller 6.13.0，在隔离Wine 10环境执行Windows工具链。已验证PE32+ x64/GUI格式、文件版本、147个内嵌PNG与字体配置哈希；Windows Python下5项图层/窗口检查通过，EXE的启动、生活馆、桌面照料、工作模式、动作资源及相册冒烟通过。

Wine执行与窗口截图检查不等同于Windows真机混合DPI、多显示器或点击穿透验收。此前Linux构建结果没有冒称Windows EXE结果。

完整图层版超过GitHub普通Git blob的100MiB限制：使用本次构建的EXE/ZIP或Actions Artifact；旧 `windows-download` 分支文件不会自动代表这个版本。打包脚本的 `--allow-large` 只允许生成Artifact，不放宽直接Git发布脚本的大小检查。

源码构建与版本信息分别在 `tools/build.py` 和 `version_info.txt`。本地构建/运行证据位于 `test-results/windows-build/`；这些文件不包含用户的实际聊天或相册数据。
