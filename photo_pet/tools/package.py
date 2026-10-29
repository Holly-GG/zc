from pathlib import Path
import argparse,hashlib,zipfile,json,os
parser=argparse.ArgumentParser()
parser.add_argument('--allow-large',action='store_true',help='Produce an artifact ZIP even when it exceeds the direct Git blob limit')
args=parser.parse_args()
root=Path(__file__).resolve().parent.parent
exe=root/'dist/Niangao-PhotoPet.exe'
assert exe.is_file(),'Build Windows exe first'
sha=hashlib.file_digest(exe.open('rb'),'sha256').hexdigest()
(root/'dist/Niangao-PhotoPet-exe-SHA256.txt').write_text(sha+'  Niangao-PhotoPet.exe\n')
with zipfile.ZipFile(root/'dist/Niangao-PhotoPet-windows.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.write(exe,'Niangao-PhotoPet/Niangao-PhotoPet.exe')
    for name in ['README.md','FEATURES.md','LATEST.md','MOTIONS.md','ASSET_PROVENANCE.md','API_COMPATIBILITY.md','CHAT_MEMORY.md','ALBUM_AND_FONTS.md','REFERENCE_REDRAW.md','FULL_PAGE_SKINS.md','WINDOWS_UI_BUILD.md','dist/Niangao-PhotoPet-exe-SHA256.txt']:
        z.write(root/name,'Niangao-PhotoPet/'+Path(name).name)
    for p in (root/'licenses').rglob('*'):
        if p.is_file():z.write(p,'Niangao-PhotoPet/licenses/'+str(p.relative_to(root/'licenses')))
    for p in (root.parent/'fonts').glob('*'):
        if p.is_file():z.write(p,'Niangao-PhotoPet/fonts/'+p.name)
    results=root/'test-results'
    if results.exists():
        for p in results.glob('*.log'):z.write(p,'Niangao-PhotoPet/validation/'+p.name)
bundle=root/'dist/Niangao-PhotoPet-windows.zip'
sha=hashlib.file_digest(bundle.open('rb'),'sha256').hexdigest()
(root/'dist/Niangao-PhotoPet-SHA256SUMS.txt').write_text(sha+'  Niangao-PhotoPet-windows.zip\n')
direct_download=exe.stat().st_size<104_000_000 and bundle.stat().st_size<104_000_000
if not args.allow_large:assert direct_download,'Direct GitHub blob must stay below 100 MiB with safety margin; use --allow-large for an artifact ZIP'
if os.environ.get('GITHUB_OUTPUT'):
    with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as output:output.write('direct_download='+str(direct_download).lower()+'\n')
print('WINDOWS_ZIP',bundle,bundle.stat().st_size,sha)
print('DIRECT_DOWNLOAD_ELIGIBLE',direct_download)
