# Installation

## Requirements

- Python 3.8 or higher
- pip package manager

## Install from PyPI

The recommended way to install VeriGen is via pip:

```bash
pip install verigen
```

This installs VeriGen with all dependencies including the PySide6 GUI.

## Install from Source

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/GNPower/VeriGen.git
cd VeriGen

# Create a virtual environment (recommended)
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install in development mode
pip install -e .
```

## Verify Installation

After installation, verify VeriGen is working:

```bash
# Check version
verigen --version

# Show help
verigen --help
```

You should see output similar to:

```
VeriGen 2.0.0

Usage: verigen [OPTIONS] COMMAND [ARGS]...

Commands:
  generate  Generate files from a VeriGen project
  gui       Launch the VeriGen GUI
  validate  Validate a schema or data file
```

## Dependencies

VeriGen automatically installs these dependencies:

| Package | Purpose |
|---------|---------|
| `Jinja2` | Template engine |
| `PyYAML` | YAML file parsing |
| `PySide6` | GUI framework |
| `Pillow` | Image handling |

## Optional: Development Dependencies

For contributing or running tests:

```bash
pip install -r requirements_dev.txt
```

This includes:

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `pylint` - Linting

## Troubleshooting

### PySide6 Installation Issues

If you encounter issues with PySide6 on Linux:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libxcb-xinerama0

# Or install without GUI support
pip install verigen --no-deps
pip install jinja2 pyyaml
```

### Python Version

VeriGen requires Python 3.8+. Check your version:

```bash
python --version
```

If you have multiple Python versions, use:

```bash
python3 -m pip install verigen
```

## Next Steps

Once installed, proceed to the [Quick Start Guide](usage.md) to create your first project.
