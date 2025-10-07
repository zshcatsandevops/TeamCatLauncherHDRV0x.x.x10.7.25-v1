import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import json
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import hashlib
import configparser
import ssl
import certifi
import tarfile  # Added for tar extraction

# Define constants for directories and URLs
MINECRAFT_DIR = os.path.expanduser("~/.minecraft")
VERSIONS_DIR = os.path.join(MINECRAFT_DIR, "versions")
JAVA_DIR = os.path.expanduser("~/.futureclient/java")
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
WURST_REPO = "https://github.com/Wurst-Imperium/Wurst7.git"  # Open-source hacked client base (ethical, non-cracked)

# Define theme dictionaries - Future Client red accents
DARK_THEME = {
    'bg': '#2c2c2c',
    'sidebar': '#1e1e1e',
    'accent': '#ff0000',
    'accent_light': '#ff4d4d',
    'text': '#ffffff',
    'text_secondary': '#b0b0b0',
    'button': '#ff0000',
    'button_hover': '#ff4d4d',
    'input_bg': '#3a3a3a',
    'header_bg': '#1a1a1a',
    'tab_active': '#ff0000',
    'tab_inactive': '#2a2a2a'
}

LIGHT_THEME = {
    'bg': '#f0f0f0',
    'sidebar': '#e0e0e0',
    'accent': '#ff0000',
    'accent_light': '#ff4d4d',
    'text': '#000000',
    'text_secondary': '#555555',
    'button': '#ff0000',
    'button_hover': '#ff4d4d',
    'input_bg': '#ffffff',
    'header_bg': '#d0d0d0',
    'tab_active': '#ff0000',
    'tab_inactive': '#e0e0e0'
}

SYSTEM_THEME = LIGHT_THEME

# Cheat modules config (108+ features, categorized like Future Client, adapted for Wurst-like powers)
CHEAT_MODULES = {
    "Combat": [
        "AntiBots", "Aura", "AutoArmor", "AutoBow", "AutoCrystal", "AutoEat", "AutoMine",
        "AutoPot", "AutoTotem", "AutoTrap", "AutoWeb", "BowAimbot", "Criticals", "CrystalAura",
        "FastBow", "Hitboxes", "KillAura", "NoHitDelay", "Offhand", "Reach", "SPush", "TargetStrafe",
        "Velocity", "WTap"
    ],
    "Render": [
        "AntiBlind", "AntiFog", "BlockESP", "BlockHighlight", "Breadcrumbs", "CameraClip",
        "ChestESP", "CityESP", "ESP", "ExtendedBlockReach", "Fullbright", "GlowESP", "HoleESP",
        "ItemESP", "NameTags", "NoRender", "PlayerESP", "StorageESP", "Tracers", "ViewModel",
        "XRay"
    ],
    "Movement": [
        "AirJump", "AirStuck", "AutoWalk", "BoatFly", "ElytraFly", "EntitySpeed", "Fly",
        "HighJump", "IceSpeed", "Jesus", "LongJump", "NoFall", "NoSlow", "Parkour", "SafeWalk",
        "Scaffold", "Speed", "Spider", "Sprint", "Step", "Strafe", "Swim", "VelocityNaN",
        "VClip"
    ],
    "Player": [
        "AntiHunger", "AutoFish", "AutoTool", "Blink", "Criticals", "Derp", "FakeLag",
        "FakePlayer", "FastPlace", "Freecam", "InventoryWalk", "NoClip", "NoRotate",
        "Phase", "SkinDerp"
    ],
    "World": [
        "AutoBuild", "AutoFarm", "AutoPlace", "Baritone", "BuildHeight", "ChestStealer",
        "FastPlace", "MultiTask", "NewChunks", "NoWeather", "Nuker", "Scaffold", "Timer"
    ],
    "Misc": [
        "AccountManager", "AltLogin", "AutoGG", "AutoReconnect", "AutoRespawn", "ChatEncrypt",
        "ClickGUI", "Coords", "DiscordRPC", "FriendManager", "KeyMap", "Macro", "NameProtect",
        "Notifier", "OpenFolder", "PacketLogger", "Spammer", "ToggleChat", "XCarry"
    ]
}

class FutureClientLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Future Client Launcher 3.0")
        self.geometry("800x600")  # Bigger for cheat panels
        self.minsize(800, 600)
        self.current_theme = LIGHT_THEME
        self.configure(background=self.current_theme['bg'])
        self.versions = {}
        self.version_categories = {
            "Latest Release": [], "Latest Snapshot": [], "Release": [], "Snapshot": [],
            "Old Beta": [], "Old Alpha": []
        }
        self.cheat_config = self.load_cheat_config()
        
        self.setup_ssl_context()
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.init_ui()
        self.update_theme()
        self.after(100, self.load_version_manifest)

    def load_cheat_config(self):
        config_path = os.path.join(MINECRAFT_DIR, "future_cheats.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {cat: {mod: False for mod in mods} for cat, mods in CHEAT_MODULES.items()}

    def save_cheat_config(self):
        config_path = os.path.join(MINECRAFT_DIR, "future_cheats.json")
        with open(config_path, 'w') as f:
            json.dump(self.cheat_config, f, indent=2)

    def setup_ssl_context(self):
        try:
            self.ssl_context = ssl.create_default_context()
        except Exception:
            try:
                self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                self.ssl_context = ssl._create_unverified_context()

    def safe_urlopen(self, url):
        try:
            return urllib.request.urlopen(url, context=self.ssl_context)
        except Exception:
            try:
                return urllib.request.urlopen(url)
            except Exception:
                raise

    def update_theme(self):
        self.configure(background=self.current_theme['bg'])
        self.style.configure("TFrame", background=self.current_theme['bg'])
        self.style.configure("TLabel", background=self.current_theme['bg'], foreground=self.current_theme['text'])
        self.style.configure("TButton", 
                           background=self.current_theme['button'],
                           foreground=self.current_theme['text'],
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat',
                           font=("Arial", 10))
        self.style.map("TButton",
                      background=[('active', self.current_theme['button_hover']),
                                 ('pressed', self.current_theme['accent'])])
        
        self.style.configure("TCombobox", 
                           fieldbackground=self.current_theme['input_bg'],
                           background=self.current_theme['input_bg'],
                           foreground=self.current_theme['text'],
                           arrowcolor=self.current_theme['text'],
                           borderwidth=0,
                           font=("Arial", 10))
        
        self.style.configure("TScale", 
                           background=self.current_theme['bg'],
                           troughcolor=self.current_theme['input_bg'])
        
        self.style.configure("TNotebook", 
                           background=self.current_theme['header_bg'],
                           borderwidth=0)
        self.style.configure("TNotebook.Tab", 
                           background=self.current_theme['tab_inactive'],
                           foreground=self.current_theme['text_secondary'],
                           padding=[15, 5],
                           borderwidth=0,
                           font=("Arial", 10))
        self.style.map("TNotebook.Tab",
                      background=[('selected', self.current_theme['tab_active'])],
                      foreground=[('selected', self.current_theme['text'])])

        for widget in self.winfo_children():
            self._update_widget_theme(widget)

    def _update_widget_theme(self, widget):
        try:
            if isinstance(widget, tk.Frame):
                widget.configure(background=self.current_theme['bg'])
            elif isinstance(widget, tk.Label):
                widget.configure(background=self.current_theme['bg'], foreground=self.current_theme['text'])
            elif isinstance(widget, tk.Entry):
                try:
                    widget.configure(background=self.current_theme['input_bg'], foreground=self.current_theme['text'], 
                                   insertbackground=self.current_theme['text'])
                except tk.TclError:
                    pass
            elif isinstance(widget, tk.Button):
                widget.configure(background=self.current_theme['button'], foreground=self.current_theme['text'])
            elif isinstance(widget, tk.Checkbutton):
                widget.configure(background=self.current_theme['bg'], foreground=self.current_theme['text'], 
                               selectcolor=self.current_theme['sidebar'], 
                               activebackground=self.current_theme['bg'], 
                               activeforeground=self.current_theme['text'])
            elif isinstance(widget, tk.Listbox):
                widget.configure(background=self.current_theme['input_bg'], foreground=self.current_theme['text'], 
                               selectbackground=self.current_theme['accent'], 
                               selectforeground=self.current_theme['text'])
            elif isinstance(widget, tk.Scale):
                widget.configure(background=self.current_theme['bg'], foreground=self.current_theme['text'],
                               activebackground=self.current_theme['accent'],
                               troughcolor=self.current_theme['input_bg'])
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self._update_widget_theme(child)

    def set_theme(self, theme_name):
        if theme_name == "Dark":
            self.current_theme = DARK_THEME
        elif theme_name == "Light":
            self.current_theme = LIGHT_THEME
        elif theme_name == "System":
            self.current_theme = SYSTEM_THEME
        self.update_theme()

    def init_ui(self):
        # Header
        header = tk.Frame(self, background=self.current_theme['header_bg'], height=40)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        # Header title
        title = tk.Label(header, text="Future Client Launcher", font=("Arial", 14, "bold"), 
                        background=self.current_theme['header_bg'], foreground=self.current_theme['text'])
        title.pack(side="left", padx=15, pady=10)
        
        # Header version
        version = tk.Label(header, text="3.0", font=("Arial", 10), 
                          background=self.current_theme['header_bg'], foreground=self.current_theme['text_secondary'])
        version.pack(side="right", padx=15, pady=10)
        
        # Theme selector
        theme_frame = tk.Frame(header, background=self.current_theme['header_bg'])
        theme_frame.pack(side="right", padx=10)
        theme_label = tk.Label(theme_frame, text="Theme:", font=("Arial", 10),
                              background=self.current_theme['header_bg'], foreground=self.current_theme['text_secondary'])
        theme_label.pack(side="left")
        theme_options = ["Dark", "Light", "System"]
        self.theme_var = tk.StringVar(value="Light")
        theme_menu = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=theme_options,
                                   state="readonly")
        theme_menu.set("Light")
        theme_menu.bind("<<ComboboxSelected>>", lambda e: self.set_theme(self.theme_var.get()))
        theme_menu.pack(side="left", padx=5)
        
        # Main container
        main_container = tk.Frame(self, background=self.current_theme['bg'])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Game settings
        left_panel = tk.Frame(main_container, background=self.current_theme['sidebar'], width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Game version selection
        version_frame = tk.Frame(left_panel, background=self.current_theme['sidebar'])
        version_frame.pack(fill="x", padx=15, pady=15)
        
        tk.Label(version_frame, text="VERSION", font=("Arial", 9, "bold"), 
                background=self.current_theme['sidebar'], foreground=self.current_theme['text_secondary']).pack(anchor="w")
        
        self.category_combo = ttk.Combobox(version_frame, values=list(self.version_categories.keys()),
                                         state="readonly")
        self.category_combo.pack(fill="x", pady=(5, 0))
        self.category_combo.set("Latest Release")
        self.category_combo.bind("<<ComboboxSelected>>", self.update_version_list)

        self.version_combo = ttk.Combobox(version_frame, state="readonly")
        self.version_combo.pack(fill="x", pady=5)

        # Account settings
        account_frame = tk.Frame(left_panel, background=self.current_theme['sidebar'])
        account_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(account_frame, text="ACCOUNT", font=("Arial", 9, "bold"), 
                background=self.current_theme['sidebar'], foreground=self.current_theme['text_secondary']).pack(anchor="w")
        
        self.username_input = tk.Entry(account_frame, font=("Arial", 10), background=self.current_theme['input_bg'],
                                     foreground=self.current_theme['text'], insertbackground=self.current_theme['text'], 
                                     bd=0, relief="flat")
        self.username_input.pack(fill="x", pady=(5, 0))
        self.username_input.insert(0, "Player")
        self.username_input.bind("<FocusIn>", lambda e: self.username_input.delete(0, tk.END) 
                               if self.username_input.get() == "Player" else None)

        # RAM settings
        ram_frame = tk.Frame(left_panel, background=self.current_theme['sidebar'])
        ram_frame.pack(fill="x", padx=15, pady=10)
        
        ram_header = tk.Frame(ram_frame, background=self.current_theme['sidebar'])
        ram_header.pack(fill="x")
        
        tk.Label(ram_header, text="RAM", font=("Arial", 9, "bold"),
                background=self.current_theme['sidebar'], foreground=self.current_theme['text_secondary']).pack(side="left")
        
        self.ram_value_label = tk.Label(ram_header, text="4 GB", font=("Arial", 9),
                                      background=self.current_theme['sidebar'], foreground=self.current_theme['text'])
        self.ram_value_label.pack(side="right")

        self.ram_scale = tk.Scale(ram_frame, from_=1, to=16, orient="horizontal",
                                background=self.current_theme['sidebar'], foreground=self.current_theme['text'],
                                activebackground=self.current_theme['accent'],
                                highlightthickness=0, bd=0,
                                troughcolor=self.current_theme['input_bg'],
                                sliderrelief="flat",
                                command=lambda v: self.ram_value_label.config(text=f"{int(float(v))} GB"))
        self.ram_scale.set(4)
        self.ram_scale.pack(fill="x")

        # Skin button
        skin_button = ttk.Button(left_panel, text="Change Skin", command=self.select_skin)
        skin_button.pack(padx=15, pady=10, fill="x")

        # Launch button - Future style
        launch_button = ttk.Button(left_panel, text="INJECT & PLAY", command=self.prepare_and_launch)
        launch_button.pack(side="bottom", padx=15, pady=15, fill="x")

        # Right panel - Tabs and content
        right_panel = tk.Frame(main_container, background=self.current_theme['bg'])
        right_panel.pack(side="left", fill="both", expand=True)

        # Create notebook for tabs
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill="both", expand=True)

        # Presets tab (formerly Mod-packs)
        presets_tab = ttk.Frame(notebook)
        notebook.add(presets_tab, text="Presets")

        # Cheats tab (formerly Mods)
        cheats_tab = ttk.Frame(notebook)
        notebook.add(cheats_tab, text="Cheats")

        # Resource Packs tab
        resourcepacks_tab = ttk.Frame(notebook)
        notebook.add(resourcepacks_tab, text="Resource Packs")

        # Settings tab
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text="Settings")

        # Populate Presets tab
        presets_content = tk.Frame(presets_tab, background=self.current_theme['bg'])
        presets_content.pack(fill="both", expand=True, padx=10, pady=10)

        presets_title = tk.Label(presets_content, text="FUTURE PRESETS", 
                             font=("Arial", 16, "bold"), background=self.current_theme['bg'], 
                             foreground=self.current_theme['accent'])
        presets_title.pack(anchor="w", pady=(0, 15))

        ttk.Button(presets_content, text="Load PvP Preset", command=lambda: self.load_preset("pvp")).pack(pady=5)
        ttk.Button(presets_content, text="Load Anarchy Preset", command=lambda: self.load_preset("anarchy")).pack(pady=5)
        ttk.Button(presets_content, text="Save Current", command=self.save_cheat_config).pack(pady=5)

        # Populate Cheats tab with scrollable categories
        cheats_content = tk.Frame(cheats_tab, background=self.current_theme['bg'])
        cheats_content.pack(fill="both", expand=True, padx=10, pady=10)
        cheats_title = tk.Label(cheats_content, text="FUTURE CHEATS (108+ Modules)", font=("Arial", 12, "bold"), 
                 background=self.current_theme['bg'], foreground=self.current_theme['text'])
        cheats_title.pack(anchor="w")

        canvas = tk.Canvas(cheats_content, background=self.current_theme['bg'])
        scrollbar = ttk.Scrollbar(cheats_content, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, background=self.current_theme['bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for cat, mods in CHEAT_MODULES.items():
            cat_frame = tk.LabelFrame(scrollable_frame, text=cat, font=("Arial", 10, "bold"),
                                      background=self.current_theme['bg'], foreground=self.current_theme['accent'],
                                      bd=2, relief="groove")
            cat_frame.pack(fill="x", padx=5, pady=5)

            for mod in mods:
                var = tk.BooleanVar(value=self.cheat_config.get(cat, {}).get(mod, False))
                cb = tk.Checkbutton(cat_frame, text=mod, variable=var,
                                    background=self.current_theme['bg'], foreground=self.current_theme['text'], 
                                    selectcolor=self.current_theme['sidebar'],
                                    activebackground=self.current_theme['bg'], 
                                    activeforeground=self.current_theme['text'],
                                    command=lambda c=cat, m=mod, v=var: self.toggle_cheat(c, m, v.get()))
                cb.pack(anchor="w", padx=10)

        # Add build button for powers (cheats) - non-Mojang only (offline mode)
        ttk.Button(scrollable_frame, text="Build Powers JAR (Non-Mojang)", command=self.build_powers_jar).pack(pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Resource Packs tab (placeholder)
        resourcepacks_content = tk.Frame(resourcepacks_tab, background=self.current_theme['bg'])
        resourcepacks_content.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(resourcepacks_content, text="RESOURCE PACKS PLACEHOLDER", font=("Arial", 12, "bold"), 
                 background=self.current_theme['bg'], foreground=self.current_theme['text']).pack(anchor="w")

        # Settings tab (placeholder)
        settings_content = tk.Frame(settings_tab, background=self.current_theme['bg'])
        settings_content.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(settings_content, text="SETTINGS PLACEHOLDER", font=("Arial", 12, "bold"), 
                 background=self.current_theme['bg'], foreground=self.current_theme['text']).pack(anchor="w")

    def toggle_cheat(self, cat, mod, enabled):
        if cat not in self.cheat_config:
            self.cheat_config[cat] = {}
        self.cheat_config[cat][mod] = enabled
        self.save_cheat_config()

    def load_preset(self, preset):
        presets = {"pvp": {"Combat": {m: True for m in ["Aura", "CrystalAura"]}, "Movement": {m: True for m in ["Speed"]}},
                   "anarchy": {"Combat": {m: True for m in CHEAT_MODULES["Combat"]}, "World": {m: True for m in ["Baritone"]}}}
        if preset in presets:
            self.cheat_config.update(presets[preset])
            self.save_cheat_config()
            messagebox.showinfo("Preset Loaded", f"{preset.capitalize()} preset activated!")

    def build_powers_jar(self):
        # Clone open-source base, build JAR with cheats enabled via config (non-Mojang/offline only)
        build_dir = os.path.join(MINECRAFT_DIR, "wurst-build")
        if not os.path.exists(build_dir):
            try:
                subprocess.call(['git', 'clone', WURST_REPO, build_dir])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clone base: {e}")
                return
        os.chdir(build_dir)
        try:
            subprocess.call(['gradle', 'build'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to build: {e}")
            return
        jar_path = os.path.join(build_dir, "build/libs/Wurst7.jar")  # Adjust for actual output
        target_version = self.version_combo.get()
        if target_version:
            vanilla_jar = os.path.join(VERSIONS_DIR, target_version, f"{target_version}.jar")
            merged_jar = os.path.join(VERSIONS_DIR, target_version, "minecraft.jar")
            if os.path.exists(vanilla_jar):
                shutil.copy(vanilla_jar, merged_jar)
                with zipfile.ZipFile(merged_jar, 'a') as vanilla_zip:
                    with zipfile.ZipFile(jar_path, 'r') as wurst_zip:
                        for file in wurst_zip.namelist():
                            vanilla_zip.writestr(file, wurst_zip.read(file))  # Merge all, including classes for cheats inside
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        messagebox.showinfo("Powers Built", "Powers JAR built and merged into minecraft.jar for non-Mojang play!")

    def update_version_list(self, event=None):
        category = self.category_combo.get()
        self.version_combo['values'] = self.version_categories[category]
        if self.version_combo['values']:
            self.version_combo.current(0)

    def load_version_manifest(self):
        try:
            with self.safe_urlopen(VERSION_MANIFEST_URL) as url:
                manifest = json.loads(url.read().decode())
                
                for category in self.version_categories:
                    self.version_categories[category] = []
                
                latest_release = None
                latest_snapshot = None
                
                for v in manifest["versions"]:
                    if self.is_future_supported(v["id"]):
                        self.versions[v["id"]] = v["url"]
                        
                        if v["id"] == manifest["latest"]["release"]:
                            latest_release = v["id"]
                            self.version_categories["Latest Release"].append(v["id"])
                        elif v["id"] == manifest["latest"]["snapshot"]:
                            latest_snapshot = v["id"]
                            self.version_categories["Latest Snapshot"].append(v["id"])
                        
                        if v["type"] == "release":
                            if v["id"] != latest_release:
                                self.version_categories["Release"].append(v["id"])
                        elif v["type"] == "snapshot":
                            if v["id"] != latest_snapshot:
                                self.version_categories["Snapshot"].append(v["id"])
                        elif v["type"] == "old_beta":
                            self.version_categories["Old Beta"].append(v["id"])
                        elif v["type"] == "old_alpha":
                            self.version_categories["Old Alpha"].append(v["id"])
                
                self.update_version_list()
        except Exception:
            pass  # Silent, as per pr files=off

    def is_future_supported(self, version_id):
        # Future supports 1.8.9+
        parts = version_id.split('.')
        if len(parts) < 2:
            return False
        major = int(parts[0])
        minor = int(parts[1])
        return major > 1 or (major == 1 and minor >= 8)

    def is_java_installed(self, required_version="21"):
        try:
            result = subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            output = result.stderr
            match = re.search(r'version "(\d+)', output)
            if match:
                major_version = int(match.group(1))
                return major_version >= int(required_version)
            return False
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    def install_java_if_needed(self):
        if self.is_java_installed():
            return True
        
        system = platform.system()
        if system == "Windows":
            java_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_windows_hotspot_21.0.5_11.zip"
            archive_path = os.path.join(JAVA_DIR, "openjdk.zip")
        elif system == "Linux":
            java_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_linux_hotspot_21.0.5_11.tar.gz"
            archive_path = os.path.join(JAVA_DIR, "openjdk.tar.gz")
        elif system == "Darwin":
            java_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_mac_hotspot_21.0.5_11.tar.gz"
            archive_path = os.path.join(JAVA_DIR, "openjdk.tar.gz")
        else:
            messagebox.showerror("Error", "Unsupported OS")
            return False

        os.makedirs(JAVA_DIR, exist_ok=True)

        try:
            response = self.safe_urlopen(java_url)
            with open(archive_path, 'wb') as f:
                f.write(response.read())
        except Exception:
            try:
                temp_context = ssl._create_unverified_context()
                response = urllib.request.urlopen(java_url, context=temp_context)
                with open(archive_path, 'wb') as f:
                    f.write(response.read())
            except Exception:
                messagebox.showerror("Error", "Failed to download Java 21. Please check your internet connection or install Java manually.")
                return False

        try:
            if system == "Windows":
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(JAVA_DIR)
            else:
                with tarfile.open(archive_path, "r:gz") as tar_ref:
                    tar_ref.extractall(JAVA_DIR)
                java_bin_dir = os.path.join(JAVA_DIR, "jdk-21.0.5+11", "bin")
                for file in os.listdir(java_bin_dir):
                    file_path = os.path.join(java_bin_dir, file)
                    if os.path.isfile(file_path):
                        os.chmod(file_path, 0o755)
            
            os.remove(archive_path)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract Java: {e}")
            return False

    def select_skin(self):
        file_path = filedialog.askopenfilename(
            title="Select Skin PNG", 
            filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                skin_dest = os.path.join(MINECRAFT_DIR, "skins")
                os.makedirs(skin_dest, exist_ok=True)
                shutil.copy(file_path, os.path.join(skin_dest, "custom_skin.png"))
                messagebox.showinfo("Skin Applied", "Skin applied successfully! Note: This may require a mod to apply in-game.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy skin: {e}")

    @staticmethod
    def verify_file(file_path, expected_sha1):
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha1(f.read()).hexdigest()
            return file_hash == expected_sha1
        except Exception:
            return False

    def safe_download_file(self, url, file_path, expected_sha1=None):
        try:
            response = self.safe_urlopen(url)
            with open(file_path, 'wb') as f:
                f.write(response.read())
            
            if expected_sha1 and not self.verify_file(file_path, expected_sha1):
                return False
            return True
        except Exception:
            try:
                temp_context = ssl._create_unverified_context()
                response = urllib.request.urlopen(url, context=temp_context)
                with open(file_path, 'wb') as f:
                    f.write(response.read())
                
                if expected_sha1 and not self.verify_file(file_path, expected_sha1):
                    return False
                return True
            except Exception:
                return False

    def download_version_files(self, version_id, version_url):
        version_dir = os.path.join(VERSIONS_DIR, version_id)
        os.makedirs(version_dir, exist_ok=True)

        # Download vanilla json and jar
        version_json_path = os.path.join(version_dir, f"{version_id}.json")
        try:
            with self.safe_urlopen(version_url) as url:
                data = json.loads(url.read().decode())
                with open(version_json_path, "w") as f:
                    json.dump(data, f, indent=2)
        except Exception:
            try:
                temp_context = ssl._create_unverified_context()
                with urllib.request.urlopen(version_url, context=temp_context) as url:
                    data = json.loads(url.read().decode())
                    with open(version_json_path, "w") as f:
                        json.dump(data, f, indent=2)
            except Exception:
                messagebox.showerror("Error", f"Failed to download version {version_id} JSON.")
                return

        try:
            jar_url = data["downloads"]["client"]["url"]
            jar_path = os.path.join(version_dir, "minecraft.jar")
            expected_sha1 = data["downloads"]["client"]["sha1"]
            
            if not os.path.exists(jar_path) or not self.verify_file(jar_path, expected_sha1):
                if not self.safe_download_file(jar_url, jar_path, expected_sha1):
                    messagebox.showerror("Error", f"Failed to download or verify version {version_id} JAR.")
                    return
        except KeyError:
            messagebox.showerror("Error", f"Version {version_id} is missing client JAR information.")
            return

        # Build Wurst and merge into minecraft.jar
        self.build_powers_jar(jar_path)

        current_os = platform.system().lower()
        if current_os == "darwin":
            current_os = "osx"

        libraries_dir = os.path.join(MINECRAFT_DIR, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)
        natives_dir = os.path.join(version_dir, "natives")
        os.makedirs(natives_dir, exist_ok=True)

        for lib in data.get("libraries", []):
            if self.is_library_allowed(lib, current_os):
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    lib_url = lib["downloads"]["artifact"]["url"]
                    lib_path = os.path.join(libraries_dir, lib["downloads"]["artifact"]["path"])
                    os.makedirs(os.path.dirname(lib_path), exist_ok=True)
                    expected_sha1 = lib["downloads"]["artifact"]["sha1"]
                    if not os.path.exists(lib_path) or not self.verify_file(lib_path, expected_sha1):
                        if not self.safe_download_file(lib_url, lib_path, expected_sha1):
                            pass

                if "natives" in lib and current_os in lib["natives"]:
                    classifier = lib["natives"][current_os]
                    if "downloads" in lib and "classifiers" in lib["downloads"] and classifier in lib["downloads"]["classifiers"]:
                        native_url = lib["downloads"]["classifiers"][classifier]["url"]
                        native_path = os.path.join(natives_dir, f"{classifier}.jar")
                        expected_sha1 = lib["downloads"]["classifiers"][classifier]["sha1"]
                        if not os.path.exists(native_path) or not self.verify_file(native_path, expected_sha1):
                            if self.safe_download_file(native_url, native_path, expected_sha1):
                                try:
                                    with zipfile.ZipFile(native_path, "r") as zip_ref:
                                        zip_ref.extractall(natives_dir)
                                    os.remove(native_path)
                                except Exception:
                                    pass

    def modify_options_txt(self, target_fps=60):
        options_path = os.path.join(MINECRAFT_DIR, "options.txt")
        options = {}
        if os.path.exists(options_path):
            try:
                with open(options_path, "r") as f:
                    for line in f:
                        parts = line.strip().split(":", 1)
                        if len(parts) == 2:
                            options[parts[0]] = parts[1]
            except Exception:
                pass

        options['maxFps'] = str(target_fps)
        options['enableVsync'] = 'false'

        try:
            with open(options_path, "w") as f:
                for key, value in options.items():
                    f.write(f"{key}:{value}\n")
        except Exception:
            pass

    def is_library_allowed(self, lib, current_os):
        if "rules" not in lib:
            return True
        allowed = False
        for rule in lib["rules"]:
            if rule["action"] == "allow":
                if "os" not in rule or (isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os):
                    allowed = True
            elif rule["action"] == "disallow":
                if "os" in rule and isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os:
                    allowed = False
        return allowed

    def evaluate_rules(self, rules, current_os):
        if not rules:
            return True
        allowed = False
        for rule in rules:
            if "features" in rule:
                continue
            if rule["action"] == "allow":
                if "os" not in rule or (isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os):
                    allowed = True
            elif rule["action"] == "disallow":
                if "os" in rule and isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os:
                    allowed = False
        return allowed

    def generate_offline_uuid(self, username):
        offline_prefix = "OfflinePlayer:"
        hash_value = hashlib.md5((offline_prefix + username).encode('utf-8')).hexdigest()
        uuid_str = f"{hash_value[:8]}-{hash_value[8:12]}-{hash_value[12:16]}-{hash_value[16:20]}-{hash_value[20:32]}"
        return uuid_str

    def build_launch_command(self, version, username, ram):
        version_dir = os.path.join(VERSIONS_DIR, version)
        json_path = os.path.join(version_dir, f"{version}.json")

        try:
            with open(json_path, "r") as f:
                version_data = json.load(f)
        except Exception:
            messagebox.showerror("Error", f"Cannot read version {version} JSON.")
            return []

        current_os = platform.system().lower()
        if current_os == "darwin":
            current_os = "osx"

        main_class = version_data.get("mainClass", "net.minecraft.client.main.Main")
        libraries_dir = os.path.join(MINECRAFT_DIR, "libraries")
        natives_dir = os.path.join(version_dir, "natives")
        jar_path = os.path.join(version_dir, "minecraft.jar")  # Merged jar with cheats inside
        classpath = [jar_path]

        for lib in version_data.get("libraries", []):
            if "downloads" in lib and "artifact" in lib["downloads"]:
                lib_path = os.path.join(libraries_dir, lib["downloads"]["artifact"]["path"])
                if os.path.exists(lib_path):
                    classpath.append(lib_path)

        classpath_str = ";".join(classpath) if platform.system() == "Windows" else ":".join(classpath)
        
        if self.is_java_installed():
            java_path = "java"
        else:
            java_exe = "java.exe" if platform.system() == "Windows" else "java"
            java_path = os.path.join(JAVA_DIR, "jdk-21.0.5+11", "bin", java_exe)
            if not os.path.exists(java_path):
                java_path = "java"

        command = [java_path, f"-Xmx{ram}G"]

        jvm_args = []
        if "arguments" in version_data and "jvm" in version_data["arguments"]:
            for arg in version_data["arguments"]["jvm"]:
                if isinstance(arg, str):
                    jvm_args.append(arg)
                elif isinstance(arg, dict) and "rules" in arg and "value" in arg:
                    if self.evaluate_rules(arg["rules"], current_os):
                        if isinstance(arg["value"], list):
                            jvm_args.extend(arg["value"])
                        else:
                            jvm_args.append(arg["value"])

        if platform.system() == "Darwin" and "-XstartOnFirstThread" not in jvm_args:
            jvm_args.append("-XstartOnFirstThread")

        if not any("-Djava.library.path" in arg for arg in jvm_args):
            jvm_args.append(f"-Djava.library.path={natives_dir}")

        command.extend(jvm_args)

        game_args = []
        if "arguments" in version_data and "game" in version_data["arguments"]:
            for arg in version_data["arguments"]["game"]:
                if isinstance(arg, str):
                    game_args.append(arg)
                elif isinstance(arg, dict) and "rules" in arg and "value" in arg:
                    if self.evaluate_rules(arg["rules"], current_os):
                        if isinstance(arg["value"], list):
                            game_args.extend(arg["value"])
                        else:
                            game_args.append(arg["value"])
        elif "minecraftArguments" in version_data:
            game_args = version_data["minecraftArguments"].split()

        uuid = self.generate_offline_uuid(username)

        replacements = {
            "${auth_player_name}": username,
            "${version_name}": version,
            "${game_directory}": MINECRAFT_DIR,
            "${assets_root}": os.path.join(MINECRAFT_DIR, "assets"),
            "${assets_index_name}": version_data.get("assetIndex", {}).get("id", "legacy"),
            "${auth_uuid}": uuid,
            "${auth_access_token}": "0",
            "${user_type}": "legacy",
            "${version_type}": version_data.get("type", "release"),
            "${user_properties}": "{}",
            "${quickPlayRealms}": "",
        }

        def replace_placeholders(arg):
            for key, value in replacements.items():
                arg = arg.replace(key, value)
            return arg

        game_args = [replace_placeholders(arg) for arg in game_args]
        jvm_args = [replace_placeholders(arg) for arg in jvm_args]

        # Add cheat config flag for "injection"
        cheats_str = json.dumps(self.cheat_config).replace(' ', '_')
        game_args.append(f"--futureCheats={cheats_str}")

        command.extend(["-cp", classpath_str, main_class] + game_args)
        return command

    def prepare_and_launch(self):
        self.save_cheat_config()  # Save cheats before launch
        self.set_hud_keybind()  # Pre-set HUD on CTRL
        if not self.install_java_if_needed():
            messagebox.showerror("Error", "Failed to install Java. Please install Java 21 manually.")
            return
            
        self.modify_options_txt(target_fps=60)
        self.download_and_launch()

    def set_hud_keybind(self):
        wurst_dir = os.path.join(MINECRAFT_DIR, "wurst")
        os.makedirs(wurst_dir, exist_ok=True)
        keybinds_path = os.path.join(wurst_dir, "keybinds.json")
        keybinds = {"ClickGUI": "KEY_LCONTROL"}  # Set HUD (ClickGUI) to CTRL
        try:
            with open(keybinds_path, "w") as f:
                json.dump(keybinds, f, indent=2)
        except Exception:
            pass

    def download_and_launch(self):
        version = self.version_combo.get()
        if not version:
            messagebox.showerror("Error", "No version selected.")
            return

        username = self.username_input.get() or "Steve"
        ram = int(self.ram_scale.get())
        version_url = self.versions.get(version)

        if not version_url:
            messagebox.showerror("Error", f"Version {version} URL not found.")
            return

        self.download_version_files(version, version_url)

        launch_cmd = self.build_launch_command(version, username, ram)
        if not launch_cmd:
            return

        try:
            subprocess.Popen(launch_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Minecraft: {e}")

if __name__ == "__main__":
    app = FutureClientLauncher()
    app.mainloop()
