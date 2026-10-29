# 年糕可替换字体包

此文件夹位于仓库根目录；同目录的 `Niangao-Fonts.zip` 为可单独保存的字体包。

- NiangaoSans.ttf：Noto Sans SC，正文和操作控件，400 字重子集。
- NiangaoSerif.ttf：Noto Serif SC，中文标题和卡片分区，600 字重子集。
- NiangaoScript.ttf：Allura，英文手写副标题，正文不使用手写体。
- roles.json：字体角色、真实字体家族名、文件名及逻辑像素字号。正文允许12–17，标题/英文20–30。

字体均按 SIL OFL 1.1 分发，相应许可证同目录保留；子集已更名，原版权保留在字体内部。原始字体来源为 Google Fonts 仓库的 ofl/notosanssc、ofl/notoserifsc、ofl/allura。manifest.json 记录包内文件的 SHA-256。

修改方式：放入具有分发许可的 TTF/OTF，修改 roles.json 的 file、family（字体内部的英文家族名）和 size，重启程序。无需向系统安装字体。请保留许可证；不要仅改文件名却不更新 family。字体文件必须位于此目录内。

源码运行读取本目录；构建脚本把本目录复制进 EXE。ZIP 版同时附带 `fonts/`；单独 EXE 也有内置字体。可把本文件夹放在 EXE 旁边作为替换包，程序重启后优先读取它。删除旁置包可恢复内置字体。若改动正文文案后需要扩充子集，可用开发工具 `photo_pet/tools/prepare_font_bundle.py` 和有许可的原始字体重新生成；fonttools 仅在制作字体包时需要，运行程序不需要。

字体子集覆盖现有界面及常用简体字；用户照片标题中的罕用字由 Qt 字体回退补齐，不把缺字方框当正常输出。替换后需检查中文、数字、标点、英文副标题和窗口溢出。
