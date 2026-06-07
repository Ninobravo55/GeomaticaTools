import os
import glob

qgis_path = r'C:\PROGRA~1\QGIS34~1.11'
lrelease = glob.glob(os.path.join(qgis_path, '**', 'lrelease.exe'), recursive=True)
if lrelease:
    print(f"Found lrelease: {lrelease[0]}")
    os.system(f'"{lrelease[0]}" i18n\\geomaticape_en.ts')
    print('Compiled.')
else:
    print('Not found.')
