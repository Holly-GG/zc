"""Publish tested ZIP to existing download branch without changing source checkout."""
import os,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
dist=root/'photo_pet/dist'
def run(*args,**kwargs):return subprocess.check_output(['git',*args],cwd=root,**kwargs).decode().strip()
run('config','user.name','github-actions[bot]');run('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
with tempfile.TemporaryDirectory(prefix='niangao-publish-') as temporary:
    temp=Path(temporary)
    readme=temp/'README.md'
    readme.write_text('''# 年糕 Windows 桌宠下载\n\n[直接下载照片版 Windows 桌宠](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet-windows.zip)\n\n解压后双击 Niangao-PhotoPet.exe，无需安装 Python 或 Godot。照片姿态为基于用户参考图的 AI 编辑补全，不是原图逐像素抠取。\n\n[旧版 Godot P0](https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-P0-windows.zip)\n\n源码见 main 分支 photo_pet/。请勿把旧版 Godot 的验证结论当成照片版结果。\n''',encoding='utf-8')
    env=os.environ.copy();env['GIT_INDEX_FILE']=str(temp/'index')
    run('fetch','--depth=1','origin','windows-download')
    parent=run('rev-parse','FETCH_HEAD')
    run('read-tree',parent,env=env)
    paths=[('README.md',readme)]
    paths.extend((name,dist/name) for name in ['Niangao-PhotoPet-windows.zip','Niangao-PhotoPet-SHA256SUMS.txt'])
    for name,path in paths:
        oid=run('hash-object','-w',str(path));run('update-index','--add','--cacheinfo',f'100644,{oid},{name}',env=env)
    tree=run('write-tree',env=env)
    commit=run('commit-tree',tree,'-p',parent,input=b'Publish tested Niangao photographic desktop pet\n')
    run('push','origin',f'{commit}:refs/heads/windows-download')
    print('DIRECT_DOWNLOAD https://github.com/Holly-GG/zc/raw/refs/heads/windows-download/Niangao-PhotoPet-windows.zip')
