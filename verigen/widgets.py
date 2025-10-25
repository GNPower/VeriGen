import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import LEFT, RIGHT, READONLY, SECONDARY, LIGHT, DANGER, OUTLINE, END, BOTH, VERTICAL, SUCCESS, INVERSE
from PIL import Image, ImageTk


def create_widget_from_config(parent, config, tooltip_manager):
    container = tb.Frame(parent)
    widget_id = config['id']
    widget_type = config['type']
    label = tb.Label(container, text=f"{config.get('label', widget_id)}:", width=20)
    label.pack(side=LEFT, padx=(0, 10))
    if 'tooltip' in config:
        tooltip_manager.add_tooltip(label, config['tooltip'])
    if widget_type == 'string':
        widget = tb.Entry(container)
        if 'default' in config: widget.insert(0, config['default'])
    elif widget_type == 'integer':
        widget = tb.Spinbox(container, from_=config.get('min', 0), to=config.get('max', 1000))
        if 'default' in config: widget.set(config['default'])
    elif widget_type == 'choice':
        widget = tb.Combobox(container, values=config['options'], state=READONLY)
        if 'default' in config: widget.set(config['default'])
    elif widget_type == 'boolean':
        var = tb.BooleanVar(value=config.get('default', False))
        widget = tb.Checkbutton(container, variable=var)
        widget.pack(side=LEFT)
        if 'tooltip' in config:
            tooltip_manager.add_tooltip(widget, config['tooltip'])
        return container, widget_id, var
    else:
        widget = tb.Label(container, text=f"Unsupported type: {widget_type}")
    widget.pack(side=LEFT, fill="x", expand=True)
    if 'tooltip' in config:
        tooltip_manager.add_tooltip(widget, config['tooltip'])
    return container, widget_id, widget


class DynamicTableRow(tb.Frame):

    def __init__(self, parent, sub_elements, tooltip_manager, delete_callback):
        super().__init__(parent, padding=5)
        self.configure(bootstyle=SECONDARY) # pyright: ignore[reportCallIssue]
        self.sub_elements_config = sub_elements
        self.tooltip_manager = tooltip_manager
        self.widgets = {}
        self.summary_frame = tb.Frame(self)
        self.summary_frame.pack(fill="x", expand=True)
        self.toggle_button = tb.Button(self.summary_frame, text="▶", width=3, command=self.toggle_details, bootstyle=LIGHT) # pyright: ignore[reportCallIssue]
        self.toggle_button.pack(side=LEFT)
        summary_config = next((el for el in sub_elements if el.get('is_summary')), sub_elements[0])
        self.summary_label_widget = tb.Label(self.summary_frame, text="New Item", font="-weight bold")
        self.summary_label_widget.pack(side=LEFT, padx=5)

        try:
            img = Image.open('icons/delete_icon.png')
            self.delete_icon = ImageTk.PhotoImage(img.resize((18, 18), Image.Resampling.LANCZOS))
            delete_button = tb.Button(self.summary_frame, image=self.delete_icon, command=delete_callback, bootstyle=(DANGER, OUTLINE)) # pyright: ignore[reportCallIssue]
        except FileNotFoundError:
            delete_button = tb.Button(self.summary_frame, text="🗑", width=3, command=delete_callback, bootstyle=(DANGER, OUTLINE)) # pyright: ignore[reportCallIssue]

        delete_button.pack(side=RIGHT)
        self.tooltip_manager.add_tooltip(delete_button, "Delete Register")

        self.details_frame = tb.Frame(self)
        for elem_config in sub_elements:
            elem_frame, elem_id, widget = create_widget_from_config(self.details_frame, elem_config, self.tooltip_manager)
            elem_frame.pack(fill="x", expand=True, padx=20, pady=4)
            self.widgets[elem_id] = widget
            if elem_config.get('is_summary'):
                if isinstance(widget, tb.Entry):
                    widget.bind("<KeyRelease>", self.update_summary_label)


    def toggle_details(self):
        if self.details_frame.winfo_viewable():
            self.details_frame.pack_forget()
            self.toggle_button.config(text="▶")
        else:
            self.details_frame.pack(fill="x", expand=True, pady=5)
            self.toggle_button.config(text="▼")
            self.update_summary_label()


    def update_summary_label(self, event=None):
        summary_config = next((el for el in self.sub_elements_config if el.get('is_summary')), None)
        if summary_config:
            summary_widget = self.widgets.get(summary_config['id'])
            if summary_widget:
                self.summary_label_widget.config(text=summary_widget.get() or "New Item")


    def set_data(self, data):
        for sub_id, sub_val in data.items():
            if sub_id in self.widgets:
                sub_widget = self.widgets[sub_id]
                if isinstance(sub_widget, tb.BooleanVar):
                    sub_widget.set(sub_val)
                elif isinstance(sub_widget, tb.Entry):
                    sub_widget.delete(0, END)
                    sub_widget.insert(0, sub_val)
                else:
                    sub_widget.set(sub_val)
        self.update_summary_label()


    def get_data(self):
        data = {}
        for elem_config in self.sub_elements_config:
            widget_id = elem_config['id']
            widget = self.widgets[widget_id]
            elem_type = elem_config['type']
            if isinstance(widget, tb.BooleanVar): raw_value = widget.get()
            else: raw_value = widget.get()
            try:
                if elem_type == 'integer': data[widget_id] = int(raw_value) if raw_value else 0
                elif elem_type == 'boolean': data[widget_id] = bool(raw_value)
                else: data[widget_id] = raw_value
            except (ValueError, TypeError): data[widget_id] = elem_config.get('default', '')
        return data


class DynamicTableWidget(tb.Frame):

    def __init__(self, parent, config, tooltip_manager):
        super().__init__(parent)
        self.config = config
        self.tooltip_manager = tooltip_manager
        self.rows = []
        scroll_area = tb.Frame(self)
        scroll_area.pack(fill=BOTH, expand=True)
        canvas = tk.Canvas(scroll_area, borderwidth=0, highlightthickness=0)
        self.scrollable_frame = tb.Frame(canvas)
        scrollbar = tb.Scrollbar(scroll_area, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill="y")
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        action_frame = tb.Frame(self)
        action_frame.pack(fill='x', pady=10)

        try:
            img = Image.open('icons/add_icon.png')
            self.add_icon = ImageTk.PhotoImage(img.resize((24, 24), Image.Resampling.LANCZOS))
            add_button = tb.Button(action_frame, image=self.add_icon, text=config.get('add_button_text', "Add Item"),
                                   compound=LEFT, command=self.add_row, bootstyle=SUCCESS) # pyright: ignore[reportCallIssue]
        except FileNotFoundError:
            add_button = tb.Button(action_frame, text="+ " + config.get('add_button_text', "Add Item"),
                                   command=self.add_row, bootstyle=SUCCESS) # pyright: ignore[reportCallIssue]

        add_button.pack()
        if 'tooltip' in config:
            self.tooltip_manager.add_tooltip(add_button, config['tooltip'])


    def add_row(self):
        new_row = DynamicTableRow(self.scrollable_frame, self.config['sub_elements'], self.tooltip_manager, delete_callback=lambda: None)
        new_row.pack(fill="x", expand=True, padx=5, pady=4)
        delete_button = new_row.summary_frame.winfo_children()[-1]
        delete_button.config(command=lambda r=new_row: self.delete_row(r)) # pyright: ignore[reportAttributeAccessIssue]
        self.rows.append(new_row)


    def delete_row(self, row_to_delete):
        row_to_delete.destroy()
        self.rows.remove(row_to_delete)


    def get_data(self):
        return [row.get_data() for row in self.rows]


class TooltipManager:

    def add_tooltip(self, widget, text):
        tooltip = Tooltip(widget, text)
        widget.bind('<Enter>', lambda e: tooltip.showtip())
        widget.bind('<Leave>', lambda e: tooltip.hidetip())


class Tooltip(object):

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None


    def showtip(self):
        if self.tipwindow or not self.text: return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tb.Toplevel(self.widget)
        tw.wm_overrideredirect(1) # pyright: ignore[reportArgumentType, reportCallIssue]
        tw.wm_geometry(f"+{x}+{y}")
        label = tb.Label(tw, text=self.text, justify=LEFT, bootstyle=(INVERSE, LIGHT), padding=5) # pyright: ignore[reportCallIssue]
        label.pack(ipadx=1)


    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw: tw.destroy()
