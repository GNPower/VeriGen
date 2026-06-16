# Changelog

All notable changes to VeriGen are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-26

### Added

- **Schema-driven architecture**: Define your own data structures via YAML schemas
- **Hierarchical table support**: Tables can contain nested child tables
- **PySide6 GUI**: Modern Qt-based interface replacing ttkbootstrap
  - Master-detail table editor for hierarchical data
  - Real-time validation feedback
  - Tooltips from schema descriptions
  - Auto-refresh summary panel
- **Enhanced validation system**:
  - Type validation (string, integer, boolean, choice)
  - Range validation (min/max values)
  - Pattern validation (regex)
  - Uniqueness constraints
  - Custom validation rules (Python expressions)
- **New template filters**:
  - `hex_format(digits)` - Hex with prefix
  - `verilog_hex(width)` - Verilog hex literal
  - `bit_range` - Verilog bit range notation
  - `mask` - Calculate bit mask
  - `log2`, `clog2`, `pow2` - Math operations
  - `snake_case`, `camel_case`, `pascal_case` - String conversions
  - `align(boundary)` - Value alignment
  - `count_ones` - Population count
  - `plural(word)` - Pluralization
- **Programmatic API**: Full Python API for integration
- **Comprehensive test suite**: 91 tests covering core functionality

### Changed

- **Project structure**: Reorganized into `core/`, `gui/`, `utils/` modules
- **Schema format**: New v2.0 format (v1.0 still supported for compatibility)
- **Template context**: Table data now uses `Row` objects with dot-notation access
- **CLI interface**: Updated commands (`generate`, `gui`, `validate`)

### Removed

- `common.py` module (was empty placeholder)
- Direct register/field concepts (now user-defined via schemas)

### Migration from 1.x

If you have existing v1.x projects:

1. Your UI spec files (`pages` format) still work
2. Update templates to use `.children` instead of hardcoded field access
3. Consider migrating to v2.0 schema format for new features

---

## [1.0.0] - 2024-XX-XX

### Added

- Initial release
- Jinja2 template engine integration
- ttkbootstrap GUI
- Basic register file generation
- AXI-Lite example project

---

## Roadmap

### Planned for 2.1.0

- [ ] Template inheritance support in project manifests
- [ ] Schema import/extend functionality
- [ ] VSCode extension for schema validation
- [ ] Additional example projects (FSM, BRAM controller)

### Planned for 2.2.0

- [ ] Web-based GUI option
- [ ] Plugin system for custom validators
- [ ] SystemRDL import support
