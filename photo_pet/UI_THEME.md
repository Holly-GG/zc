# 年糕 · 参考图水墨植物手账重绘

本版依据用户新提供的八页界面参考图及两张年糕姿态图实施：水墨排线年糕、蓝色勿忘我、白百合、藤蔓、金色尖拱与复古水彩纸。总览采用左侧插画与右侧状态，照料增加物品图标，其他页面使用各自配色及不同姿态。聊天页只在边缘保留小面积花边，正文与输入区不铺纹理。

全部功能继续使用真实 Qt 控件，未用整页 UI 图片替代界面。未改 API、数据结构、导航顺序、按钮操作或桌宠动作资源。没有新增依赖。

## 修改文件

- `niangao/theme.py`：集中色板变量、纸张卡片、物品按钮、时钟和焦点样式。Qt 不支持浏览器 CSS 自定义属性，变量经 Template 编译为 QSS。
- `niangao/journal.py`：独立装饰绘制、九宫格花边、插画缓存与姿态选择；全部位于控件下方，不接管鼠标/键盘。
- `niangao/life/window.py`：接入标题插画、总览插画及照料按钮图标，所有业务处理保持原样。
- `assets/ui/botanical/`：四份独立插画/纹理资源及来源说明，保留透明背景，未生成带按钮或文字的整张界面。

## 八页预览

[总览](validation/reference-redraw/0.png) · [照料](validation/reference-redraw/1.png) · [商城](validation/reference-redraw/2.png) · [背包](validation/reference-redraw/3.png) · [专注](validation/reference-redraw/4.png) · [聊天](validation/reference-redraw/5.png) · [日记](validation/reference-redraw/6.png) · [设置](validation/reference-redraw/7.png)

原有 740×540、860×650 窗口适配，长内容仍通过原滚动区域访问。不会为了复刻参考图而删除设置项、压缩可读文字或隐藏业务控件。参考图与实际原有软件内容不同，因此布局按真实控件数量适配，非逐像素截图复刻。

## 素材边界

新水墨图是依照本轮参考图生成的 AI 插画，保留年糕辨识特征，但不宣称是真实照片或已逐根毛发准确还原。原商品图片和角色动态动作未在此次逐件重绘；用户提供的八页参考图没有作为可点击界面的整图背景。
