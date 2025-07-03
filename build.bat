@echo off
REM CellSorter Windows Build Script
REM Creates a single executable file using PyInstaller

echo ========================================
echo CellSorter Windows Build Script
echo ========================================

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Conda not found. Please install Anaconda/Miniconda first.
    pause
    exit /b 1
)

REM Activate cellsorter environment
echo Activating cellsorter environment...
call conda activate cellsorter
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate cellsorter environment.
    echo Please run: conda create -n cellsorter python=3.12
    pause
    exit /b 1
)

REM Install build dependencies
echo Installing build dependencies...
pip install -r build_requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install build dependencies.
    pause
    exit /b 1
)

REM Clean previous build
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build executable
echo Building CellSorter executable...
pyinstaller build_exe.spec --clean --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo Error: Build failed.
    pause
    exit /b 1
)

REM Check if build succeeded
if not exist "dist\CellSorter.exe" (
    echo Error: CellSorter.exe not found in dist folder.
    pause
    exit /b 1
)

echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\CellSorter.exe
echo File size: 
for %%A in ("dist\CellSorter.exe") do echo %%~zA bytes

echo.
echo You can now run: dist\CellSorter.exe
echo.
pause 