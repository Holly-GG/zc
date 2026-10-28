from pathlib import Path
import hashlib,zipfile,json
root=Path(__file__).resolve().parent.parent
exe=root/'dist/Niangao-PhotoPet.exe'
assert exe.is_file(),'Build Windows exe first'
sha=hashlib.file_digest(exe.open('rb'),'sha256').hexdigest()
(root/'dist/Niangao-PhotoPet-exe-SHA256.txt').write_text(sha+'  Niangao-PhotoPet.exe\n')
with zipfile.ZipFile(root/'dist/Niangao-PhotoPet-windows.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.write(exe,'Niangao-PhotoPet/Niangao-PhotoPet.exe')
    for name in ['README.md','FEATURES.md','MOTIONS.md','ASSET_PROVENANCE.md','dist/Niangao-PhotoPet-exe-SHA256.txt']:
        z.write(root/name,'Niangao-PhotoPet/'+Path(name).name)
    for p in (root/'licenses').rglob('*'):
        if p.is_file():z.write(p,'Niangao-PhotoPet/licenses/'+str(p.relative_to(root/'licenses')))
    results=root/'test-results'
    if results.exists():
        for p in results.glob('*.log'):z.write(p,'Niangao-PhotoPet/validation/'+p.name)
bundle=root/'dist/Niangao-PhotoPet-windows.zip'
sha=hashlib.file_digest(bundle.open('rb'),'sha256').hexdigest()
(root/'dist/Niangao-PhotoPet-SHA256SUMS.txt').write_text(sha+'  Niangao-PhotoPet-windows.zip\n')
assert bundle.stat().st_size<95_000_000,'Direct GitHub blob must stay below 100MB'
print('WINDOWS_ZIP',bundle,bundle.stat().st_size,sha)

with zipfile.ZipFile(root/'dist/Niangao-3D-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in (root/'assets/models').glob('*'):
        if p.is_file():z.write(p,'Niangao-3D/assets/models/'+p.name)
    z.write(root/'tools/modeling/build_niangao.py','Niangao-3D/tools/modeling/build_niangao.py')
    z.write(root/'FEATURES.md','Niangao-3D/FEATURES.md')
print('MODEL_SOURCE_ZIP',root/'dist/Niangao-3D-source.zip')
