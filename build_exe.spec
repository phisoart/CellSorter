# -*- mode: python ; coding: utf-8 -*-

"""
CellSorter PyInstaller Spec File
- Creates a single executable file without console window
- Includes all necessary dependencies and resources
"""

import sys
from pathlib import Path

# Get conda site-packages path if available
conda_env_path = Path(sys.executable).parent.parent
site_packages_path = conda_env_path / 'Lib' / 'site-packages'

block_cipher = None

# Main application entry point
a = Analysis(
    ['run_gui_only.py'],
    pathex=['C:\\Users\\royjang\\Desktop\\Code\\CellSorter', 'C:\\Users\\royjang\\Desktop\\Code\\CellSorter\\src'],
    binaries=[],
    datas=[
        # Include UI definitions and assets
        ('ui_definitions', 'ui_definitions'),
        ('src/assets/logo.ico', 'src/assets'),
    ],
    hiddenimports=[
        # Default imports
        'win32ctypes.pywin32',
        'PySide6.QtOpenGL',
        'opencv-python',
        'qt_material',
        'PyYAML',

        # Application modules
        'models.csv_parser',
        'models.image_handler',
        'models.selection_manager',
        'models.coordinate_transformer',
        'models.extractor',
        'components.scientific_widgets',
        'components.skeleton_loader',
        'components.tooltip_wrapper',
        'components.design_system',
        'utils.design_tokens',
        'utils.accessibility',
        'utils.style_converter',
        'utils.update_checker',
        'utils.default_templates',
        'utils.expression_parser',
        'utils.card_colors',
        'utils.exceptions',
        'utils.error_handler',
        'utils.logging_config',
        'config.settings',
        'config.design_tokens',
        'services.theme_manager',
        'pages.main_window',
        'components.dialogs.calibration_dialog',
        'components.dialogs.custom_color_dialog',
        'components.dialogs.export_dialog',
        'components.dialogs.image_export_dialog',
        'components.dialogs.protocol_export_dialog',
        'components.dialogs.well_selection_dialog',
        'components.widgets.expression_filter',
        'components.widgets.minimap',
        'components.widgets.scatter_plot',
        'components.widgets.selection_panel',
        'components.widgets.well_plate',
        'components.base.base_button',
        'components.base.base_card',
        'components.base.base_input',
        'components.base.base_select',
        'components.base.base_textarea',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['headless'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CellSorter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 터미널 창 숨기기
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src\\assets\\logo.ico',
) 