import os
import yaml
from tkinter import filedialog, font
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, BOTTOM, READONLY, SUCCESS, DISABLED, NORMAL, END

from widgets import DynamicTableWidget, create_widget_from_config, TooltipManager
from templates import generate_templates

class DynamicGui:

    def __init__(self, root, project_data, ui_yaml_file, project_base_dir):
        self.root = root

        try:
            default_font = font.nametofont("TkDefaultFont")
            default_font.configure(family="Segoe UI", size=10)
        except Exception:
            print("Segoe UI font not found, using system default.")

        self.project_data = project_data
        self.ui_yaml_file = ui_yaml_file
        self.project_base_dir = project_base_dir
        self.widgets = {}
        self.page_frames = []
        self.current_page = 0
        self.image_references = []
        self.tooltip_manager = TooltipManager()
        self.save_config_var = tb.BooleanVar(value=True)

        if not self.load_config(): return
        self.setup_main_window()
        self.create_pages()
        self.create_navigation()
        self.show_page(0)


    def load_config(self):
        try:
            with open(self.ui_yaml_file, 'r') as f:
                self.ui_config = yaml.safe_load(f)
            return True
        except Exception as e:
            tb.dialogs.Messagebox.show_error(f"Failed to load UI file '{self.ui_yaml_file}':\n{e}", "Load Error", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]
            self.root.destroy()
            return False


    def setup_main_window(self):
        if 'default_size' in self.ui_config:
            self.root.geometry(self.ui_config['default_size'])
        self.main_content_frame = tb.Frame(self.root)
        self.main_content_frame.pack(fill=BOTH, expand=True)


    def create_pages(self):
        for i, page_config in enumerate(self.ui_config['pages']):
            page_frame = tb.Frame(self.main_content_frame, padding=15)
            if i == 0:
                load_frame = tb.Frame(page_frame)
                load_frame.pack(fill='x', pady=(0, 20))
                load_button = tb.Button(load_frame, text="Load Configuration...", command=self._load_configuration)
                load_button.pack(side=LEFT)
                tb.Separator(load_frame, orient='horizontal').pack(fill='x', expand=True, padx=10, side=LEFT)
            page_title = tb.Label(page_frame, text=page_config.get('title', f'Page {i+1}'), font=("-size 16 -weight bold"))
            page_title.pack(anchor="w", pady=(0,15))
            for element_config in page_config.get('elements', []):
                self.create_element(page_frame, element_config)
            self.page_frames.append(page_frame)


    def _browse_directory(self, string_var):
        dir_name = filedialog.askdirectory(parent=self.root)
        if dir_name:
            string_var.set(dir_name)


    def create_element(self, parent, config):
        element_type = config.get('type')
        if not element_type: return
        if element_type == 'dynamic_table':
            widget = DynamicTableWidget(parent, config, self.tooltip_manager)
            widget.pack(fill=BOTH, expand=True, pady=(10,0))
            self.widgets[config['id']] = widget
        elif element_type == 'summary':
            frame = tb.LabelFrame(parent, text=config.get('label', 'Summary'), padding=10)
            frame.pack(fill=BOTH, expand=True, pady=10)
            tree = tb.Treeview(frame, columns=('Parameter', 'Value'), show='headings')
            tree.heading('Parameter', text='Parameter')
            tree.heading('Value', text='Value')
            tree.column('Parameter', width=220)
            tree.pack(fill=BOTH, expand=True)
            self.widgets[config['id']] = tree
        elif element_type == 'directory_selector':
            frame = tb.LabelFrame(parent, text=config.get('label', 'Directory'), padding=10)
            frame.pack(fill='x', pady=10)
            path_var = tb.StringVar()
            entry = tb.Entry(frame, textvariable=path_var, state=READONLY)
            entry.pack(side=LEFT, fill='x', expand=True, padx=(0, 5))
            button = tb.Button(frame, text="Browse...", command=lambda: self._browse_directory(path_var))
            button.pack(side=LEFT)
            self.widgets[config['id']] = path_var
            if 'tooltip' in config:
                self.tooltip_manager.add_tooltip(entry, config['tooltip'])
        elif element_type == 'image':
            try:
                img_path = os.path.join(self.project_base_dir, config['path'])
                img = Image.open(img_path)
                if 'height' in config:
                    ratio = img.width / img.height
                    img = img.resize((int(config['height'] * ratio), config['height']), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tb.Label(parent, image=photo)
                label.pack(pady=10)
                self.image_references.append(photo)
            except Exception as e:
                tb.Label(parent, text=f"Image Error: {e}").pack()
        elif element_type == 'label':
             tb.Label(parent, text=config.get('text', ''), wraplength=550, justify='left').pack(anchor='w', pady=5)
        else:
            container, widget_id, widget = create_widget_from_config(parent, config, self.tooltip_manager)
            container.pack(fill='x', padx=5, pady=8, anchor='w')
            self.widgets[widget_id] = widget


    def create_navigation(self):
        self.nav_frame = tb.Frame(self.root, padding=10)
        self.nav_frame.pack(fill="x", side=BOTTOM)
        tb.Separator(self.nav_frame).pack(fill='x', expand=True, pady=(0,10))
        self.back_button = tb.Button(self.nav_frame, text="< Back", command=self.prev_page)
        self.back_button.pack(side=LEFT)
        self.next_button = tb.Button(self.nav_frame, text="Next >", command=self.next_page)
        self.next_button.pack(side=RIGHT)
        self.generate_frame = tb.Frame(self.nav_frame)
        self.save_config_checkbox = tb.Checkbutton(self.generate_frame, text="Save configuration file", variable=self.save_config_var)
        self.save_config_checkbox.pack(side=LEFT, padx=(0, 10))
        self.generate_button = tb.Button(self.generate_frame, text="Generate and Save", command=self.generate_code, bootstyle=SUCCESS) # pyright: ignore[reportCallIssue]
        self.generate_button.pack(side=LEFT)


    def show_page(self, page_index):
        if self.page_frames:
            self.page_frames[self.current_page].pack_forget()
        self.current_page = page_index
        self.page_frames[self.current_page].pack(fill=BOTH, expand=True)
        self.back_button.config(state=NORMAL if self.current_page > 0 else DISABLED)
        self.next_button.config(state=NORMAL if self.current_page < len(self.page_frames) - 1 else DISABLED)
        self.generate_frame.pack_forget()
        if self.current_page == len(self.page_frames) - 1:
            self._update_summary()
            self.generate_frame.pack(side=RIGHT)


    def next_page(self):
        if self.current_page < len(self.page_frames) - 1:
            self.show_page(self.current_page + 1)


    def prev_page(self):
        if self.current_page > 0:
            self.show_page(self.current_page - 1)


    def _load_configuration(self):
        filepath = filedialog.askopenfilename(
            parent=self.root,
            title="Load Configuration File",
            filetypes=[("YAML Configuration", "*.yaml"), ("All Files", "*.*")]
        )
        if not filepath: return
        try:
            with open(filepath, 'r') as f:
                loaded_data = yaml.safe_load(f)
            if not isinstance(loaded_data, dict):
                raise ValueError("Configuration file is not a valid key-value structure.")
        except Exception as e:
            tb.dialogs.Messagebox.show_error(f"Failed to read or parse configuration file:\n{e}", "Load Error", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]
            return
        if self._validate_and_populate(loaded_data):
            tb.dialogs.Messagebox.show_info("Configuration loaded successfully.", "Success", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]


    def _validate_and_populate(self, data):
        errors = []
        all_ui_elements = {elem['id']: elem for page in self.ui_config['pages'] for elem in page.get('elements', []) if 'id' in elem}
        expected_ids = {elem['id'] for elem in all_ui_elements.values() if elem.get('type') not in ['summary', 'image', 'label', 'directory_selector']}
        loaded_ids = set(data.keys())
        missing_ids = expected_ids - loaded_ids
        for param_id in missing_ids:
            errors.append(f"- Parameter '{param_id}' is missing from the configuration file.")
        extra_ids = loaded_ids - expected_ids
        for param_id in extra_ids:
            errors.append(f"- Parameter '{param_id}' from the file is not defined in the current UI.")
        for param_id in expected_ids.intersection(loaded_ids):
            config = all_ui_elements[param_id]
            value = data[param_id]
            try:
                if config['type'] == 'choice' and value not in config['options']:
                    errors.append(f"- Parameter '{param_id}': Value '{value}' is not a valid option. Valid options are: {config['options']}.")
                if config['type'] == 'integer' and not isinstance(value, int):
                    errors.append(f"- Parameter '{param_id}': Value must be an integer, but got type '{type(value).__name__}'.")
                if config['type'] == 'boolean' and not isinstance(value, bool):
                    errors.append(f"- Parameter '{param_id}': Value must be a boolean (true/false), but got type '{type(value).__name__}'.")
            except Exception as e:
                errors.append(f"An unexpected error occurred while validating parameter '{param_id}': {e}")
        if errors:
            error_summary = "Configuration file is invalid. The following issues were found:\n\n" + "\n".join(errors)
            tb.dialogs.Messagebox.show_error(error_summary, "Validation Failed", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]
            return False
        for param_id, value in data.items():
            widget = self.widgets[param_id]
            if isinstance(widget, (tb.StringVar, tb.BooleanVar)):
                widget.set(value)
            elif isinstance(widget, DynamicTableWidget):
                for row in widget.rows[:]: widget.delete_row(row)
                for item_data in value:
                    widget.add_row()
                    new_row_widget = widget.rows[-1]
                    new_row_widget.set_data(item_data)
            elif isinstance(widget, tb.Entry):
                widget.delete(0, END)
                widget.insert(0, value)
            else:
                widget.set(value)
        return True


    def _get_all_params(self):
        params = {}
        all_elements = [elem for page in self.ui_config['pages'] for elem in page.get('elements', [])]
        for elem_config in all_elements:
            elem_id = elem_config.get('id')
            elem_type = elem_config.get('type')
            if elem_type == 'summary': continue
            if not elem_id or elem_id not in self.widgets: continue
            widget = self.widgets[elem_id]
            if hasattr(widget, 'get_data'):
                params[elem_id] = widget.get_data()
            elif isinstance(widget, (tb.BooleanVar, tb.StringVar)):
                params[elem_id] = widget.get()
            else:
                raw_value = widget.get()
                try:
                    if elem_type == 'integer': params[elem_id] = int(raw_value)
                    elif elem_type == 'choice' and all(isinstance(opt, int) for opt in elem_config.get('options', [])): params[elem_id] = int(raw_value)
                    else: params[elem_id] = raw_value
                except (ValueError, TypeError): params[elem_id] = elem_config.get('default', '')
        return params


    def _update_summary(self):
        summary_tree = self.widgets.get('summary_view')
        if not summary_tree: return
        summary_tree.delete(*summary_tree.get_children())
        params = self._get_all_params()
        for key, value in params.items():
            elem_config = next((e for p in self.ui_config['pages'] for e in p.get('elements', []) if e.get('id') == key), None)
            label = elem_config.get('label', key) if elem_config else key
            if isinstance(value, list):
                parent_item = summary_tree.insert('', 'end', values=(f"{label} ({len(value)} items)", ""))
                for i, item_dict in enumerate(value):
                    reg_name = item_dict.get('name', f"Register {i+1}")
                    child_item = summary_tree.insert(parent_item, 'end', values=(f"  ↳ {reg_name}", ""))
                    for sub_key, sub_val in item_dict.items():
                        summary_tree.insert(child_item, 'end', values=(f"    • {sub_key}", sub_val))
            elif isinstance(value, bool):
                summary_tree.insert('', 'end', values=(label, "Enabled" if value else "Disabled"))
            elif key != 'save_directory':
                summary_tree.insert('', 'end', values=(label, value))


    def generate_code(self):
        params = self._get_all_params()
        output_dir = params.get('save_directory')
        module_name = params.get('module_name', 'generated_ip')
        if not output_dir:
            tb.dialogs.Messagebox.show_error("Please select an output directory before generating.", "Error", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]
            return
        try:
            generate_templates(
                project_data=self.project_data,
                project_base_dir=self.project_base_dir,
                output_dir=output_dir,
                user_params=params
            )
            if self.save_config_var.get():
                config_filename = f"{module_name}.yaml"
                config_filepath = os.path.join(output_dir, config_filename)
                params_to_save = params.copy()
                if 'save_directory' in params_to_save:
                    del params_to_save['save_directory']
                with open(config_filepath, 'w') as f:
                    yaml.dump(params_to_save, f, default_flow_style=False, sort_keys=False)
                tb.dialogs.Messagebox.show_info(f"Successfully generated project files and configuration in:\n{output_dir}", "Success", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]
            else:
                tb.dialogs.Messagebox.show_info(f"Successfully generated project files in:\n{output_dir}", "Success", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]
        except Exception as e:
            tb.dialogs.Messagebox.show_error(f"A failure occurred during generation:\n{e}", "Generation Failed", parent=self.root) # pyright: ignore[reportAttributeAccessIssue]
