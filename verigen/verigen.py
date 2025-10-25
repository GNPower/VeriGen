import argparse
import ctypes
import sys
import os
from typing import List, TypedDict
import yaml
import ttkbootstrap as tb

from gui import DynamicGui
from templates import generate_templates


class TemplateDefinition(TypedDict):
    """
    Defines a code template with source template path and destination render path.
    Use of Jinja2 parameters in destination path is allowed.
    """
    source: str
    destination: str

class ProjectManifest(TypedDict):
    """
    Defines a project manifest containing a name, description,
    relative path to parameter definition file, and list of TemplateDefinitions.
    """
    name: str
    description: str
    definition: str
    templates: List[TemplateDefinition]


def run_cli_generation_wrapper(
        manifest: ProjectManifest,
        project_base_dir: str,
        config_path: str,
        output_dir: str
    ):
    """Template generation for cli mode

    Args:
        manifest (ProjectManifest): Project Manifest loaded from a manifest file
        project_base_dir (str): Directory from which all project manifest paths are specified
        config_path (str): Path to the user parameter configuration file. Parameters are used to render the template
        output_dir (str): Directory to output the generated files to (does not need to exist prior to function call)

    Raises:
        ValueError: Configuration file has invalid sructure
    """
    print("--- Running in Command-Line Mode ---")
    try:
        print(f"Loading user parameters from: {config_path}")
        with open(config_path, 'r') as f:
            params = yaml.safe_load(f)
        if not isinstance(params, dict):
            raise ValueError("Configuration file is not a valid key-value structure.")
        generate_templates(
            project_data=manifest,
            project_base_dir=project_base_dir,
            output_dir=output_dir,
            user_params=params
        )
        print(f"\nGeneration complete. Files saved in '{output_dir}'.")
    except FileNotFoundError:
        print(f"Error: User configuration file not found at '{config_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during generation: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="A generic, multi-file code generation tool using Jinja2 templates.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'project_file',
        metavar='<project.verigen.yaml>',
        help="Path to the VeriGen project manifest file."
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help="Run the application with the graphical user interface."
    )
    parser.add_argument(
        '-c', '--config',
        metavar='<file_path>',
        help="[CLI Mode] Path to the YAML file with user parameters."
    )
    parser.add_argument(
        '-o', '--output',
        metavar='<dir_path>',
        help="[CLI/GUI Mode] Directory where the output files will be saved."
    )
    args = parser.parse_args()

    try:
        project_abs_path = os.path.abspath(args.project_file)
        project_base_dir = os.path.dirname(project_abs_path)
        with open(project_abs_path, 'r') as f:
            manifest = yaml.safe_load(f)
        if not all(k in manifest for k in ['name', 'description', 'definition', 'templates']):
            raise ValueError("Project manifest is missing required keys: 'name', 'description', 'definition', 'templates'.")
    except FileNotFoundError:
        print(f"Error: Project manifest file not found at '{args.project_file}'")
        sys.exit(1)
    except (yaml.YAMLError, ValueError) as e:
        print(f"Error: Could not parse project manifest file '{args.project_file}':\n{e}")
        sys.exit(1)

    if args.gui:
        root = tb.Window()
        root.title(manifest.get('name', 'VeriGen Code Generator'))

        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icons", "512.png")
            app_icon = tb.PhotoImage(file=icon_path)
            # Custom app id required so windows uses our icon on toolbar not Python's
            myappid = 'tkinter.python.verigen'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            # For some reason, True works when later windows are spawned but not on root.
            # So we will 1. Add iconphoto with False so it shows up on this window.
            # 2. Re-add iconphoto with True so it works on any additional windows.
            root.iconphoto(False, app_icon)
            root.iconphoto(True, app_icon)
        except Exception as e:
            print(f"Warning: Could not load application icon. Error: {e}")

        # Dynamically populate the gui
        DynamicGui(
            root,
            manifest,
            os.path.join(project_base_dir, manifest['definition']),
            project_base_dir
        )

        root.mainloop()
    else:
        if not all([args.config, args.output]):
            parser.error("In CLI mode, --config (-c) and --output (-o) are required.")
        run_cli_generation_wrapper(
            manifest=manifest,
            project_base_dir=project_base_dir,
            config_path=args.config,
            output_dir=args.output
        )


if __name__ == "__main__":
    main()
