import time
import tkinter as tk
from tkinter import ttk

from gps import GPSListener
from smarteye import SEListener
from trigger_box import TriggerBoxListener
from h10 import H10Listener
from vivosmart5 import Vivosmart5Listener

import threading
import configparser
import socket

import ast

class ToggleButton(ttk.Frame):
    def __init__(self, parent, text, variable, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.variable = variable
        
        # Create the button frame
        self.button_frame = tk.Frame(self, borderwidth=1, relief="solid")
        self.button_frame.pack(expand=True, fill="both", padx=5, pady=2)
        
        # Label
        self.label = tk.Label(self.button_frame, text=text, padx=10, pady=5)
        self.label.pack(expand=True, fill="both")
        
        # Bind click events
        self.button_frame.bind("<Button-1>", self.toggle)
        self.label.bind("<Button-1>", self.toggle)
        
        # Update initial state
        self.update_state()
        
    def toggle(self, event=None):
        self.variable.set(not self.variable.get())
        self.update_state()
        
    def update_state(self):
        if self.variable.get():
            self.button_frame.configure(bg="#90EE90")  # Light green
            self.label.configure(bg="#90EE90")
        else:
            self.button_frame.configure(bg="#E0E0E0")  # Light grey
            self.label.configure(bg="#E0E0E0")

class IMotionsIntegrator():
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("IMotions Integrator")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.log_text = None  # Will be set after widget creation
        self.style = ttk.Style(self.root)
        self.current_theme = "light"
        self._create_menu()

        # Read checkbox states from config file
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')        
        
        self.gps_com = "COM9"
        self.triggerbox_com = "COM10"
        self.vivosmart5_address = "EC:8B:36:92:28:93"
        
        #listeners
        self.smarteye_listener = None
        self.gps_listener = None
        self.triggerbox_listener = None
        self.h10_listener = None
        self.vivosmart5_listener = None
        
        # Spinner state for modules
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_active = {
            "imotions": False,
            "triggerbox": False,
            "gps": False,
            "smarteye": False,
            "h10": False,
            "vivosmart5": False
        }
        
        # Set window size
        self.window_width = 400
        self.window_height = 580
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.x_coordinate = int((self.screen_width / 2) - (self.window_width / 2))
        self.y_coordinate = int((self.screen_height / 2) - (self.window_height / 2))
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.x_coordinate}+{self.y_coordinate}")
        
        self.stream = None

        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(expand=True, fill="both", padx=10, pady=2)

        #Configuration form
        config_frame = ttk.LabelFrame(main_container, text="Connection Settings")
        config_frame.pack(fill="both", pady=(2,2))

        # IMotions settings (side by side IP and Port)
        imotions_frame = ttk.Frame(config_frame)
        imotions_frame.pack(fill="x", padx=10, pady=5)

        ip_port_row = ttk.Frame(imotions_frame)
        ip_port_row.pack(fill="x", pady=(2, 2))

        ip_label = ttk.Label(ip_port_row, text="IMotions IP:")
        ip_label.pack(side="left", padx=(0,5))
        self.ip_entry = ttk.Entry(ip_port_row, width=15)
        self.ip_entry.insert(0, "192.168.0.100")
        self.ip_entry.pack(side="left", padx=(0,2))

        port_label = ttk.Label(ip_port_row, text="Port:")
        port_label.pack(side="left", padx=(0,5))
        self.port_entry = ttk.Entry(ip_port_row, width=6)
        self.port_entry.insert(0, "8089")
        self.port_entry.pack(side="left")

        ################### SE settings (side by side label and entry) ###################
        se_frame = ttk.Frame(config_frame)
        se_frame.pack(fill="x", padx=10, pady=5)
        se_port_row = ttk.Frame(se_frame)
        se_port_row.pack(fill="x", pady=(2, 2))
        se_port_label = ttk.Label(se_port_row, text="SmartEye UDP Port:")
        se_port_label.pack(side="left", padx=(0,5))
        self.se_port_entry = ttk.Entry(se_port_row, width=8)
        self.se_port_entry.insert(0, "8089")
        self.se_port_entry.pack(side="left")

        # Connect and Config buttons
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill="x", padx=10, pady=2)

        config_button = tk.Button(button_frame, text="Edit Config File", command=self.open_config_in_notepad, bg="#FFCCFF", border=0)
        config_button.pack(fill="x", pady=(0, 5))

        imotions_btn_frame = ttk.Frame(button_frame)
        imotions_btn_frame.pack(fill="x", pady=5)
        self.imotions_spinner = ttk.Label(imotions_btn_frame, text="", width=2, foreground="blue")
        self.imotions_spinner.pack(side="left", padx=2)
        self.imotions_connect_btn = tk.Button(imotions_btn_frame, text="Connect to IMotions", command=self.connectIMotions, bg="#E8F4E8", border=1)
        self.imotions_connect_btn.pack(side="left", fill="x", expand=True)

        ##################################################################################

        # Supported Modules
        modules_frame = ttk.LabelFrame(main_container, text="Modules")
        modules_frame.pack(fill="x", pady=(5, 5))

        # Create module rows with labels and connect/disconnect buttons
        # Trigger Box
        triggerbox_row = ttk.Frame(modules_frame)
        triggerbox_row.pack(fill="x", padx=5, pady=2)
        triggerbox_label = ttk.Label(triggerbox_row, text="Trigger Box", width=20)
        triggerbox_label.pack(side="left", fill="x", expand=True)
        self.triggerbox_status = ttk.Label(triggerbox_row, text="⚫", foreground="gray")
        self.triggerbox_status.pack(side="right", padx=5)
        triggerbox_disconnect_btn = tk.Button(triggerbox_row, text="Disconnect", command=self.disconnectTriggerBox, width=10, bg="#FFE8E8", border=1)
        triggerbox_disconnect_btn.pack(side="right", padx=1)
        self.triggerbox_spinner = ttk.Label(triggerbox_row, text="", width=2, foreground="blue")
        self.triggerbox_spinner.pack(side="right", padx=1)
        triggerbox_btn = tk.Button(triggerbox_row, text="Connect", command=self.connectTriggerBox, width=8, bg="#E8F4E8", border=1)
        triggerbox_btn.pack(side="right", padx=1)

        # GPS
        gps_row = ttk.Frame(modules_frame)
        gps_row.pack(fill="x", padx=5, pady=2)
        gps_label = ttk.Label(gps_row, text="GPS", width=20)
        gps_label.pack(side="left", fill="x", expand=True)
        self.gps_status = ttk.Label(gps_row, text="⚫", foreground="gray")
        self.gps_status.pack(side="right", padx=5)
        gps_disconnect_btn = tk.Button(gps_row, text="Disconnect", command=self.disconnectGPS, width=10, bg="#FFE8E8", border=1)
        gps_disconnect_btn.pack(side="right", padx=1)
        self.gps_spinner = ttk.Label(gps_row, text="", width=2, foreground="blue")
        self.gps_spinner.pack(side="right", padx=1)
        gps_btn = tk.Button(gps_row, text="Connect", command=self.connectGPS, width=8, bg="#E8F4E8", border=1)
        gps_btn.pack(side="right", padx=1)

        # SmartEye
        se_row = ttk.Frame(modules_frame)
        se_row.pack(fill="x", padx=5, pady=2)
        se_label = ttk.Label(se_row, text="SmartEye", width=20)
        se_label.pack(side="left", fill="x", expand=True)
        self.se_status = ttk.Label(se_row, text="⚫", foreground="gray")
        self.se_status.pack(side="right", padx=5)
        se_disconnect_btn = tk.Button(se_row, text="Disconnect", command=self.disconnectSmartEye, width=10, bg="#FFE8E8", border=1)
        se_disconnect_btn.pack(side="right", padx=1)
        self.se_spinner = ttk.Label(se_row, text="", width=2, foreground="blue")
        self.se_spinner.pack(side="right", padx=1)
        se_btn = tk.Button(se_row, text="Connect", command=self.connectSmartEye, width=8, bg="#E8F4E8", border=1)
        se_btn.pack(side="right", padx=1)

        # Polar H10
        h10_row = ttk.Frame(modules_frame)
        h10_row.pack(fill="x", padx=5, pady=2)
        h10_label = ttk.Label(h10_row, text="Polar H10", width=20)
        h10_label.pack(side="left", fill="x", expand=True)
        self.h10_status = ttk.Label(h10_row, text="⚫", foreground="gray")
        self.h10_status.pack(side="right", padx=5)
        h10_disconnect_btn = tk.Button(h10_row, text="Disconnect", command=self.disconnectH10, width=10, bg="#FFE8E8", border=1)
        h10_disconnect_btn.pack(side="right", padx=1)
        self.h10_spinner = ttk.Label(h10_row, text="", width=2, foreground="blue")
        self.h10_spinner.pack(side="right", padx=1)
        h10_btn = tk.Button(h10_row, text="Connect", command=self.connectH10, width=8, bg="#E8F4E8", border=1)
        h10_btn.pack(side="right", padx=1)

        # Vivosmart 5
        vivosmart5_row = ttk.Frame(modules_frame)
        vivosmart5_row.pack(fill="x", padx=5, pady=2)
        vivosmart5_label = ttk.Label(vivosmart5_row, text="Vivosmart 5", width=20)
        vivosmart5_label.pack(side="left", fill="x", expand=True)
        self.vivosmart5_status = ttk.Label(vivosmart5_row, text="⚫", foreground="gray")
        self.vivosmart5_status.pack(side="right", padx=5)
        vivosmart5_disconnect_btn = tk.Button(vivosmart5_row, text="Disconnect", command=self.disconnectVivosmart5, width=10, bg="#FFE8E8", border=1)
        vivosmart5_disconnect_btn.pack(side="right", padx=1)
        self.vivosmart5_spinner = ttk.Label(vivosmart5_row, text="", width=2, foreground="blue")
        self.vivosmart5_spinner.pack(side="right", padx=1)
        vivosmart5_btn = tk.Button(vivosmart5_row, text="Connect", command=self.connectVivosmart5, width=8, bg="#E8F4E8", border=1)
        vivosmart5_btn.pack(side="right", padx=1)

        # Multiline log textbox
        log_frame = ttk.LabelFrame(main_container, text="Log Messages")
        log_frame.pack(fill="both", expand=True, pady=(5, 5))
        self.log_text = tk.Text(log_frame, height=8, wrap="word", state="disabled")
        # 1. Configure tags for different colors
        self.log_text.tag_configure("Normal", foreground="black")
        self.log_text.tag_configure("Error", foreground="red")
        self.log_text.tag_configure("Info", foreground="blue")
        self.log_text.tag_configure("Success", foreground="green")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Load config settings
        self.load_config()
        self.set_theme(self.current_theme)
        
        self.root.mainloop()

    def _create_menu(self):
        """Create the application menu bar."""
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=False)
        themes_menu = tk.Menu(tools_menu, tearoff=False)
        self.theme_var = tk.StringVar(value=self.current_theme)
        themes_menu.add_radiobutton(
            label="Light",
            variable=self.theme_var,
            value="light",
            command=lambda: self.set_theme("light"),
        )
        themes_menu.add_radiobutton(
            label="Dark",
            variable=self.theme_var,
            value="dark",
            command=lambda: self.set_theme("dark"),
        )
        tools_menu.add_cascade(label="Themes", menu=themes_menu)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        self.menu_bar = menu_bar
        self.file_menu = file_menu
        self.tools_menu = tools_menu
        self.themes_menu = themes_menu
        self.root.configure(menu=menu_bar)

    def set_theme(self, theme):
        """Apply the selected light or dark color palette to the application."""
        if theme not in ("light", "dark"):
            raise ValueError(f"Unsupported theme: {theme}")

        self.current_theme = theme
        self.theme_var.set(theme)

        if theme == "dark":
            colors = {
                "background": "#252526",
                "surface": "#333333",
                "text": "#F1F1F1",
                "input": "#3C3C3C",
                "border": "#666666",
                "connect": "#285C35",
                "disconnect": "#6B3030",
            }
        else:
            colors = {
                "background": "#F0F0F0",
                "surface": "#FFFFFF",
                "text": "#000000",
                "input": "#FFFFFF",
                "border": "#A0A0A0",
                "connect": "#E8F4E8",
                "disconnect": "#FFE8E8",
            }

        self.root.configure(background=colors["background"])
        menu_options = {
            "background": colors["surface"],
            "foreground": colors["text"],
            "activebackground": colors["border"],
            "activeforeground": colors["text"],
        }
        for menu in (
            self.menu_bar,
            self.file_menu,
            self.tools_menu,
            self.themes_menu,
        ):
            menu.configure(**menu_options)
        self.style.configure("TFrame", background=colors["background"])
        self.style.configure(
            "TLabelframe",
            background=colors["background"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TLabelframe.Label",
            background=colors["background"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TLabel",
            background=colors["background"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TEntry",
            fieldbackground=colors["input"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TSpinbox",
            fieldbackground=colors["input"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TMenubutton",
            background=colors["surface"],
            foreground=colors["text"],
        )

        self._apply_theme_to_widgets(self.root, colors)
        if self.log_text is not None:
            self.log_text.tag_configure("Normal", foreground=colors["text"])
            self.log_text.tag_configure("Error", foreground="#FF7777")
            self.log_text.tag_configure("Info", foreground="#6EA8FE")
            self.log_text.tag_configure("Success", foreground="#70D890")

    def _apply_theme_to_widgets(self, widget, colors):
        """Update classic Tk widgets, which do not use ttk styles."""
        widget_class = widget.winfo_class()
        if widget_class in ("Frame", "Labelframe"):
            widget.configure(background=colors["background"])
        elif widget_class == "Label":
            widget.configure(
                background=colors["background"],
                foreground=colors["text"],
            )
        elif widget_class == "Text":
            widget.configure(
                background=colors["input"],
                foreground=colors["text"],
                insertbackground=colors["text"],
            )
        elif widget_class == "Button":
            label = widget.cget("text")
            button_color = (
                colors["disconnect"]
                if label == "Disconnect"
                else colors["connect"]
                if label in ("Connect", "Connect to IMotions")
                else colors["surface"]
            )
            widget.configure(
                background=button_color,
                foreground=colors["text"],
                activebackground=colors["border"],
                activeforeground=colors["text"],
            )

        for child in widget.winfo_children():
            self._apply_theme_to_widgets(child, colors)
    
    def load_config(self):

        ################### IMotions settings ######################
        if 'IMotions' in self.config:
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, self.config.get('IMotions', 'IMotions_IP'))
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, self.config.get('IMotions', 'IMotions_Port'))
            try:
                self.protocol = self.config.get('IMotions', 'protocol')
            except:
                self.protocol = "udp"
        
        ################### SmartEye settings ######################
        if 'SmartEye' in self.config:
            self.se_port_entry.delete(0, "end")
            self.se_port_entry.insert(0, self.config.get('SmartEye', 'SmartEye_Port'))
        
        ################### GPS settings ######################
        if 'GPS' in self.config:
            self.gps_com = self.config.get('GPS', 'com')
        
        ################### TriggerBox settings ######################
        if 'TriggerBox' in self.config:
            self.triggerbox_com = self.config.get('TriggerBox', 'com')
            self.triggerbox_triggers = ast.literal_eval(self.config.get('TriggerBox', 'triggers'))
        
        ################### Vivosmart5 settings ######################
        if 'Vivosmart5' in self.config:
            self.vivosmart5_address = self.config.get('Vivosmart5', 'address')
    
    def open_config_in_notepad(self):
        import subprocess
        subprocess.Popen(["notepad.exe", "config.ini"])

    def log_message(self, message, message_type="Normal"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n", message_type)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def save_config(self):
        server_ip = self.ip_entry.get()
        server_port = self.port_entry.get()
        se_server_port = self.se_port_entry.get()

        # Save IMotions settings to config file
        config = configparser.ConfigParser()
        config['IMotions'] = {
            'IMotions_IP': str(server_ip),
            'IMotions_Port': str(server_port),
            'protocol': self.protocol
        }
        config['SmartEye'] = {
            'smarteye_port': str(se_server_port)
        }
        config['GPS'] = {
            'COM': str(self.gps_com)
        }

        config['TriggerBox'] = {
            'COM': str(self.triggerbox_com),
            'Triggers': str(self.triggerbox_triggers)
        }
        
        config['Vivosmart5'] = {
            'address': str(self.vivosmart5_address)
        }

        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    
    def on_close(self):
            self.save_config()
            self.disconnect()
            self.root.destroy()  # Closes the window

    def _create_status_update_callback(self, update_method):
        """Create a callback that safely updates status from a background thread."""
        def callback(connected):
            # Schedule the UI update on the main thread
            self.root.after(0, lambda: update_method())
        return callback

    def _create_message_callback(self, module_name):
        """Create a callback for module messages that safely updates the log from a background thread."""
        def callback(message, message_type="Normal"):
            # Stop the spinner when we get a response
            self.root.after(0, lambda: self._stop_spinner(module_name))
            # Schedule the log update on the main thread
            self.root.after(0, lambda: self.log_message(message, message_type))
        return callback

    def updateTriggerBoxStatus(self):
        """Update Trigger Box status indicator based on listener state."""
        if self.triggerbox_listener is not None and hasattr(self.triggerbox_listener, 'is_connected') and self.triggerbox_listener.is_connected():
            self.triggerbox_status.config(text="🟢", foreground="green")
        else:
            self.triggerbox_status.config(text="⚫", foreground="gray")
    
    def updateGPSStatus(self):
        """Update GPS status indicator based on listener state."""
        if self.gps_listener is not None and hasattr(self.gps_listener, 'is_connected') and self.gps_listener.is_connected():
            self.gps_status.config(text="🟢", foreground="green")
        else:
            self.gps_status.config(text="⚫", foreground="gray")
    
    def updateSmartEyeStatus(self):
        """Update SmartEye status indicator based on listener state."""
        if self.smarteye_listener is not None and hasattr(self.smarteye_listener, 'is_connected') and self.smarteye_listener.is_connected():
            self.se_status.config(text="🟢", foreground="green")
        else:
            self.se_status.config(text="⚫", foreground="gray")
    
    def updateH10Status(self):
        """Update Polar H10 status indicator based on listener state."""
        if self.h10_listener is not None and self.h10_listener.is_connected():
            self.h10_status.config(text="🟢", foreground="green")
        else:
            self.h10_status.config(text="⚫", foreground="gray")
    
    def updateVivosmart5Status(self):
        """Update Garmin Vivosmart5 status indicator based on listener state."""
        if self.vivosmart5_listener is not None and self.vivosmart5_listener.is_connected():
            self.vivosmart5_status.config(text="🟢", foreground="green")
        else:
            self.vivosmart5_status.config(text="⚫", foreground="gray")

    def connectIMotions(self):
        """Connect only to IMotions server."""
        self._start_spinner("imotions")
        # Run connection in background thread to avoid blocking UI
        self.imotions_thread = threading.Thread(target=self._connectIMotionsBackground)
        self.imotions_thread.start()
    
    def _connectIMotionsBackground(self):
        """Background thread for IMotions connection."""
        # Clear log textbox at start
        self.root.after(0, lambda: self.log_text.configure(state="normal"))
        self.root.after(0, lambda: self.log_text.delete("1.0", "end"))
        self.root.after(0, lambda: self.log_text.configure(state="disabled"))

        server_ip = self.ip_entry.get()
        server_port = int(self.port_entry.get())
        self.root.after(0, lambda: self.log_message(f"IMotions Protocol: {self.protocol.upper()}"))
        self.save_config()
        if self.protocol.upper() == '"TCP"':
            self.stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.stream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.stream.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.root.after(0, lambda: self.log_message(f"Connecting to IMotions Server: {server_ip}:{server_port}"))
            self.stream.connect((server_ip, server_port))
            self.root.after(0, lambda: self._stop_spinner("imotions"))
            self.root.after(0, lambda: self.imotions_connect_btn.config(bg="#90EE90"))
            self.root.after(0, lambda: self.log_message(f"IMotions Server Connected", "Success"))
        except:
            self.root.after(0, lambda: self._stop_spinner("imotions"))
            self.root.after(0, lambda: self.imotions_connect_btn.config(bg="#FFB6C6"))
            self.root.after(0, lambda: self.log_message(f"Error connecting to IMotions Server", "Error"))
            self.root.after(0, lambda: self.log_message(f"Check the IP/Port and try again","Info"))
            return
   
    def _start_spinner(self, module_name):
        """Start spinner animation for a module."""
        self.spinner_active[module_name] = True
        self._animate_spinner(module_name)

    def _stop_spinner(self, module_name):
        """Stop spinner animation for a module."""
        self.spinner_active[module_name] = False
        spinner_widgets = {
            "imotions": self.imotions_spinner,
            "triggerbox": self.triggerbox_spinner,
            "gps": self.gps_spinner,
            "smarteye": self.se_spinner,
            "h10": self.h10_spinner,
            "vivosmart5": self.vivosmart5_spinner
        }
        spinner_widgets[module_name].config(text="")

    def _animate_spinner(self, module_name):
        """Animate the spinner for a module."""
        if not self.spinner_active.get(module_name, False):
            return
        
        spinner_widgets = {
            "imotions": self.imotions_spinner,
            "triggerbox": self.triggerbox_spinner,
            "gps": self.gps_spinner,
            "smarteye": self.se_spinner,
            "h10": self.h10_spinner,
            "vivosmart5": self.vivosmart5_spinner
        }
        
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
        spinner_widgets[module_name].config(text=self.spinner_frames[self.spinner_index])
        
        # Schedule next animation frame
        self.root.after(100, lambda: self._animate_spinner(module_name))
        
    def disconnect(self):
        if self.smarteye_listener is not None:
            self.smarteye_listener.stop()
        if self.gps_listener is not None:
            self.gps_listener.stop()
        if self.h10_listener is not None:
            self.h10_listener.stop()
        if self.vivosmart5_listener is not None:
            self.vivosmart5_listener.stop()

################################ Module Connect/Disconnect Methods #################################
    def connectTriggerBox(self):
        """Connect to Trigger Box module."""
        self._start_spinner("triggerbox")
        self.triggerbox_thread = threading.Thread(target=self.runTriggerBox)
        self.triggerbox_thread.start()
    
    def disconnectTriggerBox(self):
        """Disconnect from Trigger Box module."""
        if self.triggerbox_listener is not None:
            self.triggerbox_listener.stop()
    
    def updateTriggerBoxStatus(self):
        """Update Trigger Box status indicator based on listener state."""
        if self.triggerbox_listener is not None and hasattr(self.triggerbox_listener, 'is_connected') and self.triggerbox_listener.is_connected():
            self.triggerbox_status.config(text="🟢", foreground="green")
        else:
            self.triggerbox_status.config(text="⚫", foreground="gray")
    
    def connectGPS(self):
        """Connect to GPS module."""
        self._start_spinner("gps")
        self.gps_thread = threading.Thread(target=self.runGPS)
        self.gps_thread.start()
    
    def disconnectGPS(self):
        """Disconnect from GPS module."""
        if self.gps_listener is not None:
            self.gps_listener.stop()
    
    def updateGPSStatus(self):
        """Update GPS status indicator based on listener state."""
        if self.gps_listener is not None and hasattr(self.gps_listener, 'is_connected') and self.gps_listener.is_connected():
            self.gps_status.config(text="🟢", foreground="green")
        else:
            self.gps_status.config(text="⚫", foreground="gray")
    
    def connectSmartEye(self):
        """Connect to SmartEye module."""
        self._start_spinner("smarteye")
        self.se_thread = threading.Thread(target=self.runSmartEye)
        self.se_thread.start()
    
    def disconnectSmartEye(self):
        """Disconnect from SmartEye module."""
        if self.smarteye_listener is not None:
            self.smarteye_listener.stop()
    
    def updateSmartEyeStatus(self):
        """Update SmartEye status indicator based on listener state."""
        if self.smarteye_listener is not None and hasattr(self.smarteye_listener, 'is_connected') and self.smarteye_listener.is_connected():
            self.se_status.config(text="🟢", foreground="green")
        else:
            self.se_status.config(text="⚫", foreground="gray")
    
    def connectH10(self):
        """Connect to Polar H10 module."""
        self._start_spinner("h10")
        self.h10_thread = threading.Thread(target=self.runH10)
        self.h10_thread.start()
    
    def disconnectH10(self):
        """Disconnect from Polar H10 module."""
        if self.h10_listener is not None:
            self.h10_listener.stop()
    
    def updateH10Status(self):
        """Update Polar H10 status indicator based on listener state."""
        if self.h10_listener is not None and self.h10_listener.is_connected():
            self.h10_status.config(text="🟢", foreground="green")
        else:
            self.h10_status.config(text="⚫", foreground="gray")
    
    def connectVivosmart5(self):
        """Connect to Vivosmart 5 module."""
        self._start_spinner("vivosmart5")
        self.vivosmart5_thread = threading.Thread(target=self.runVivosmart5)
        self.vivosmart5_thread.start()
    
    def disconnectVivosmart5(self):
        """Disconnect from Vivosmart 5 module."""
        if self.vivosmart5_listener is not None:
            self.vivosmart5_listener.stop()
    
    def updateVivosmart5Status(self):
        """Update Garmin Vivosmart5 status indicator based on listener state."""
        if self.vivosmart5_listener is not None and self.vivosmart5_listener.is_connected():
            self.vivosmart5_status.config(text="🟢", foreground="green")
        else:
            self.vivosmart5_status.config(text="⚫", foreground="gray")

################################ Runners #################################################################    
    def runSmartEye(self):
        se_server_port = int(self.se_port_entry.get())
        self.smarteye_listener = SEListener(se_server_port, self.stream)
        self.smarteye_listener.register_status_callback(self._create_status_update_callback(self.updateSmartEyeStatus))
        self.smarteye_listener.register_message_callback(self._create_message_callback("smarteye"))
        self.smarteye_listener.connect()
        self.smarteye_listener.start()
    
    def runGPS(self):
        self.gps_listener = GPSListener(self.gps_com, self.stream)
        self.gps_listener.register_status_callback(self._create_status_update_callback(self.updateGPSStatus))
        self.gps_listener.register_message_callback(self._create_message_callback("gps"))
        self.gps_listener.connect()
        self.gps_listener.start()
    
    def runTriggerBox(self):
        self.triggerbox_listener = TriggerBoxListener(self.triggerbox_triggers, self.triggerbox_com, self.stream)
        self.triggerbox_listener.register_status_callback(self._create_status_update_callback(self.updateTriggerBoxStatus))
        self.triggerbox_listener.register_message_callback(self._create_message_callback("triggerbox"))
        self.triggerbox_listener.connect()
        self.triggerbox_listener.start()
    
    def runH10(self):
        self.h10_listener = H10Listener(self.stream)
        self.h10_listener.register_status_callback(self._create_status_update_callback(self.updateH10Status))
        self.h10_listener.register_message_callback(self._create_message_callback("h10"))
        self.h10_listener.connect()
        if self.h10_listener.device:
            self.h10_listener.start()
    
    def runVivosmart5(self):
        self.vivosmart5_listener = Vivosmart5Listener(self.stream, address=self.vivosmart5_address)
        self.vivosmart5_listener.register_status_callback(self._create_status_update_callback(self.updateVivosmart5Status))
        self.vivosmart5_listener.register_message_callback(self._create_message_callback("vivosmart5"))
        self.vivosmart5_listener.connect()
        if self.vivosmart5_listener.device:
            self.vivosmart5_listener.start()
#####################################################################################################

if __name__ == "__main__":
     imotions_integrator = IMotionsIntegrator()