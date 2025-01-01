# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden_imports = collect_submodules('scipy')
datas = collect_data_files('scipy')

a = Analysis(['main.py'],
             pathex=['Z:\\src'],
             binaries=[],
             datas=[
                ('\\wine\\drive_c\\Python\\Lib\\site-packages\\mne\\report\\js_and_css', 'mne\\report\\js_and_css'),
                ('\\wine\\drive_c\\Python\\Lib\\site-packages\\mne\\icons', 'mne\\icons'),
                ('\\wine\\drive_c\\Python\\Lib\\site-packages\\brainflow\\lib', 'brainflow\\lib'),
                ('\\wine\\drive_c\\Python\\Lib\\site-packages\\mne\\channels\\data', 'mne\\channels\\data'),
                ('\\wine\\drive_c\\Python\\Lib\\site-packages\\mne\\data', 'mne\\data'),
             ] + datas,
             hiddenimports=['process_ssvep', 'connect_port', 'control_gui', 'scipy.spatial.transform._rotation_groups', 'mido.backends.rtmidi'] + hidden_imports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='Icon.ico')
