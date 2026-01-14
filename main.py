import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import json
import os
from pathlib import Path

# Windows-specific registry access for detecting system theme
try:
    import winreg
except Exception:
    winreg = None

class WinGetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WinGet Package Installer")
        self.root.geometry("900x700")
        
        # Menu Bar (keep native menu for keyboard shortcuts)
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=lambda: self.exit_app())
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        # App-style top menu bar (Windows 11-like)
        # Keep theme/state variables used by the menu
        self.topmost_var = tk.BooleanVar(value=False)
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.theme_var = tk.StringVar(value='dark' if self.dark_mode_var.get() else 'light')
        self.follow_system_var = tk.BooleanVar(value=False)
        self.package_manager_var = tk.StringVar(value='winget')

        # Window menu moved to native menubar (replaces app-style top bar)
        window_menu = tk.Menu(menubar, tearoff=0)
        window_menu.add_checkbutton(label='Always on Top', variable=self.topmost_var, command=self.toggle_topmost)
        window_menu.add_radiobutton(label='Light', variable=self.theme_var, value='light', command=lambda: self._set_theme_from_menu('light'))
        window_menu.add_radiobutton(label='Dark', variable=self.theme_var, value='dark', command=lambda: self._set_theme_from_menu('dark'))
        window_menu.add_separator()
        window_menu.add_checkbutton(label='Follow System Theme', variable=self.follow_system_var, command=self.toggle_follow_system)
        window_menu.add_separator()
        window_menu.add_command(label='Refresh System Theme\tCtrl+R', command=self._refresh_system_theme)
        window_menu.add_command(label='Toggle Dark Mode\tCtrl+D', command=lambda: self._key_toggle_dark())
        menubar.add_cascade(label='Window', menu=window_menu)

        # Toolbar (Dark Mode toggle and Package Manager selector)
        toolbar = ttk.Frame(self.root, padding="4")
        toolbar.pack(fill=tk.X, padx=10, pady=(5,0))
        self.toolbar_dark_chk = ttk.Checkbutton(toolbar, text="Dark Mode", variable=self.dark_mode_var, command=self._toolbar_toggle_dark)
        
        # Package Manager selector
        ttk.Label(toolbar, text="Package Manager:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Radiobutton(toolbar, text="WinGet", variable=self.package_manager_var, value='winget').pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toolbar, text="Chocolatey", variable=self.package_manager_var, value='chocolatey').pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Install Chocolatey", command=self.install_chocolatey).pack(side=tk.LEFT, padx=(20, 5))

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu) 
        # keyboard shortcut for Exit
        self.root.bind_all("<Control-q>", lambda e: self.exit_app())
        # keyboard shortcuts for Dark Mode and Refresh
        self.root.bind_all("<Control-d>", lambda e: self._key_toggle_dark())
        self.root.bind_all("<Control-r>", lambda e: self._refresh_system_theme())
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu) 
        # keyboard shortcut for Exit
        self.root.bind_all("<Control-q>", lambda e: self.exit_app())
        
        # Search Frame (hidden by default under Advanced options)
        self.search_frame = ttk.Frame(root, padding="10")
        # not packed by default
        
        ttk.Label(self.search_frame, text="Package ID:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        ttk.Entry(self.search_frame, textvariable=self.search_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.search_frame, text="Search", command=self.search_package).pack(side=tk.LEFT, padx=5)
        
        # Results Frame (hidden by default under Advanced options)
        self.results_frame = ttk.LabelFrame(root, text="Search Results", padding="10")
        # not packed by default
        
        self.results_text = scrolledtext.ScrolledText(self.results_frame, height=10, width=70)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Advanced Options (hide/install by ID)
        self.advanced_var = tk.BooleanVar(value=False)
        adv_chk = ttk.Checkbutton(root, text="Advanced options", variable=self.advanced_var, command=self.toggle_advanced)
        adv_chk.pack(anchor=tk.W, padx=10, pady=(5,0))
        
        # Install Frame (hidden by default; shows when Advanced options checked)
        self.install_frame = ttk.Frame(root, padding="10")
        ttk.Label(self.install_frame, text="Package ID to Install:").pack(side=tk.LEFT, padx=5)
        self.install_var = tk.StringVar()
        ttk.Entry(self.install_frame, textvariable=self.install_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.install_frame, text="Install", command=self.install_package).pack(side=tk.LEFT, padx=5)
        # (not packed by default)
        
        # Categories Frame
        self.categories_frame = ttk.LabelFrame(root, text="Categories", padding="10")
        self.categories_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.categories = {
            "Browsers": [
                ("Google Chrome", "Google.Chrome"),
                ("Firefox", "Mozilla.Firefox"),
                ("Microsoft Edge", "Microsoft.Edge"),
                ("Brave Browser", "Brave.Brave"),
                ("Zen Browser", "ZenBrowser.Zen"),
            ],
            "Development": [
                ("Visual Studio Code", "Microsoft.VisualStudioCode"),
                ("Git", "Git.Git"),
                ("Node.js", "OpenJS.NodeJS"),
            ],
            "Media": [
                ("VLC", "VideoLAN.VLC"),
                ("Spotify", "Spotify.Spotify"),
            ],
            "Gaming": [
                ("Steam", "Valve.Steam"),
                ("Epic Games Launcher", "EpicGames.EpicGameLauncher"),
                ("GOG Galaxy", "GOG.Galaxy"),
                ("Discord", "Discord.Discord"),
                ("OBS Studio", "OBSProject.OBSStudio"),
            ],
            "Utilities": [
                ("7-Zip", "7zip.7zip"),
                ("Notepad++", "Notepad++.Notepad++"),
            ],
        }
        
        cat_buttons_frame = ttk.Frame(self.categories_frame)
        cat_buttons_frame.pack(fill=tk.X)
        for cat in self.categories.keys():
            ttk.Button(cat_buttons_frame, text=cat, command=lambda c=cat: self.show_category(c)).pack(side=tk.LEFT, padx=5, pady=2) 
        
        # Category Apps Frame (shows apps for selected category)
        category_list_frame = ttk.LabelFrame(root, text="Category Apps", padding="10")
        category_list_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        self.apps_container = ttk.Frame(category_list_frame)
        self.apps_container.pack(fill=tk.X)
        # Show first category by default
        self.show_category(list(self.categories.keys())[0])
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(root, textvariable=self.status_var).pack(padx=10, pady=5)

        # Configuration path for storing user settings (per-user)
        local_appdata = os.getenv('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
        config_dir = Path(local_appdata) / 'WinGet Package Installer'
        config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = config_dir / 'settings.json'
        # Load persisted settings and apply theme (or follow system if configured)
        self.load_settings()
        if getattr(self, 'follow_system_var', None) and self.follow_system_var.get():
            self.toggle_follow_system()
        else:
            self.apply_theme(self.dark_mode_var.get())
    
    def search_package(self):
        query = self.search_var.get()
        if not query:
            messagebox.showwarning("Input Error", "Enter a package name")
            return
        
        self.status_var.set("Searching...")
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()
    
    def _search_thread(self, query):
        manager = self.package_manager_var.get()
        try:
            if manager == 'chocolatey':
                result = subprocess.run(
                    ["choco", "search", query],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:  # winget
                result = subprocess.run(
                    ["winget", "search", query],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, result.stdout)
            self.status_var.set("Search complete")
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Error: {str(e)}")
            self.status_var.set("Error")
    
    def install_package(self):
        package = self.install_var.get()
        if not package:
            messagebox.showwarning("Input Error", "Enter a package ID")
            return
        
        self.status_var.set(f"Installing {package}...")
        threading.Thread(target=self._install_thread, args=(package,), daemon=True).start()
    
    def _install_thread(self, package):
        manager = self.package_manager_var.get()
        try:
            if manager == 'chocolatey':
                subprocess.run(
                    ["choco", "install", package, "-y"],
                    check=True,
                    timeout=300
                )
            else:  # winget
                subprocess.run(
                    ["winget", "install", "-e", "--id", package, "--accept-package-agreements", "--accept-source-agreements"],
                    check=True,
                    timeout=300
                )
            self.status_var.set(f"✓ {package} installed successfully")
            messagebox.showinfo("Success", f"{package} installed successfully!")
        except subprocess.CalledProcessError:
            self.status_var.set("Installation failed")
            messagebox.showerror("Error", f"Failed to install {package}")
        except Exception as e:
            self.status_var.set("Error")
            messagebox.showerror("Error", str(e))

    def toggle_advanced(self):
        # Show or hide advanced controls: manual ID install, search, and results
        if self.advanced_var.get():
            # pack search and results before categories frame to keep order
            self.search_frame.pack(fill=tk.X, before=self.categories_frame)
            self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5, before=self.categories_frame)
            self.install_frame.pack(fill=tk.X)
        else:
            self.install_frame.pack_forget()
            self.search_frame.pack_forget()
            self.results_frame.pack_forget()

    def toggle_topmost(self):
        # Toggle window always-on-top
        try:
            self.root.attributes("-topmost", self.topmost_var.get())
        except Exception:
            pass

    def save_settings(self):
        try:
            data = {"dark_mode": bool(self.dark_mode_var.get()), "follow_system": bool(getattr(self, 'follow_system_var', tk.BooleanVar(value=False)).get())}
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def load_settings(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                dark = data.get("dark_mode", False)
                follow = data.get("follow_system", False)
                self.dark_mode_var.set(dark)
                try:
                    self.theme_var.set('dark' if dark else 'light')
                except Exception:
                    pass
                # follow_system_var should exist already; set it if present
                if getattr(self, 'follow_system_var', None) is not None:
                    self.follow_system_var.set(follow)
        except Exception:
            pass

    def show_category(self, category_name):
        # Clear previous
        for widget in self.apps_container.winfo_children():
            widget.destroy()
        apps = self.categories.get(category_name, [])
        if not apps:
            ttk.Label(self.apps_container, text="No apps in this category").pack()
            return
        top_frame = ttk.Frame(self.apps_container)
        top_frame.pack(fill=tk.X)
        ttk.Label(top_frame, text=f"Apps in {category_name}:").pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Install All", command=lambda: self.install_category_all(category_name)).pack(side=tk.RIGHT)
        for name, pkgid in apps:
            row = ttk.Frame(self.apps_container)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=name).pack(side=tk.LEFT, padx=5)
            ttk.Button(row, text="Install", command=lambda p=pkgid, n=name: self._install_from_category(p, n)).pack(side=tk.RIGHT, padx=5)

    def install_category_all(self, category_name):
        apps = self.categories.get(category_name, [])
        if not apps:
            return
        for name, pkgid in apps:
            threading.Thread(target=self._install_thread, args=(pkgid,), daemon=True).start()

    def _install_from_category(self, package, display_name):
        self.status_var.set(f"Installing {display_name}...")
        threading.Thread(target=self._install_thread, args=(package,), daemon=True).start()

    def toggle_dark_mode(self):
        # Manual toggle disables following the system theme
        if getattr(self, 'follow_system_var', None):
            self.follow_system_var.set(False)
            try:
                self.stop_system_watch()
            except Exception:
                pass
            try:
                self.toolbar_dark_chk.state(['!disabled'])
            except Exception:
                pass
        try:
            self.theme_var.set('dark' if self.dark_mode_var.get() else 'light')
        except Exception:
            pass
        self.apply_theme(self.dark_mode_var.get())
        self.save_settings()

    def _key_toggle_dark(self, event=None):
        """Keyboard shortcut handler to toggle Dark Mode and disable following system theme."""
        if getattr(self, 'follow_system_var', None):
            self.follow_system_var.set(False)
            try:
                self.stop_system_watch()
            except Exception:
                pass
        # toggle dark mode flag and apply
        self.dark_mode_var.set(not self.dark_mode_var.get())
        self.toggle_dark_mode()

    def apply_theme(self, dark):
        style = ttk.Style()
        try:
            # Use the same base theme for both light and dark so widget metrics stay consistent
            try:
                style.theme_use('clam')
            except Exception:
                pass

            if dark:
                # Dark theme colors
                bg = '#2b2b2b'
                fg = '#eaeaea'
                entry_bg = '#3c3f41'
                text_bg = '#1e1e1e'
                pressed = '#252525'
            else:
                # Light theme colors (kept neutral to match system look)
                bg = '#f0f0f0'
                fg = '#000000'
                entry_bg = '#ffffff'
                text_bg = '#ffffff'
                pressed = '#d9d9d9'

            # Base widget colors
            style.configure('.', background=bg, foreground=fg)
            style.configure('TFrame', background=bg)
            style.configure('TLabelframe', background=bg, foreground=fg)
            style.configure('TLabelframe.Label', background=bg, foreground=fg)
            style.configure('TLabel', background=bg, foreground=fg)

            # Buttons (consistent padding and relief so size doesn't change)
            style.configure('TButton', background=entry_bg, foreground=fg, relief='flat', padding=6)
            style.map('TButton',
                      background=[('active', entry_bg), ('pressed', pressed)],
                      foreground=[('active', fg), ('pressed', fg)])

            # App-style menu bar and modern popup menu button styles
            style.configure('App.TButton', background=entry_bg, foreground=fg)
            style.configure('Menu.TButton', background=entry_bg, foreground=fg, relief='flat')
            style.configure('Menu.TFrame', background=entry_bg)

            # Entries / Combobox
            style.configure('TEntry', fieldbackground=entry_bg, foreground=fg)
            style.configure('TCombobox', fieldbackground=entry_bg, foreground=fg)
            style.map('TCombobox', fieldbackground=[('readonly', entry_bg)])

            # Checkbuttons
            style.configure('TCheckbutton', background=bg, foreground=fg)
            style.map('TCheckbutton', background=[('active', bg)], foreground=[('active', fg)])

            # Radiobuttons
            style.configure('TRadiobutton', background=bg, foreground=fg)
            style.map('TRadiobutton', background=[('active', bg)], foreground=[('active', fg)])

            # Scrollbars (visual consistency)
            style.configure('Vertical.TScrollbar', background=entry_bg, troughcolor=bg)
            style.configure('Horizontal.TScrollbar', background=entry_bg, troughcolor=bg)

            # Root and ScrolledText widget - keep same relief/border in both themes to avoid layout shifts
            self.root.configure(bg=bg)
            self.results_text.configure(bg=text_bg, fg=fg, insertbackground=fg, highlightbackground=entry_bg, relief='sunken', bd=1)

            # Ensure consistent border/paddings for frames and container widgets
            try:
                for w in self.root.winfo_children():
                    if isinstance(w, ttk.Frame) or isinstance(w, ttk.LabelFrame):
                        w.configure(padding=4)
            except Exception:
                pass

            # Save colors for dialogs (e.g., About) and other transient windows
            self._theme_colors = {'bg': bg, 'fg': fg, 'entry_bg': entry_bg, 'text_bg': text_bg, 'pressed': pressed} 

        except Exception:
            pass

    # Legacy modern menu removed; using native menubar for File/Window/Help actions

    def get_system_dark_preference(self):
        """Return True if Windows is set to dark mode for apps, False otherwise."""
        try:
            if winreg is None:
                return False
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            # AppsUseLightTheme: 1 = light, 0 = dark
            return bool(val == 0)
        except Exception:
            return False

    def _check_system_theme(self):
        if not getattr(self, 'follow_system_var', tk.BooleanVar(value=False)).get():
            return
        sys_dark = self.get_system_dark_preference()
        if sys_dark != getattr(self, '_system_theme_last', None):
            self._system_theme_last = sys_dark
            self.dark_mode_var.set(sys_dark)
            self.apply_theme(sys_dark)
        # schedule next check
        try:
            self._system_watch_id = self.root.after(5000, self._check_system_theme)
        except Exception:
            pass

    def start_system_watch(self):
        self._system_theme_last = None
        try:
            self._check_system_theme()
        except Exception:
            pass

    def stop_system_watch(self):
        try:
            if getattr(self, '_system_watch_id', None):
                self.root.after_cancel(self._system_watch_id)
                self._system_watch_id = None
        except Exception:
            pass

    def _set_theme_from_menu(self, val):
        """Set theme from the top-bar Theme submenu ('light' or 'dark')."""
        # Selecting a theme from the menu disables following the system theme.
        if getattr(self, 'follow_system_var', None):
            self.follow_system_var.set(False)
            try:
                self.stop_system_watch()
            except Exception:
                pass
            try:
                self.toolbar_dark_chk.state(['!disabled'])
            except Exception:
                pass
        self.dark_mode_var.set(val == 'dark')
        try:
            self.theme_var.set(val)
        except Exception:
            pass
        self.apply_theme(self.dark_mode_var.get())
        self.save_settings()

    def toggle_follow_system(self):
        if getattr(self, 'follow_system_var', tk.BooleanVar(value=False)).get():
            # Enable follow system
            sys_dark = self.get_system_dark_preference()
            self.dark_mode_var.set(sys_dark)
            try:
                self.theme_var.set('dark' if sys_dark else 'light')
            except Exception:
                pass
            self.apply_theme(sys_dark)
            try:
                self.toolbar_dark_chk.state(['disabled'])
            except Exception:
                pass
            self.start_system_watch()
        else:
            # Disable follow system
            try:
                self.toolbar_dark_chk.state(['!disabled'])
            except Exception:
                pass
            self.stop_system_watch()
        self.save_settings()

    def _toolbar_toggle_dark(self):
        # User toggled the visible toolbar switch; disable follow-system and apply
        if getattr(self, 'follow_system_var', None):
            self.follow_system_var.set(False)
            try:
                self.stop_system_watch()
            except Exception:
                pass
        self.toggle_dark_mode()

    def _refresh_system_theme(self):
        if getattr(self, 'follow_system_var', tk.BooleanVar(value=False)).get():
            self._check_system_theme()

    def install_chocolatey(self):
        """Install Chocolatey package manager."""
        response = messagebox.askyesno(
            "Install Chocolatey",
            "This will install Chocolatey, a Windows package manager.\n\n"
            "Chocolatey requires administrator privileges.\n\n"
            "Do you want to proceed?"
        )
        if not response:
            return
        
        self.status_var.set("Installing Chocolatey...")
        threading.Thread(target=self._install_chocolatey_thread, daemon=True).start()
    
    def _install_chocolatey_thread(self):
        try:
            # Run PowerShell command to install Chocolatey
            ps_command = (
                "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                "[System.Net.ServicePointManager]::SecurityProtocol = "
                "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
            )
            subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True,
                timeout=600
            )
            self.status_var.set("✓ Chocolatey installed successfully")
            messagebox.showinfo("Success", "Chocolatey installed successfully!\n\nPlease restart the application for changes to take effect.")
        except subprocess.CalledProcessError:
            self.status_var.set("Installation failed")
            messagebox.showerror("Error", "Failed to install Chocolatey. Make sure you have administrator privileges.")
        except Exception as e:
            self.status_var.set("Error")
            messagebox.showerror("Error", f"Error installing Chocolatey: {str(e)}")

    def exit_app(self):
        # Graceful exit
        try:
            self.stop_system_watch()
        except Exception:
            pass
        try:
            self.root.quit()
        except Exception:
            self.root.destroy()

    def show_about(self):
        # About dialog
        about = tk.Toplevel(self.root)
        about.title("About WinGet Package Installer")
        about.geometry("400x220")
        about.resizable(False, False)
        about.transient(self.root)
        about.grab_set()
        # Use current theme colors if available
        colors = getattr(self, '_theme_colors', {'bg': '#f0f0f0', 'fg': '#000000', 'entry_bg': '#ffffff', 'text_bg': '#ffffff'})
        try:
            about.configure(bg=colors['bg'])
        except Exception:
            pass

        content = ttk.Frame(about, padding=12)
        content.pack(fill=tk.BOTH, expand=True)
        ttk.Label(content, text="WinGet Package Installer", font=("Segoe UI", 12, "bold")).pack(pady=(6,6))
        ttk.Label(content, text="Simple GUI to search and install packages via winget.").pack(pady=(0,8))
        ttk.Label(content, text="\nVersion: 0.2 beta\nCopyright © 2026 Nikki\nLicensed under the GNU GPL v3 (see LICENSE)").pack()
        ttk.Button(content, text="Close", command=about.destroy).pack(pady=(8,0))

        # center the about dialog over root
        about.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (about.winfo_width() // 2)
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (about.winfo_height() // 2)
        about.geometry(f"+{x}+{y}")


# Removed legacy _ModernMenu class and duplicate method definitions; using native menubar for File/Window/Help actions

if __name__ == "__main__":

    root = tk.Tk()
    app = WinGetGUI(root)
    root.mainloop()
