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

        self._create_app_menu_bar()

        # Toolbar with a refresh button (hidden Dark Mode toggle retained for compatibility)
        toolbar = ttk.Frame(self.root, padding="4")
        toolbar.pack(fill=tk.X, padx=10, pady=(5,0))
        self.toolbar_dark_chk = ttk.Checkbutton(toolbar, text="Dark Mode", variable=self.dark_mode_var, command=self._toolbar_toggle_dark)
        ttk.Button(toolbar, text="Refresh System Theme", command=self._refresh_system_theme).pack(side=tk.LEFT, padx=(6,0))
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
        try:
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
        try:
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

    # --- Modern app-style menu popup implementation (Windows 11-like) ---
    def _create_app_menu_bar(self):
        """Create a slim app-style bar with File / Window / Help buttons that show modern popups."""
        # Place the app menu bar just under the native menu
        try:
            self._app_menu_bar = ttk.Frame(self.root, padding=(6,2), style='AppBar.TFrame')
            self._app_menu_bar.pack(fill=tk.X, padx=6)
            btn_style = 'App.TButton'
            ttk.Style().configure(btn_style, relief='flat', padding=(8,4))
            ttk.Button(self._app_menu_bar, text='File', style=btn_style, command=self._open_file_menu).pack(side=tk.LEFT, padx=(2,4))
            ttk.Button(self._app_menu_bar, text='Window', style=btn_style, command=self._open_window_menu).pack(side=tk.LEFT, padx=(2,4))
            ttk.Button(self._app_menu_bar, text='Help', style=btn_style, command=self._open_help_menu).pack(side=tk.LEFT, padx=(2,4))
        except Exception:
            pass

    def _open_file_menu(self):
        # For now, open a simple modern menu with Exit
        items = [
            {'type': 'cmd', 'label': 'Exit', 'command': self.exit_app},
        ]
        self._show_modern_menu(items, anchor_widget=self._app_menu_bar.winfo_children()[0])

    def _open_window_menu(self):
        # Window menu items: Always on Top, Light/Dark, Follow System
        items = [
            {'type': 'check', 'label': 'Always on Top', 'var': self.topmost_var, 'command': self.toggle_topmost},
            {'type': 'radio', 'label': 'Light', 'group': 'theme', 'value': 'light', 'command': lambda: self._set_theme_from_menu('light')},
            {'type': 'radio', 'label': 'Dark', 'group': 'theme', 'value': 'dark', 'command': lambda: self._set_theme_from_menu('dark')},
            {'type': 'sep'},
            {'type': 'check', 'label': 'Follow System Theme', 'var': self.follow_system_var, 'command': self.toggle_follow_system},
        ]
        self._show_modern_menu(items, anchor_widget=self._app_menu_bar.winfo_children()[1])

    def _open_help_menu(self):
        items = [
            {'type': 'cmd', 'label': 'About', 'command': self.show_about},
        ]
        self._show_modern_menu(items, anchor_widget=self._app_menu_bar.winfo_children()[2])

    def _show_modern_menu(self, items, anchor_widget):
        # Close previous menu if open
        self._close_modern_menu()
        try:
            x = anchor_widget.winfo_rootx()
            y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height()
        except Exception:
            x = self.root.winfo_rootx() + 10
            y = self.root.winfo_rooty() + 30
        colors = getattr(self, '_theme_colors', {'bg': '#ffffff', 'fg': '#000000', 'entry_bg': '#ffffff'})
        menu = _ModernMenu(self.root, items, x, y, colors, on_close=self._close_modern_menu)
        self._current_modern_menu = menu

    def _close_modern_menu(self):
        try:
            if getattr(self, '_current_modern_menu', None):
                self._current_modern_menu.close()
                self._current_modern_menu = None
        except Exception:
            pass

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
        ttk.Label(content, text=f"\nVersion: 0.1.1\nCopyright © Nikki 2026\n").pack()
        ttk.Button(content, text="Close", command=about.destroy).pack(pady=(8,0))

        # center the about dialog over root
        about.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (about.winfo_width() // 2)
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (about.winfo_height() // 2)
        about.geometry(f"+{x}+{y}")


class _ModernMenu(tk.Toplevel):
    """Lightweight modern-looking popup menu implemented as an overrideredirect Toplevel.
    Supports command, check, radio and separator item types (minimal).
    """
    def __init__(self, parent, items, x, y, colors, on_close=None):
        super().__init__(parent)
        self.overrideredirect(True)
        self.transient(parent)
        self.attributes('-topmost', True)
        self.configure(bg=colors.get('bg', '#ffffff'))
        # Outer frame
        frm = ttk.Frame(self, padding=6, style='Menu.TFrame')
        frm.pack()
        self._parent = parent
        self._on_close = on_close
        # Build items
        for it in items:
            it_type = it.get('type', 'cmd')
            if it_type == 'sep':
                ttk.Separator(frm, orient='horizontal').pack(fill=tk.X, pady=4)
                continue
            row = ttk.Frame(frm)
            row.pack(fill=tk.X, pady=2)
            label_text = it.get('label', '')
            if it_type == 'check':
                var = it.get('var')
                indicator = '✓' if getattr(var, 'get', lambda: False)() else ' '
                lbl = ttk.Label(row, text=indicator, width=2)
                lbl.pack(side=tk.LEFT)
                btn = ttk.Button(row, text=label_text, command=self._wrap_cmd(it), style='Menu.TButton')
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            elif it_type == 'radio':
                # determine current state from theme_var if available
                group = it.get('group')
                current = getattr(parent, 'theme_var', None)
                indicator = '●' if (current and current.get() == it.get('value')) else ' '
                lbl = ttk.Label(row, text=indicator, width=2)
                lbl.pack(side=tk.LEFT)
                btn = ttk.Button(row, text=label_text, command=self._wrap_cmd(it), style='Menu.TButton')
                btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                btn = ttk.Button(row, text=label_text, command=self._wrap_cmd(it), style='Menu.TButton')
                btn.pack(fill=tk.X)
        # place window
        self.geometry(f"+{x}+{y}")
        # click outside to close
        self._click_binding = parent.bind_all('<Button-1>', self._on_global_click, '+')
        self.bind('<FocusOut>', lambda e: self.close())
        self.after(10, lambda: self.focus_force())

    def _wrap_cmd(self, item):
        def _cmd():
            try:
                if item.get('type') == 'check' and item.get('var') is not None:
                    item['var'].set(not item['var'].get())
                cmd = item.get('command')
                if callable(cmd):
                    cmd()
            finally:
                self.close()
        return _cmd

    def _on_global_click(self, event):
        # close if click not inside this window
        if not self.winfo_containing(event.x_root, event.y_root):
            self.close()

    def close(self):
        try:
            if getattr(self._parent, 'unbind_all', None) and getattr(self, '_click_binding', None):
                self._parent.unbind_all('<Button-1>')
        except Exception:
            pass
        try:
            if callable(self._on_close):
                self._on_close()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


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

if __name__ == "__main__":
    root = tk.Tk()
    app = WinGetGUI(root)
    root.mainloop()
