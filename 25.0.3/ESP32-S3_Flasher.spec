# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

# esptool의 모든 데이터 파일 수집
esptool_datas = collect_data_files('esptool')

a = Analysis(
    ['flasher_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
    ('bootloader.bin', '.'),
    ('partitions.bin', '.'),
    ('firmware.bin', '.')
] + esptool_datas,

    hiddenimports=['esptool', 'serial', 'serial.tools', 'serial.tools.list_ports'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ESP32-S3_Flasher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='NONE',
)