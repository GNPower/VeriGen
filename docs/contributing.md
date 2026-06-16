# Contributing

Thank you for your interest in contributing to VeriGen! This guide will help you get started.

## Development Setup

1. **Fork and clone the repository:**

    ```bash
    git clone https://github.com/YOUR_USERNAME/VeriGen.git
    cd VeriGen
    ```

2. **Create a virtual environment:**

    ```bash
    python -m venv env
    source env/bin/activate  # On Windows: env\Scripts\activate
    ```

3. **Install development dependencies:**

    ```bash
    pip install -r requirements.txt
    pip install -r requirements_dev.txt
    pip install -e .
    ```

4. **Verify the setup:**

    ```bash
    pytest tests/
    ```

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **Pylint** for linting

Before submitting a PR, run:

```bash
# Format code
black verigen/
isort verigen/

# Check linting
pylint verigen/
```

## Running Tests

Run the full test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=verigen --cov-report=html
```

View coverage report in `htmlcov/index.html`.

## Project Structure

```
verigen/
├── cli.py              # Command-line interface
├── core/
│   ├── models.py       # Data models (Schema, Table, Row, etc.)
│   ├── schema.py       # Schema and data parsing
│   ├── validator.py    # Validation logic
│   └── engine.py       # Jinja2 template engine
├── gui/
│   ├── app.py          # Main PySide6 application
│   ├── table_editor.py # Hierarchical table editor
│   └── widgets.py      # Custom widgets
└── utils/
    └── paths.py        # Path utilities
```

## Making Changes

### Adding a New Filter

1. Add the filter function in `verigen/core/engine.py`:

    ```python
    def my_filter(value, arg):
        """Description of what the filter does."""
        return processed_value
    ```

2. Register it in `TemplateEngine.__init__`:

    ```python
    self.env.filters['my_filter'] = my_filter
    ```

3. Add tests in `tests/test_engine.py`:

    ```python
    def test_my_filter(self, engine):
        result = engine.render_string(
            "{{ value | my_filter(arg) }}",
            tmpdir,
            {"value": input_value}
        )
        assert result == expected_output
    ```

4. Document it in `docs/api/engine.md`.

### Adding a New Attribute Type

1. Update `AttributeDefinition.validate_value()` in `models.py`
2. Update `SchemaParser._parse_attribute_definition()` in `schema.py`
3. Add tests in `tests/test_models.py` and `tests/test_schema.py`

## Submitting a Pull Request

1. Create a feature branch:

    ```bash
    git checkout -b feature/my-feature
    ```

2. Make your changes and commit:

    ```bash
    git add .
    git commit -m "Add feature X

    - Description of changes
    - Any important notes

    Co-Authored-By: Your Name <your@email.com>"
    ```

3. Push to your fork:

    ```bash
    git push origin feature/my-feature
    ```

4. Open a Pull Request against the `dev` branch.

### PR Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] Code is formatted (`black`, `isort`)
- [ ] Linting passes (`pylint`)
- [ ] Documentation updated if needed
- [ ] Commit messages are clear

## Reporting Issues

When reporting bugs, please include:

1. VeriGen version (`verigen --version`)
2. Python version (`python --version`)
3. Operating system
4. Steps to reproduce
5. Expected vs actual behavior
6. Relevant error messages or logs

## Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Describe the use case
3. Propose a solution if you have one
4. Be open to discussion

## Questions?

- Open a [Discussion](https://github.com/GNPower/VeriGen/discussions)
- Check the [FAQ](faq.md)

Thank you for contributing!
