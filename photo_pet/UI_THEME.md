# 年糕手账界面、字体与相册

本版采用奶油旧纸、墨绿文字、蓝白植物、水墨插画和手写英文副标题。首页真实状态环、分栏纸卡、照料按钮、背包分类与聊天气泡均为真实Qt控件/绘制，不使用整页截图冒充界面。原有八页索引保留，相册追加index 8，没有新增运行时依赖。

## 实机预览

[首页](validation/album-journal/0.png) · [照料](validation/album-journal/1.png) · [商城](validation/album-journal/2.png) · [背包](validation/album-journal/3.png) · [专注](validation/album-journal/4.png) · [聊天](validation/album-journal/5.png) · [日记](validation/album-journal/6.png) · [设置](validation/album-journal/7.png) · [空相册](validation/album-journal/8.png) · [导入演示](validation/album-journal/8-imported-demo.png)。

预览为1260×820宽屏，另保存740×540、860×650的首页、聊天和相册。导入演示使用临时素材文件，不是用户照片，不会随程序填充相册。

## 字体与实现

根目录 fonts/ 和 Niangao-Fonts.zip 收录正文Noto Sans SC、标题Noto Serif SC、英文副标题Allura的更名子集、配置和OFL许可证；EXE内置，无需安装字体。详见 [相册与字体说明](ALBUM_AND_FONTS.md)。

theme.py、typography.py、journal.py、journal_components.py负责展示；life/window.py接入已有控制器；life/album.py和album_page.py为新增相册。原life.json、聊天数据库、API和桌宠动作没有因视觉工作重构。

## 素材边界

原年糕候选插画保留待确认标记，相册专属角色位显示待制作。新月光花窗、森林收藏装饰不含动物。相册照片不会自动变成角色素材。原商品图和角色动作未逐项重绘，不宣称逐像素复刻全部参考图。
