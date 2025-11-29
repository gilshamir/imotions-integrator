import tkinter as tk

def load_config(file_path):
    config = {}
    current_section = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
            elif '=' in line:
                key, value = line.split('=')
                if current_section:
                    config[current_section][key.strip()] = value.strip()
    return config

def save_config(file_path, config):
    with open(file_path, 'w') as file:
        for section, section_data in config.items():
            file.write(f"[{section}]\n")
            for key, value in section_data.items():
                file.write(f"{key}={value}\n")
            file.write("\n")

def update_config_value(section, key, value):
    config[section][key] = value

def on_save_button_click():
    for section, entry_widgets in entry_widgets_dict.items():
        for key in entry_widgets:
            update_config_value(section, key, entry_widgets[key].get())
    save_config(config_file_path, config)

def set_window_height(window):
    window.update_idletasks()
    content_height = window.winfo_reqheight()
    window.geometry(f"350x{content_height}")

# Load the config file
config_file_path = 'config.ini'
config = load_config(config_file_path)

# Create the GUI
root = tk.Tk()
root.title("Config Parser 1.0")  # Set the title of the GUI form
root.resizable(False, False)  # Disable resizing of the GUI window
entry_widgets_dict = {}

# Add entry fields for each section's key-value pairs with padding
row = 0
for section, section_data in config.items():
    label = tk.Label(root, text=f"{section}")
    label.grid(row=row, column=0, columnspan=2, padx=10, pady=5)
    row += 1

    entry_widgets = {}
    for i, (key, value) in enumerate(section_data.items(), start=row):
        label = tk.Label(root, text=key)
        label.grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
        entry = tk.Entry(root)
        entry.insert(0, value)
        entry.grid(row=i, column=1, padx=5, pady=2)
        entry_widgets[key] = entry

    entry_widgets_dict[section] = entry_widgets
    row += len(section_data)

# Add save button with padding
save_button = tk.Button(root, text="Save", command=on_save_button_click)
save_button.grid(row=row, column=0, columnspan=2, padx=10, pady=15, sticky=tk.E)

set_window_height(root)

root.mainloop()
