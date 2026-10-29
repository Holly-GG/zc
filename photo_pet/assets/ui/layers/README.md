# 独立 PNG 展示层

`manifest.json` 是来源与完整性清单。既有独立插画从 `../botanical/` 无损编码为 PNG；这些文件不是整页截图的自动裁切，也不是其他会话中未同步的原始拆分文件。

`header-ornament.png` 为本轮补生成的透明植物页眉装饰，不含文字或角色。位于标题区底角的预留留白，不接受鼠标或键盘输入。

`niangao/layers.py` 缓存读取图层。文字、按钮、输入、动态数据继续由 Qt Widgets 绘制，禁止在图层中烘焙运行状态。完整规则见 `docs/design-system/LAYERED_UI.md`。
