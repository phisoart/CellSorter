# PySide6 Cursor Default Structure

🚀 **A comprehensive project template for PySide6 applications with Cursor AI integration**

This repository provides a well-structured, production-ready template for developing PySide6 desktop applications with enhanced Cursor AI support and best practices.

## 📋 Overview

This template includes:
- **Complete project structure** for PySide6 applications
- **Cursor AI rules and guidelines** for consistent development
- **Coding style guides** and conventions
- **Testing framework** setup
- **Documentation templates** for professional development
- **Cross-platform compatibility** (Windows & macOS)

## 🎯 Purpose

This default structure is designed to:
- **Accelerate PySide6 project setup** with proven patterns
- **Ensure consistency** across development teams
- **Integrate seamlessly with Cursor AI** for enhanced productivity
- **Provide best practices** for Python GUI development
- **Support professional workflows** from development to deployment

## 🏗️ Project Structure

```
├── PRODUCT_REQUIREMENTS.md          # Product requirements specification
├── README.md                        # Project overview and usage guide
├── ARCHITECTURE.md                 # Technical architecture documentation
├── CODING_STYLE_GUIDE.md           # Coding conventions and style guide
├── TESTING_STRATEGY.md             # Testing approach and guidelines
├── CONTRIBUTING.md                 # Development workflow and collaboration guide
├── .cursor/rules/update-rules.mdc   # Cursor AI behavioral guidelines
│
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore patterns
├── .cursorignore                   # Cursor AI ignore patterns
│
├── /docs/                          # Documentation
│   ├── /design/                    # UI/UX design documents
│   │   ├── DESIGN_SPEC.md          # UI flow and interaction definitions
│   │   ├── DESIGN_SYSTEM.md        # UI component specifications
│   │   ├── assets/                 # Design assets and mockups
│   │   └── style.css               # Style definitions
│   │
│   ├── USER_PERSONAS.md            # Target user definitions
│   ├── USER_SCENARIOS.md           # User scenarios and workflows
│   └── RELEASE_PLAN.md             # Release planning and deployment
│
├── /src/                           # PySide6 application source code
│   ├── /components/                # Reusable UI components
│   │   ├── __init__.py
│   │   ├── /base/                  # Base component classes
│   │   ├── /dialogs/               # Custom dialogs
│   │   └── /widgets/               # Custom widgets
│   ├── /pages/                     # Main application pages/windows
│   ├── /models/                    # Data models and business logic
│   ├── /utils/                     # Utility functions and helpers
│   ├── /config/                    # Configuration files
│   ├── /assets/                    # Static assets (icons, images)
│   └── main.py                     # Application entry point
│
└── /tests/                         # Test suite
    ├── /components/                # Component tests
    ├── /pages/                     # Page tests
    ├── /models/                    # Model tests
    └── /utils/                     # Utility tests
```

## 🛠️ Technology Stack

- **Framework**: PySide6 (Qt for Python)
- **Language**: Python 3.8+
- **Testing**: pytest, pytest-qt
- **Code Quality**: Black, flake8, mypy
- **Build**: PyInstaller
- **AI Integration**: Cursor AI with custom rules
- **Environment**: Conda (recommended)

## ⚙️ Quick Start

### 1. Clone this template
```bash
git clone https://github.com/phisoart/pyside6-cursor-default-structure.git
cd pyside6-cursor-default-structure
```

### 2. Set up development environment
```bash
# Create conda environment
conda create --name your-project-name python=3.11
conda activate your-project-name

# Install dependencies
pip install -r requirements.txt
```

### 3. Customize for your project
- Update `PRODUCT_REQUIREMENTS.md` with your project specifications
- Modify `src/main.py` to implement your application logic
- Customize the project structure as needed
- Update documentation files

### 4. Start developing
```bash
# Run the application
python src/main.py

# Run tests
pytest

# Format code
black src/ tests/

# Type checking
mypy src/
```

## 🎨 Features

### 🤖 Cursor AI Integration
- **Smart code completion** with context-aware suggestions
- **Automated documentation** updates based on code changes
- **Consistent coding patterns** enforced through AI rules
- **Intelligent refactoring** assistance

### 📁 Organized Structure
- **Modular architecture** for scalable applications
- **Separation of concerns** with clear component boundaries
- **Reusable components** for efficient development
- **Professional documentation** structure

### 🧪 Testing Ready
- **pytest integration** with Qt testing support
- **Test structure** mirroring source code organization
- **Coverage reporting** setup
- **CI/CD friendly** configuration

### 🔧 Development Tools
- **Code formatting** with Black
- **Linting** with flake8
- **Type checking** with mypy
- **Git hooks** for quality assurance

## 📖 Documentation

This template includes comprehensive documentation:

- **[Coding Style Guide](CODING_STYLE_GUIDE.md)**: Python and PySide6 specific conventions
- **[Testing Strategy](TESTING_STRATEGY.md)**: Testing approach and tools
- **[Architecture](ARCHITECTURE.md)**: Technical architecture overview
- **[Contributing](CONTRIBUTING.md)**: Development workflow guidelines

## 🚀 Deployment

The template supports multiple deployment options:

- **Standalone executable** with PyInstaller
- **Cross-platform builds** for Windows and macOS
- **Automated build scripts** included
- **Distribution ready** packaging

## 🤝 Contributing

This template is designed to be:
- **Community driven** - contributions welcome
- **Best practice focused** - following Python and Qt conventions
- **Production ready** - suitable for professional projects
- **Educational** - well documented for learning

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📋 Template Usage

### For new projects:
1. Use this template as a starting point
2. Customize the structure for your needs
3. Update documentation to match your project
4. Follow the established patterns for consistency

### For existing projects:
1. Gradually adopt the structure patterns
2. Integrate Cursor AI rules
3. Implement the testing framework
4. Update documentation standards

## 🔗 Related Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Qt for Python Examples](https://doc.qt.io/qtforpython/examples/index.html)
- [Cursor AI Documentation](https://cursor.sh/)
- [Python Packaging Guide](https://packaging.python.org/)

## 📄 License

This template is released under the MIT License. See [LICENSE](LICENSE) for details.

## 🏷️ Template Version

Current template version: **1.0.0**

---

⭐ **Star this repository** if you find it helpful for your PySide6 development!

🐛 **Found an issue?** Please report it in the [Issues](https://github.com/phisoart/pyside6-cursor-default-structure/issues) section.

🔄 **Want to contribute?** Check out our [Contributing Guidelines](CONTRIBUTING.md). 