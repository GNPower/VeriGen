"""
VeriGen Command-Line Interface

This module provides the CLI entry point for VeriGen.

Usage:
    verigen generate project.verigen.yaml -c config.yaml -o output/
    verigen validate schema.yaml
    verigen gui project.verigen.yaml
    verigen info project.verigen.yaml
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from .core.schema import SchemaParser, DataParser, SchemaParseError
from .core.validator import Validator
from .core.engine import generate_templates, TemplateError
from .utils.paths import get_project_base_dir, resolve_path


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load and validate a project manifest file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Parsed manifest dictionary.

    Raises:
        SystemExit: If the file cannot be loaded or is invalid.
    """
    try:
        abs_path = os.path.abspath(manifest_path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)

        # Handle v2 format with 'project' key
        if 'verigen_version' in manifest or 'project' in manifest:
            version = manifest.get('verigen_version', '2.0')
            project = manifest.get('project', {})
            return {
                '_version': version,
                '_raw': manifest,
                'name': project.get('name', 'VeriGen Project'),
                'description': project.get('description', ''),
                'definition': manifest.get('ui', manifest.get('schema')),
                'schema': manifest.get('schema'),
                'templates': manifest.get('templates', []),
            }
        else:
            # Simple format - use as-is
            manifest['_version'] = '1.0'
            return manifest

    except FileNotFoundError:
        print(f"Error: Project manifest file not found at '{manifest_path}'")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Could not parse project manifest file:\n{e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid project manifest file:\n{e}")
        sys.exit(1)


def run_generation(
    manifest: Dict[str, Any],
    project_base_dir: str,
    config_path: str,
    output_dir: str
):
    """
    Run template generation.

    Args:
        manifest: Project manifest dictionary.
        project_base_dir: Base directory of the project.
        config_path: Path to user configuration file.
        output_dir: Output directory for generated files.
    """
    print(f"Loading configuration from: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            params = yaml.safe_load(f)

        if not isinstance(params, dict):
            raise ValueError("Configuration file is not a valid key-value structure.")

        # Validate against schema if available
        schema_path = manifest.get('schema')
        if schema_path:
            full_schema_path = os.path.join(project_base_dir, schema_path)
            if os.path.exists(full_schema_path):
                print(f"Validating against schema: {schema_path}")
                parser = SchemaParser()
                schema = parser.parse_file(full_schema_path)
                validator = Validator(schema)
                errors = validator.validate_parameters(params)
                if errors:
                    print("Validation issues:")
                    for error in errors:
                        print(f"  - {error}")

        # Generate templates
        generated = generate_templates(
            project_data=manifest,
            project_base_dir=project_base_dir,
            output_dir=output_dir,
            user_params=params
        )

        print(f"\nGeneration complete. {len(generated)} files saved to '{output_dir}':")
        for path in generated:
            rel_path = os.path.relpath(path, output_dir)
            print(f"  - {rel_path}")

    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{config_path}'")
        sys.exit(1)
    except TemplateError as e:
        print(f"\nTemplate error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during generation: {e}")
        sys.exit(1)


def run_gui(manifest_path: str):
    """
    Run the GUI interface.

    Args:
        manifest_path: Path to the project manifest file.
    """
    try:
        from .gui import run_gui as gui_run
        sys.exit(gui_run(manifest_path))
    except ImportError as e:
        print(f"Error: GUI dependencies not installed. Install PySide6:")
        print(f"  pip install PySide6")
        print(f"\nDetails: {e}")
        sys.exit(1)


def cmd_generate(args):
    """Handle the 'generate' command."""
    manifest = load_manifest(args.project_file)
    project_base_dir = str(get_project_base_dir(args.project_file))

    run_generation(
        manifest=manifest,
        project_base_dir=project_base_dir,
        config_path=args.config,
        output_dir=args.output
    )


def cmd_validate(args):
    """Handle the 'validate' command."""
    print(f"Validating: {args.file}")

    try:
        parser = SchemaParser()
        schema = parser.parse_file(args.file)

        # Validate the schema itself
        validator = Validator(schema)
        result = validator.validate_schema()

        if result.is_valid:
            print("\nSchema is valid!")
            print(f"\nParameters ({len(schema.parameters)}):")
            for name, param in schema.parameters.items():
                default_str = f" = {param.default}" if param.default is not None else ""
                print(f"  - {name}: {param.type}{default_str}")

            print(f"\nTables ({len(schema.tables)}):")
            for name, table in schema.tables.items():
                nested_info = f" -> {table.nested_table}" if table.nested_table else ""
                print(f"  - {name}{nested_info}")
                for attr in table.attributes:
                    print(f"      {attr.name}: {attr.type}")
        else:
            print("\nSchema has errors:")
            print(result.format_errors())
            sys.exit(1)

    except SchemaParseError as e:
        print(f"Error parsing schema: {e}")
        sys.exit(1)


def cmd_gui(args):
    """Handle the 'gui' command."""
    run_gui(args.project_file)


def cmd_info(args):
    """Handle the 'info' command."""
    manifest = load_manifest(args.project_file)
    project_base_dir = str(get_project_base_dir(args.project_file))

    print(f"Project: {manifest.get('name', 'Unknown')}")
    print(f"Version: {manifest.get('_version', '1.0')}")
    print(f"Description: {manifest.get('description', 'No description')}")
    print(f"Base directory: {project_base_dir}")
    print()

    if manifest.get('schema'):
        print(f"Schema: {manifest['schema']}")
    if manifest.get('definition'):
        print(f"UI Definition: {manifest['definition']}")
    print()

    templates = manifest.get('templates', [])
    print(f"Templates ({len(templates)}):")
    for t in templates:
        print(f"  - {t.get('source')} -> {t.get('destination')}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='verigen',
        description="VeriGen - A generic code generation tool using Jinja2 templates.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='Available commands'
    )

    # Generate command
    gen_parser = subparsers.add_parser(
        'generate',
        help='Generate code from templates',
        description='Generate code from Jinja2 templates using a configuration file.'
    )
    gen_parser.add_argument(
        'project_file',
        metavar='PROJECT',
        help="Path to the VeriGen project manifest file (.verigen.yaml)"
    )
    gen_parser.add_argument(
        '-c', '--config',
        metavar='FILE',
        required=True,
        help="Path to the YAML configuration file with parameter values"
    )
    gen_parser.add_argument(
        '-o', '--output',
        metavar='DIR',
        required=True,
        help="Output directory for generated files"
    )
    gen_parser.set_defaults(func=cmd_generate)

    # Validate command
    val_parser = subparsers.add_parser(
        'validate',
        help='Validate a schema file',
        description='Validate a VeriGen schema file for correctness.'
    )
    val_parser.add_argument(
        'file',
        metavar='SCHEMA',
        help="Path to the schema file to validate"
    )
    val_parser.set_defaults(func=cmd_validate)

    # GUI command
    gui_parser = subparsers.add_parser(
        'gui',
        help='Launch the graphical user interface',
        description='Open the VeriGen GUI for interactive configuration.'
    )
    gui_parser.add_argument(
        'project_file',
        metavar='PROJECT',
        nargs='?',
        default=None,
        help="Optional path to a VeriGen project manifest file (.verigen.yaml)"
    )
    gui_parser.set_defaults(func=cmd_gui)

    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Display project information',
        description='Show information about a VeriGen project.'
    )
    info_parser.add_argument(
        'project_file',
        metavar='PROJECT',
        help="Path to the VeriGen project manifest file (.verigen.yaml)"
    )
    info_parser.set_defaults(func=cmd_info)

    # Parse arguments
    args = parser.parse_args()

    if args.command and hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
