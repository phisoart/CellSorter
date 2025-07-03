#!/bin/bash
# CellSorter macOS/Linux Build Script
# Creates a single executable file using PyInstaller

echo "========================================"
echo "CellSorter macOS/Linux Build Script"
echo "========================================"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: Conda not found. Please install Anaconda/Miniconda first."
    exit 1
fi

# Activate cellsorter environment
echo "Activating cellsorter environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cellsorter
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate cellsorter environment."
    echo "Please run: conda create -n cellsorter python=3.12"
    exit 1
fi

# Install build dependencies
echo "Installing build dependencies..."
pip install -r build_requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install build dependencies."
    exit 1
fi

# Clean previous build
echo "Cleaning previous build..."
rm -rf build dist

# Build executable
echo "Building CellSorter executable..."
pyinstaller build_exe.spec --clean --noconfirm
if [ $? -ne 0 ]; then
    echo "Error: Build failed."
    exit 1
fi

# Check if build succeeded
if [ ! -f "dist/CellSorter" ]; then
    echo "Error: CellSorter executable not found in dist folder."
    exit 1
fi

echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo
echo "Executable location: dist/CellSorter"
echo "File size: $(du -h dist/CellSorter | cut -f1)"
echo
echo "You can now run: ./dist/CellSorter"
echo 