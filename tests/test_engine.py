#!/usr/bin/env python
"""Tests for verigen.core.engine module."""

import pytest
import tempfile
import os

from verigen.core.engine import TemplateEngine, TemplateError, generate_templates
from verigen.core.models import Row, Table, TableDefinition, AttributeDefinition


class TestTemplateEngine:
    """Tests for TemplateEngine class."""

    def test_create_engine(self):
        """Test creating a template engine."""
        engine = TemplateEngine()
        assert engine is not None

    def test_render_simple_string(self):
        """Test rendering a simple template string."""
        engine = TemplateEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "Hello, {{ name }}!",
                tmpdir,
                {"name": "World"}
            )
            assert result == "Hello, World!"

    def test_render_template_file(self):
        """Test rendering a template file."""
        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a template file
            template_path = os.path.join(tmpdir, "test.txt.j2")
            with open(template_path, 'w') as f:
                f.write("Module: {{ module_name }}\nWidth: {{ width }}")

            result = engine.render_template(
                "test.txt.j2",
                tmpdir,
                {"module_name": "test_mod", "width": 32}
            )

            assert "Module: test_mod" in result
            assert "Width: 32" in result

    def test_render_undefined_variable_raises_error(self):
        """Test that undefined variables raise TemplateError."""
        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(TemplateError):
                engine.render_string(
                    "{{ undefined_var }}",
                    tmpdir,
                    {}
                )

    def test_template_not_found_raises_error(self):
        """Test that missing template raises TemplateError."""
        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(TemplateError):
                engine.render_template(
                    "nonexistent.j2",
                    tmpdir,
                    {}
                )


class TestBuiltinFilters:
    """Tests for built-in Jinja2 filters."""

    @pytest.fixture
    def engine(self):
        """Create a template engine for testing."""
        return TemplateEngine()

    def test_hex_format_filter(self, engine):
        """Test hex_format filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 255 | hex_format(4) }}",
                tmpdir,
                {}
            )
            assert result == "0x00FF"

    def test_verilog_hex_filter(self, engine):
        """Test verilog_hex filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 255 | verilog_hex(8) }}",
                tmpdir,
                {}
            )
            assert result == "8'hFF"

    def test_bit_range_filter_with_dict(self, engine):
        """Test bit_range filter with dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ field | bit_range }}",
                tmpdir,
                {"field": {"bit_offset": 4, "bit_width": 8}}
            )
            assert result == "[11:4]"

    def test_bit_range_filter_single_bit(self, engine):
        """Test bit_range filter for single bit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ field | bit_range }}",
                tmpdir,
                {"field": {"bit_offset": 7, "bit_width": 1}}
            )
            assert result == "[7]"

    def test_mask_filter(self, engine):
        """Test mask filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ field | mask }}",
                tmpdir,
                {"field": {"bit_offset": 0, "bit_width": 4}}
            )
            assert result == "15"  # 0xF

    def test_snake_case_filter(self, engine):
        """Test snake_case filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 'CamelCaseTest' | snake_case }}",
                tmpdir,
                {}
            )
            assert result == "camel_case_test"

    def test_upper_snake_case_filter(self, engine):
        """Test upper_snake_case filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 'CamelCase' | upper_snake_case }}",
                tmpdir,
                {}
            )
            assert result == "CAMEL_CASE"

    def test_camel_case_filter(self, engine):
        """Test camel_case filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 'some_variable_name' | camel_case }}",
                tmpdir,
                {}
            )
            assert result == "someVariableName"

    def test_pascal_case_filter(self, engine):
        """Test pascal_case filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 'some_variable_name' | pascal_case }}",
                tmpdir,
                {}
            )
            assert result == "SomeVariableName"

    def test_log2_filter(self, engine):
        """Test log2 filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 256 | log2 }}",
                tmpdir,
                {}
            )
            assert result == "8"

    def test_clog2_filter(self, engine):
        """Test clog2 filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Exact power of 2
            result1 = engine.render_string("{{ 256 | clog2 }}", tmpdir, {})
            assert result1 == "8"

            # Not exact power of 2
            result2 = engine.render_string("{{ 257 | clog2 }}", tmpdir, {})
            assert result2 == "9"

    def test_pow2_filter(self, engine):
        """Test pow2 filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 8 | pow2 }}",
                tmpdir,
                {}
            )
            assert result == "256"

    def test_align_filter(self, engine):
        """Test align filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 100 | align(64) }}",
                tmpdir,
                {}
            )
            assert result == "128"

    def test_format_bin_filter(self, engine):
        """Test format_bin filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 15 | format_bin(8) }}",
                tmpdir,
                {}
            )
            assert result == "00001111"

    def test_count_ones_filter(self, engine):
        """Test count_ones filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 240 | count_ones }}",
                tmpdir,
                {}
            )
            assert result == "4"  # 0xF0 = 11110000

    def test_range_str_filter(self, engine):
        """Test range_str filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ 31 | range_str(0) }}",
                tmpdir,
                {}
            )
            assert result == "[31:0]"

    def test_plural_filter(self, engine):
        """Test plural filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = engine.render_string(
                "{{ 1 | plural('register') }}",
                tmpdir,
                {}
            )
            assert result1 == "register"

            result2 = engine.render_string(
                "{{ 5 | plural('register') }}",
                tmpdir,
                {}
            )
            assert result2 == "registers"


class TestRowAccess:
    """Tests for Row object access in templates."""

    def test_row_dot_notation(self):
        """Test accessing Row attributes with dot notation."""
        engine = TemplateEngine()
        row = Row(attributes={"name": "TEST", "value": 42})

        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{{ row.name }}: {{ row.value }}",
                tmpdir,
                {"row": row}
            )
            assert result == "TEST: 42"

    def test_row_children_iteration(self):
        """Test iterating over Row children."""
        engine = TemplateEngine()
        parent = Row(
            attributes={"name": "PARENT"},
            children=[
                Row(attributes={"name": "CHILD1"}),
                Row(attributes={"name": "CHILD2"}),
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.render_string(
                "{% for child in row.children %}{{ child.name }} {% endfor %}",
                tmpdir,
                {"row": parent}
            )
            assert "CHILD1" in result
            assert "CHILD2" in result


class TestGenerateTemplates:
    """Tests for generate_templates function."""

    def test_generate_single_template(self):
        """Test generating a single template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template
            os.makedirs(os.path.join(tmpdir, "templates"))
            template_path = os.path.join(tmpdir, "templates", "output.txt.j2")
            with open(template_path, 'w') as f:
                f.write("Hello, {{ name }}!")

            # Create output directory
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir)

            project_data = {
                "templates": [
                    {
                        "source": "templates/output.txt.j2",
                        "destination": "output.txt"
                    }
                ]
            }

            generated = generate_templates(
                project_data=project_data,
                project_base_dir=tmpdir,
                output_dir=output_dir,
                user_params={"name": "World"}
            )

            assert len(generated) == 1
            assert os.path.exists(generated[0])

            with open(generated[0], 'r') as f:
                content = f.read()
            assert content == "Hello, World!"

    def test_generate_with_dynamic_destination(self):
        """Test generating with Jinja2 variables in destination path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template
            os.makedirs(os.path.join(tmpdir, "templates"))
            template_path = os.path.join(tmpdir, "templates", "module.sv.j2")
            with open(template_path, 'w') as f:
                f.write("module {{ module_name }};")

            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir)

            project_data = {
                "templates": [
                    {
                        "source": "templates/module.sv.j2",
                        "destination": "{{ module_name }}.sv"
                    }
                ]
            }

            generated = generate_templates(
                project_data=project_data,
                project_base_dir=tmpdir,
                output_dir=output_dir,
                user_params={"module_name": "my_design"}
            )

            assert len(generated) == 1
            assert "my_design.sv" in generated[0]

    def test_generate_with_table_data(self):
        """Test generating with table data converted to Row objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template
            os.makedirs(os.path.join(tmpdir, "templates"))
            template_path = os.path.join(tmpdir, "templates", "list.txt.j2")
            with open(template_path, 'w') as f:
                f.write("{% for item in items %}{{ item.name }}\n{% endfor %}")

            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir)

            project_data = {
                "templates": [
                    {
                        "source": "templates/list.txt.j2",
                        "destination": "list.txt"
                    }
                ]
            }

            # Pass table data as list of dicts (like GUI would)
            user_params = {
                "items": [
                    {"name": "Item1"},
                    {"name": "Item2"},
                    {"name": "Item3"},
                ]
            }

            generated = generate_templates(
                project_data=project_data,
                project_base_dir=tmpdir,
                output_dir=output_dir,
                user_params=user_params
            )

            with open(generated[0], 'r') as f:
                content = f.read()

            assert "Item1" in content
            assert "Item2" in content
            assert "Item3" in content

    def test_generate_with_nested_data(self):
        """Test generating with nested table data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template
            os.makedirs(os.path.join(tmpdir, "templates"))
            template_path = os.path.join(tmpdir, "templates", "nested.txt.j2")
            with open(template_path, 'w') as f:
                f.write("""{% for reg in registers %}
{{ reg.name }}:
{% for field in reg.children %}  - {{ field.name }}
{% endfor %}
{% endfor %}""")

            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir)

            project_data = {
                "templates": [
                    {
                        "source": "templates/nested.txt.j2",
                        "destination": "nested.txt"
                    }
                ]
            }

            # Nested table data
            user_params = {
                "registers": [
                    {
                        "name": "CTRL",
                        "children": [
                            {"name": "enable"},
                            {"name": "mode"},
                        ]
                    },
                    {
                        "name": "STATUS",
                        "children": [
                            {"name": "ready"},
                        ]
                    },
                ]
            }

            generated = generate_templates(
                project_data=project_data,
                project_base_dir=tmpdir,
                output_dir=output_dir,
                user_params=user_params
            )

            with open(generated[0], 'r') as f:
                content = f.read()

            assert "CTRL" in content
            assert "enable" in content
            assert "mode" in content
            assert "STATUS" in content
            assert "ready" in content
