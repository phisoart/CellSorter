# -*- mode: python ; coding: utf-8 -*-

"""
CellSorter PyInstaller Spec File
- Creates a single executable file without console window
- Includes all necessary dependencies and resources
"""

import sys
from pathlib import Path

block_cipher = None

# Main application entry point
a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Include UI definitions
        ('ui_definitions', 'ui_definitions'),
        # Include source code as data for dynamic imports
        ('src', 'src'),
    ],
    hiddenimports=[
        # PySide6 modules
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'PySide6.QtOpenGL',
        
        # Scientific computing
        'numpy',
        'pandas',
        'scipy',
        'matplotlib',
        'matplotlib.backends',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.qt_compat',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'opencv-python',
        'cv2',
        
        # Qt Material
        'qt_material',
        
        # Application modules
        'src.main',
        'src.pages.main_window',
        'src.services.theme_manager',
        'src.models',
        'src.components',
        'src.headless',
        'src.utils',
        'src.config',
        
        # PIL/Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageFilter',
        'PIL.ImageDraw',
        
        # Additional dependencies
        'yaml',
        'packaging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude development/testing modules
        'pytest',
        'test',
        'tests',
        'unittest',
        'doctest',
        
        # Exclude unnecessary GUI backends
        'tkinter',
        'PyQt5',
        'PyQt4',
        
        # Exclude development tools
        'IPython',
        'jupyter',
        'notebook',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CellSorter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 터미널 창 표시
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows specific - 버전 정보는 선택사항이므로 제거
    # version='version_info.txt' if sys.platform == 'win32' else None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
) 