# -*- mode: python ; coding: utf-8 -*-
# Execute: python -m PyInstaller InclusaoCADIN_portavel.spec

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


block_cipher = None
PROJ = os.path.dirname(os.path.abspath(SPEC))

hiddenimports = []
for pacote in (
    "nodriver",
    "websockets",
):
    hiddenimports += collect_submodules(pacote)

hiddenimports += [
    "pandas",
    "openpyxl",
    "xlrd",
    "nest_asyncio",
    "PIL",
    "PIL.Image",
    "pandas._libs.tslibs.timedeltas",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
]

datas = []
for pacote in ("nodriver", "openpyxl", "certifi"):
    datas += collect_data_files(pacote)

modelo_planilha = os.path.join(PROJ, "modelo_planilha_cadin.csv")
if os.path.exists(modelo_planilha):
    datas.append((modelo_planilha, "."))

logo_png = os.path.join(PROJ, "assets", "logo_antt.png")
logo_ico = os.path.join(PROJ, "assets", "logo_antt.ico")
if os.path.exists(logo_png):
    datas.append((logo_png, "assets"))
if os.path.exists(logo_ico):
    datas.append((logo_ico, "assets"))

a = Analysis(
    [os.path.join(PROJ, "app.py")],
    pathex=[PROJ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "notebook",
        "pytest",
        "IPython",
        "cv2",
        "pyarrow",
        "pyarrow.compute",
        "pyarrow.lib",
        "pandas.tests",
        "numpy.tests",
        "openpyxl.tests",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InclusaoCADIN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=logo_ico if os.path.exists(logo_ico) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="InclusaoCADIN_Portavel",
)
