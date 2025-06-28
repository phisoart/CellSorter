# CellSorter

🧬 **Advanced Cell Sorting and Tissue Extraction Software for CosmoSort Hardware Integration**

CellSorter is a sophisticated GUI-based application designed to work in conjunction with the CosmoSort research instrument for precision cell sorting and tissue extraction from pathology slides. The software analyzes microscopy images and CellProfiler-generated data to enable researchers to select specific cell populations and generate extraction protocols for automated tissue harvesting.

## 📋 Overview

CellSorter provides researchers with an intuitive, powerful tool that bridges the gap between cellular image analysis and physical tissue extraction, enabling precise, reproducible cell sorting workflows for pathology research and diagnostics.

### 🎯 Key Capabilities

- **Multi-format Image Support**: Load TIFF, JPG, JPEG, and PNG microscopy images
- **CellProfiler Integration**: Parse and analyze CSV data from CellProfiler exports
- **Interactive Data Visualization**: Generate scatter plots for cell feature analysis
- **Precision Cell Selection**: Rectangle selection tools with real-time feedback
- **Coordinate Calibration**: Two-point calibration system for pixel-to-stage transformation
- **Protocol Generation**: Export .cxprotocol files compatible with CosmoSort hardware
- **96-Well Plate Management**: Automatic assignment and visualization
- **Modern UI Design**: shadcn/ui inspired interface with qt-material theming

## 🚀 Features

### 🔬 Scientific Analysis
- **Cell Population Identification**: Advanced scatter plot visualization for marker-based selection
- **Bounding Box Processing**: Automatic extraction of cell coordinates from CellProfiler data
- **Square Crop Calculation**: Optimized crop regions for consistent extraction
- **Coordinate Transformation**: High-precision pixel-to-stage coordinate mapping
- **Multi-Selection Management**: Color-coded selections with customizable labels

### 🎨 Modern Interface
- **Responsive Design**: Adaptive layout supporting multiple screen sizes
- **Accessibility First**: WCAG 2.1 AA compliance with keyboard navigation
- **Theme Integration**: Seamless switching between light/dark themes and qt-material styles
- **Real-time Feedback**: Progressive loading and immediate visual confirmation
- **Error Handling**: Graceful degradation with informative user messages

### 🔧 Research Workflow
- **Quality Control**: Built-in validation and accuracy metrics
- **Direct Export**: .cxprotocol files for CosmoSort hardware integration

## 🛠️ Technology Stack

### Core Framework
- **PySide6** (≥6.4.0) - Modern Qt-based GUI framework
- **Python** 3.11+ - Primary development language

### Image Processing & Analysis
- **OpenCV** (≥4.8.0) - Computer vision and image processing
- **NumPy** (≥1.24.0) - Numerical computing and array operations
- **Pillow** (≥10.0.0) - Image file format support
- **SciPy** (≥1.11.0) - Scientific computing and transformations

### Data Analysis & Visualization
- **Pandas** (≥2.0.0) - Data manipulation and CSV processing
- **Matplotlib** (≥3.7.0) - Interactive plotting and visualization

### User Interface & Theming
- **qt-material** (≥2.14) - Material Design themes for Qt applications
- **shadcn/ui-inspired** styling - Modern, accessible design system

### Development & Testing
- **pytest** (≥7.4.0) - Testing framework
- **pytest-qt** (≥4.2.0) - Qt-specific testing utilities
- **pytest-cov** (≥4.1.0) - Code coverage analysis
- **Black** (≥23.0.0) - Code formatting
- **flake8** (≥6.0.0) - Linting and style checking
- **mypy** (≥1.5.0) - Static type checking

### Build & Deployment
- **PyInstaller** (≥5.13.0) - Standalone executable creation
- **Sphinx** (≥7.1.0) - Documentation generation

## 📁 Project Structure

```
├── PRODUCT_REQUIREMENTS.md          # Product requirements specification ('what' and 'why')
├── README.md                        # Project overview, execution methods, installation, etc.
├── ARCHITECTURE.md                 # Overall technical architecture and tech stack description
├── CODING_STYLE_GUIDE.md           # Naming conventions, directory structure, documentation rules, etc.
├── TESTING_STRATEGY.md             # Unit/integration test plans, tools, coverage criteria
├── .cursorignore                   # Cursor IDE ignore file settings
├── .gitignore                      # Git version control ignore file settings
│
├── requirements.txt                # Production(runtime) Python library specifications
├── requirements-dev.txt            # Development and testing dependency specifications
├── requirements-build.txt          # Build/deployment dependency specifications
│
├── /docs/                          # Documentation and design
│   ├── /design/                    # UI/UX design documents
│   │   ├── DESIGN_SPEC.md          # UI flow and interaction definitions
│   │   ├── DESIGN_SYSTEM.md        # Component library and design system
│   │   ├── style.css               # shadcn/ui + qt-material style definitions
│   │   └── assets/                 # Design-related images and mockups
│   │
│   ├── /examples/                  # Sample data and examples
│   │   ├── data_FilterObjects_dapi_CK7n_CK20_CDX2.csv  # CellProfiler CSV example
│   │   └── example.cxprotocol      # CosmoSort protocol example
│   │
│   ├── USER_PERSONAS.md            # User persona definitions
│   ├── USER_SCENARIOS.md           # User scenarios and workflows
│   └── PROJECT_STRUCTURE.md        # Project structure description
│
├── /src/                           # PySide6 application code
│   ├── /components/                # Reusable UI components
│   │   ├── /base/                  # Basic abstract component classes
│   │   ├── /dialogs/               # Modal dialog components
│   │   └── /widgets/               # Custom widget components
│   ├── /pages/                     # Main application screens
│   ├── /models/                    # Data models and business logic
│   ├── /utils/                     # Utility functions and helpers
│   ├── /config/                    # Configuration files and constants
│   ├── /assets/                    # Icons, images, and static files
│   └── main.py                     # Application entry point
│
├── /tests/                         # Unit and integration tests
│   ├── /components/                # UI component tests
│   ├── /pages/                     # Page/view tests
│   ├── /models/                    # Business logic tests
│   └── /utils/                     # Utility function tests
│
└── /.cursor/                       # Cursor IDE settings
    └── /rules/                     # Project-specific AI rule definitions
        ├── base-rules.mdc          # Basic development rules
        └── update-rules.mdc        # Project update rules
```

## ⚙️ Installation

### Prerequisites

- **Python 3.11+**
- **Conda** (recommended for environment management)
- **Git**

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/phisoart/CellSorter.git
   cd CellSorter
   ```

2. **Set up Python Environment**
   ```bash
   conda create --name cellsorter python=3.11
   conda activate cellsorter
   pip install -r requirements.txt
   ```

3. **Launch Application**
   ```bash
   python src/main.py
   ```

### Basic Workflow

1. **Load Your Data**
   - Import microscopy image (File → Open Image)
   - Load CellProfiler CSV data (File → Open CSV)

2. **Visualize and Select**
   - Choose X/Y axes from CSV columns  
   - Use Shift+Drag to select cell populations
   - Assign colors and labels to selections

3. **Calibrate Coordinates**
   - Click two reference points on image
   - Enter corresponding stage coordinates
   - Validate transformation accuracy

4. **Export Protocol**
   - Review selections and well assignments
   - Generate .cxprotocol file for CosmoSort

### Advanced Features

- **Multi-Selection Management**: Create and manage multiple cell populations
- **Real-time Preview**: See selected cells highlighted on original image
- **Quality Control**: Built-in validation for coordinate accuracy
- **Point/Rectangle Selection**: Flexible cell selection methods

## 🧪 Testing

### CRITICAL: All tests run in headless mode by default

CellSorter follows Test-Driven Development (TDD) with **mandatory headless testing**:
- **NEVER shows GUI during testing unless explicitly specified**
- **ALL UI tests work without display server**
- **Comprehensive interaction simulation in terminal mode**

### Running Tests

```bash
# Run all tests (headless by default)
pytest tests/ --headless

# Run with full interactive simulation
pytest tests/ --headless --interactive-sim

# Run with coverage
pytest --cov=src --headless

# Test all UI interactions without display
pytest tests/test_ui_interactions.py --headless --test-all-clicks
pytest tests/test_ui_interactions.py --headless --test-all-drags
pytest tests/test_ui_interactions.py --headless --test-keyboard-nav

# Run specific test categories (all headless)
pytest tests/components/ --headless  # UI component tests (no display)
pytest tests/models/ --headless      # Business logic tests
pytest tests/integration/ --headless --simulate-user  # User workflow tests
```

- **[User Guide](docs/USER_SCENARIOS.md)**: Detailed usage scenarios and workflows
- **[Installation Guide](docs/INSTALLATION.md)**: Complete setup instructions
- **[Technical Documentation](ARCHITECTURE.md)**: System architecture and APIs
- **[Development Guide](CODING_STYLE_GUIDE.md)**: Contributing guidelines

- **Unit Tests**: Individual component and function testing
- **Integration Tests**: End-to-end workflow validation
- **GUI Tests**: User interface interaction testing
- **Regression Tests**: Bug fix verification

- **Issues**: [GitHub Issues](https://github.com/phisoart/CellSorter/issues)
- **Documentation**: [Project Wiki](https://github.com/phisoart/CellSorter/wiki)  
- **Contact**: [phisoart@github.com](mailto:phisoart@github.com)

## 📄 License

CellSorter is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🚀 Development Status

**Current Release**: v1.0 Production Ready

- **Core Features**: ✅ Complete (all essential functionality implemented)
- **Test Coverage**: 94% (84/89 tests passing)
- **Hardware Integration**: ✅ Full CosmoSort compatibility
- **Cross-Platform**: ✅ Windows and macOS support verified
- **Documentation**: ✅ Comprehensive user and technical guides

### Recent Updates
- ✅ Interactive coordinate calibration with visual feedback
- ✅ Advanced export options with session management  
- ✅ 96-well plate visualization and management
- ✅ Batch processing capabilities for high-throughput workflows
- ✅ Real-time cell highlighting and selection validation

### Roadmap
- 🔄 Linux support for cross-platform compatibility

---

🔬 **Advancing pathology research through precision cell sorting technology**

## 🚫 Excluded Features - Design Philosophy

CellSorter maintains a **focused, single-purpose design** and the following features are **permanently excluded**:

### ❌ Session Management (Not Implemented)
- Save/Load Session functionality
- Auto-save and session recovery
- Session persistence features

**Rationale**: Direct workflow approach (Image → Analysis → Export) without intermediate save states.

### ❌ Edit Menu Operations (Not Implemented)  
- Undo/Redo functionality
- Copy/Paste operations
- Edit history management

**Rationale**: Specialized analysis tool focused on direct interaction, not general document editing.

### ❌ Template Management (Not Implemented)
- Template creation and management
- Workflow templates
- Template library system

**Rationale**: External documentation preferred for protocol standardization.

### ❌ Advanced Analysis Features (Not Implemented)
- Batch processing workflows
- Statistical analysis functions  
- Multi-format data export
- Comparative analysis tools

**Rationale**: Focused on cell selection and coordinate generation; complex analysis should use dedicated tools (CellProfiler, R, Python).

## Three Operation Modes

CellSorter supports three distinct operation modes for different use cases:

### 1. GUI Mode (Production Mode)
**Purpose**: Production use by end users  
**Description**: Standard graphical interface for normal operation

```bash
# Run in GUI mode
python run.py --gui-mode

# Or set environment variable
export CELLSORTER_MODE=gui
python run.py
```

### 2. Dev Mode (Debug Mode - Headless Only)
**Purpose**: AI agents and headless development  
**Description**: Terminal-only interface for automated operations and testing

```bash
# Run in dev mode
python run.py --dev-mode

# Or set environment variable
export CELLSORTER_MODE=dev
python run.py

# Use headless commands
python run.py --dev-mode dump-ui output.yaml
python run.py --dev-mode validate-ui ui_definition.yaml
```

### 3. Dual Mode (Debug Mode - Both)
**Purpose**: Real-time debugging and demonstration  
**Description**: Both headless and GUI running simultaneously - perfect for watching AI agents work

```bash
# Run in dual mode
python run.py --dual-mode

# Or set environment variable
export CELLSORTER_MODE=dual
python run.py
```

**Features**: 
- All operations performed by AI agents in the terminal are reflected in the GUI in real-time
- User manipulations in the GUI are immediately synchronized to the headless interface
- Developers can debug while visually confirming AI agent operations

## Installation

### Prerequisites
- Python 3.9 or higher
- Anaconda or Miniconda

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/phisoart/CellSorter.git
   cd CellSorter
   ```

2. **Create conda environment**:
   ```bash
   conda create -n cellsorter python=3.11
   conda activate cellsorter
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Basic Usage

1. **Start the application** (choose your mode):
   ```bash
   # GUI mode for regular use
   python run.py --gui-mode
   
   # Dev mode for headless operation
   python run.py --dev-mode
   
   # Dual mode for development/debugging
   python run.py --dual-mode
   ```

2. **Load an image**:
   - Click "Open Image" or press Ctrl+O
   - Select a microscopy image file

3. **Load cell data**:
   - Click "Open CSV" or press Ctrl+Shift+O
   - Select the corresponding CSV file

4. **Analyze cells**:
   - Use expression filters to identify cell populations
   - Select cells in the scatter plot
   - Export results or save templates

### Dual Mode Development Example

```bash
# Terminal 1: Start in dual mode
python run.py --dual-mode

# Terminal 2: Run headless commands while watching GUI
# The GUI will update in real-time!
python run.py load-ui modified_ui.yaml
cellsorter-cli add-widget --type=QPushButton --name=analyzeButton

# You can see every change immediately in the GUI window
```

## Development

### Project Structure
```
CellSorter/
├── src/
│   ├── components/      # Reusable UI components
│   ├── headless/       # Headless mode infrastructure
│   ├── models/         # Core business logic
│   ├── pages/          # Application views
│   └── services/       # Application services
├── tests/              # Test suites
├── docs/               # Documentation
└── ui_definitions/     # UI configuration files
```

### Testing

Run tests in different modes:

```bash
# Test in dev mode (headless only)
CELLSORTER_MODE=dev pytest tests/

# Test in GUI mode
CELLSORTER_MODE=gui pytest tests/

# Test in dual mode (see visual feedback)
CELLSORTER_MODE=dual pytest tests/ --watch
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in all three modes
5. Submit a pull request

## Documentation

- [Architecture Guide](docs/HEADLESS_GUI_ARCHITECTURE.md)
- [Development Guide](docs/HEADLESS_DEVELOPMENT_GUIDE.md) 
- [API Reference](docs/API_REFERENCE.md)
- [User Guide](docs/USER_GUIDE.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/phisoart/CellSorter/issues)
- **Documentation**: [Wiki](https://github.com/phisoart/CellSorter/wiki)
- **Contact**: phisoart@gmail.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with PySide6 and modern Python
- Designed for scientific research workflows
- AI-enhanced for improved productivity
