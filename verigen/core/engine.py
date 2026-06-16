"""
VeriGen Template Engine

Enhanced Jinja2 template engine with helper filters and functions
for code generation.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import jinja2

from .models import Schema, Table, Row


class TemplateEngine:
    """
    Jinja2-based template engine for code generation.

    Provides:
    - Template loading and rendering
    - Built-in helper filters (optional, users don't have to use them)
    - Proper error handling and reporting
    """

    def __init__(self, search_paths: Optional[List[str]] = None):
        """
        Initialize the template engine.

        Args:
            search_paths: List of directories to search for templates.
        """
        self.search_paths = search_paths or ['.']
        self._env: Optional[jinja2.Environment] = None
        self._custom_filters: Dict[str, Callable] = {}
        self._custom_globals: Dict[str, Any] = {}

        # Register built-in filters
        self._register_builtin_filters()

        # Register built-in globals
        self._register_builtin_globals()

    def _create_environment(self, base_dir: str) -> jinja2.Environment:
        """Create a Jinja2 environment with the given base directory."""
        paths = [base_dir] + self.search_paths
        loader = jinja2.FileSystemLoader(searchpath=paths)

        env = jinja2.Environment(
            loader=loader,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,  # Raise errors for undefined vars
        )

        # Add custom filters
        env.filters.update(self._custom_filters)

        # Add custom globals
        env.globals.update(self._custom_globals)

        return env

    def _register_builtin_filters(self):
        """Register built-in helper filters."""
        # These are optional helpers - users can use them if their schema
        # defines attributes with these names, but they're not required.

        def bit_range(row_or_dict) -> str:
            """
            Generate Verilog bit range notation.

            Usage: {{ field | bit_range }} -> [7:0]

            Requires attributes: bit_offset, bit_width
            """
            if isinstance(row_or_dict, Row):
                offset = row_or_dict.get('bit_offset', 0)
                width = row_or_dict.get('bit_width', 1)
            elif isinstance(row_or_dict, dict):
                offset = row_or_dict.get('bit_offset', 0)
                width = row_or_dict.get('bit_width', 1)
            else:
                return "[0]"

            if width == 1:
                return f"[{offset}]"
            return f"[{offset + width - 1}:{offset}]"

        def hex_format(value: int, width: int = 8) -> str:
            """
            Format integer as hex with specified width.

            Usage: {{ value | hex_format(8) }} -> 0x0000FFFF
            """
            return f"0x{value:0{width}X}"

        def verilog_hex(value: int, bit_width: int = 32) -> str:
            """
            Format integer as Verilog hex literal.

            Usage: {{ value | verilog_hex(32) }} -> 32'h0000FFFF
            """
            hex_chars = (bit_width + 3) // 4  # Round up
            return f"{bit_width}'h{value:0{hex_chars}X}"

        def mask(row_or_dict) -> int:
            """
            Calculate bitmask for a field.

            Usage: {{ field | mask }} -> integer mask value

            Requires attributes: bit_offset, bit_width
            """
            if isinstance(row_or_dict, Row):
                offset = row_or_dict.get('bit_offset', 0)
                width = row_or_dict.get('bit_width', 1)
            elif isinstance(row_or_dict, dict):
                offset = row_or_dict.get('bit_offset', 0)
                width = row_or_dict.get('bit_width', 1)
            else:
                return 1

            return ((1 << width) - 1) << offset

        def snake_case(s: str) -> str:
            """Convert string to snake_case."""
            import re
            # Insert underscore before uppercase letters and lowercase
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        def upper_snake_case(s: str) -> str:
            """Convert string to UPPER_SNAKE_CASE."""
            return snake_case(s).upper()

        def camel_case(s: str) -> str:
            """Convert string to camelCase."""
            # First convert to snake case, then to camel
            snake = snake_case(s)
            parts = snake.split('_')
            return parts[0] + ''.join(p.title() for p in parts[1:])

        def pascal_case(s: str) -> str:
            """Convert string to PascalCase."""
            snake = snake_case(s)
            return ''.join(p.title() for p in snake.split('_'))

        def log2(value: int) -> int:
            """
            Calculate floor of log base 2.

            Usage: {{ 256 | log2 }} -> 8
            """
            if value <= 0:
                return 0
            import math
            return int(math.log2(value))

        def clog2(value: int) -> int:
            """
            Calculate ceiling of log base 2 (minimum bits needed).

            Usage: {{ 256 | clog2 }} -> 8
                   {{ 257 | clog2 }} -> 9
            """
            if value <= 1:
                return 1
            import math
            return int(math.ceil(math.log2(value)))

        def pow2(exponent: int) -> int:
            """
            Calculate 2 raised to power (avoids << in templates).

            Usage: {{ 8 | pow2 }} -> 256
            """
            return 2 ** exponent

        def align(value: int, alignment: int) -> int:
            """
            Align value up to the nearest multiple of alignment.

            Usage: {{ 100 | align(64) }} -> 128
            """
            if alignment <= 0:
                return value
            return ((value + alignment - 1) // alignment) * alignment

        def format_bin(value: int, width: int = 8) -> str:
            """
            Format integer as binary with specified width.

            Usage: {{ 15 | format_bin(8) }} -> 00001111
            """
            return f"{value:0{width}b}"

        def count_ones(value: int) -> int:
            """
            Count number of 1 bits in value.

            Usage: {{ 0xF0 | count_ones }} -> 4
            """
            return bin(value).count('1')

        def repeat_char(char: str, count: int) -> str:
            """
            Repeat a character or string.

            Usage: {{ '-' | repeat_char(10) }} -> ----------
            """
            return char * count

        def range_str(high: int, low: int = 0) -> str:
            """
            Create SystemVerilog range string.

            Usage: {{ 31 | range_str(0) }} -> [31:0]
                   {{ 7 | range_str }} -> [7:0]
            """
            if high == low:
                return f"[{high}]"
            return f"[{high}:{low}]"

        def plural(count: int, singular: str, plural_form: str = None) -> str:
            """
            Return singular or plural form based on count.

            Usage: {{ 1 | plural('register') }} -> register
                   {{ 5 | plural('register') }} -> registers
            """
            if plural_form is None:
                plural_form = singular + 's'
            return singular if count == 1 else plural_form

        # Register all built-in filters
        self._custom_filters = {
            # Bit/hex formatting
            'bit_range': bit_range,
            'hex_format': hex_format,
            'verilog_hex': verilog_hex,
            'format_bin': format_bin,
            'range_str': range_str,

            # Bitwise operations
            'mask': mask,
            'log2': log2,
            'clog2': clog2,
            'pow2': pow2,
            'count_ones': count_ones,
            'align': align,

            # String case conversions
            'snake_case': snake_case,
            'upper_snake_case': upper_snake_case,
            'camel_case': camel_case,
            'pascal_case': pascal_case,

            # Misc utilities
            'repeat_char': repeat_char,
            'plural': plural,
        }

    def _register_builtin_globals(self):
        """Register built-in global variables and functions."""
        # namespace is a Jinja2 utility class for mutable state in loops
        # Usage: {% set ns = namespace(counter=0) %}
        #        {% set ns.counter = ns.counter + 1 %}
        self._custom_globals = {
            'namespace': jinja2.utils.Namespace,
        }

    def add_filter(self, name: str, func: Callable):
        """Add a custom filter function."""
        self._custom_filters[name] = func
        if self._env:
            self._env.filters[name] = func

    def add_global(self, name: str, value: Any):
        """Add a global variable available in all templates."""
        self._custom_globals[name] = value
        if self._env:
            self._env.globals[name] = value

    def render_template(
        self,
        template_path: str,
        base_dir: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a template file with the given context.

        Args:
            template_path: Path to the template file (relative to base_dir).
            base_dir: Base directory for template resolution.
            context: Dictionary of variables to pass to the template.

        Returns:
            Rendered template content.
        """
        env = self._create_environment(base_dir)

        try:
            template = env.get_template(template_path)
            return template.render(context)
        except jinja2.TemplateNotFound as e:
            raise TemplateError(f"Template not found: {e.name}")
        except jinja2.TemplateSyntaxError as e:
            raise TemplateError(f"Template syntax error in {e.name}:{e.lineno}: {e.message}")
        except jinja2.UndefinedError as e:
            raise TemplateError(f"Undefined variable in template: {e.message}")

    def render_string(
        self,
        template_str: str,
        base_dir: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a template string with the given context.

        Useful for rendering destination paths that may contain Jinja2 variables.

        Args:
            template_str: Template string to render.
            base_dir: Base directory for includes (if any).
            context: Dictionary of variables.

        Returns:
            Rendered string.
        """
        env = self._create_environment(base_dir)

        try:
            template = env.from_string(template_str)
            return template.render(context)
        except jinja2.TemplateSyntaxError as e:
            raise TemplateError(f"Template syntax error: {e.message}")
        except jinja2.UndefinedError as e:
            raise TemplateError(f"Undefined variable: {e.message}")


class TemplateError(Exception):
    """Raised when template rendering fails."""
    pass


def _convert_to_rows(data: Any) -> Any:
    """
    Recursively convert dictionaries to Row objects for template access.

    This allows templates to use dot notation (reg.name) instead of
    dictionary access (reg['name']).
    """
    if isinstance(data, list):
        return [_convert_to_rows(item) for item in data]
    elif isinstance(data, dict):
        # Extract children separately
        children_data = data.get('children', [])
        children = [_convert_to_rows(child) for child in children_data]

        # Create attributes dict without 'children' key
        attributes = {k: v for k, v in data.items() if k != 'children'}

        return Row(attributes=attributes, children=children)
    else:
        return data


def generate_templates(
    project_data: Dict[str, Any],
    project_base_dir: str,
    output_dir: str,
    user_params: Dict[str, Any]
) -> List[str]:
    """
    Generate all templates defined in a project.

    This is the main entry point for template generation, compatible
    with the original VeriGen API.

    Args:
        project_data: Project manifest data containing 'templates' list.
        project_base_dir: Base directory of the project.
        output_dir: Output directory for generated files.
        user_params: User parameters and table data.

    Returns:
        List of generated file paths.
    """
    engine = TemplateEngine()
    generated_files = []

    # Prepare context - flatten tables into the context
    context = dict(user_params)

    # Convert any Table objects to lists of Row objects for template access
    for key, value in list(context.items()):
        if isinstance(value, Table):
            context[key] = value.rows
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Convert list of dictionaries to list of Row objects
            context[key] = _convert_to_rows(value)

    templates = project_data.get('templates', [])

    for template_info in templates:
        source_path = template_info.get('source')
        dest_template = template_info.get('destination')

        if not source_path or not dest_template:
            continue

        # Render the destination path (may contain Jinja2 variables)
        try:
            rendered_dest = engine.render_string(
                dest_template,
                project_base_dir,
                context
            )
        except TemplateError as e:
            raise TemplateError(f"Error in destination path '{dest_template}': {e}")

        # Full output path
        full_dest_path = os.path.join(output_dir, rendered_dest)

        # Create output directory if needed
        os.makedirs(os.path.dirname(full_dest_path), exist_ok=True)

        # Render the template
        try:
            output_code = engine.render_template(
                source_path,
                project_base_dir,
                context
            )
        except TemplateError as e:
            raise TemplateError(f"Error rendering '{source_path}': {e}")

        # Write output file
        with open(full_dest_path, 'w', encoding='utf-8') as f:
            f.write(output_code)

        generated_files.append(full_dest_path)

    return generated_files
