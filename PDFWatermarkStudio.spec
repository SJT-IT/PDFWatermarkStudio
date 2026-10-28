
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Collect CustomTkinter resources and imports
ctk_datas, ctk_binaries, ctk_hidden = collect_all("customtkinter")

# Collect PyMuPDF resources and imports
pdf_datas, pdf_binaries, pdf_hidden = collect_all("pymupdf")

a = Analysis(
    ["pdf_watermark_studio.py"],
    pathex=[],
    binaries=ctk_binaries + pdf_binaries,
    datas=ctk_datas + pdf_datas,
    hiddenimports=ctk_hidden + pdf_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PDFWatermarkStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    onefile=True,
)
