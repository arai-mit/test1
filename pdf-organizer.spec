# -*- mode: python ; coding: utf-8 -*-
a = Analysis(["run_app.py"], pathex=[], binaries=[], datas=[], hiddenimports=[], hookspath=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="経理PDF整理ツール", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=True, console=False)
