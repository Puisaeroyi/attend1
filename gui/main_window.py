"""Main application window for Attendance & CSV Converter Tool

Provides tabbed interface with CSV Converter and Attendance Processor tabs.
Handles window management, menu bar, and status bar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gui.styles import apply_default_styling
except ImportError:
    apply_default_styling = None


class MainWindow:
    """Main application window with tabbed interface"""

    def __init__(self):
        """Initialize main window"""
        self.root = tk.Tk()
        self.setup_window()
        self.apply_styling()
        self.create_menu_bar()
        self.create_widgets()
        self.bind_events()

    def setup_window(self):
        """Configure window properties"""
        self.root.title("Attendance & CSV Converter Tool v3.0.0")
        self.root.geometry("850x650")
        self.root.minsize(800, 600)

        # Center window on screen
        self.center_window()

        # Set icon (will be added later)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass  # Icon optional

    def apply_styling(self):
        """Apply default styling to the window"""
        if apply_default_styling:
            apply_default_styling(self.root)

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Alt+F4")

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Clear All Logs", command=self.clear_all_logs)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)

    def create_widgets(self):
        """Create main window widgets"""
        # Create title frame
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=10, pady=10)

        title_label = ttk.Label(
            title_frame,
            text="Attendance & CSV Converter Tool",
            font=("Arial", 16, "bold"),
            style='Title.TLabel' if apply_default_styling else None
        )
        title_label.pack()

        version_label = ttk.Label(
            title_frame,
            text="Version 3.0.0 - GUI Edition",
            font=("Arial", 10),
            style='Subtitle.TLabel' if apply_default_styling else None
        )
        version_label.pack()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Import and create tabs
        try:
            from gui.csv_tab import CSVConverterTab
            from gui.attendance_tab import AttendanceProcessorTab

            # Create and add CSV Converter tab
            self.csv_tab = CSVConverterTab(self.notebook)
            self.notebook.add(self.csv_tab, text="CSV Converter")

            # Create and add Attendance Processor tab
            self.attendance_tab = AttendanceProcessorTab(self.notebook)
            self.notebook.add(self.attendance_tab, text="Attendance Processor")

            # Store references for later use
            self.tabs = {
                "CSV Converter": self.csv_tab,
                "Attendance Processor": self.attendance_tab
            }

        except ImportError as e:
            # Fallback to placeholder if modules not yet implemented
            print(f"Warning: Could not import tab modules: {e}")
            placeholder_frame = ttk.Frame(self.notebook)
            self.notebook.add(placeholder_frame, text="Coming Soon")
            self.tabs = {}

        # Create status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief='sunken',
            anchor='w'
        )
        self.status_bar.pack(fill='x', side='bottom')

        # Update initial status
        self.update_status("Application ready. Select a tab to begin.")

    def bind_events(self):
        """Bind window events"""
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F1>', lambda e: self.show_help())

    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def on_tab_changed(self, event):
        """Handle tab change event"""
        selected_tab = event.widget.tab('current')['text']
        self.update_status(f"Switched to {selected_tab} tab")

    def update_status(self, message):
        """Update status bar message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_bar.config(text=f"[{timestamp}] {message}")

    def clear_all_logs(self):
        """Clear all log text areas"""
        if hasattr(self, 'tabs'):
            for tab_name, tab in self.tabs.items():
                try:
                    if hasattr(tab, 'status_text'):
                        tab.status_text.config(state='normal')
                        tab.status_text.delete(1.0, tk.END)
                        tab.status_text.config(state='disabled')
                    elif hasattr(tab, 'log_text'):
                        tab.log_text.config(state='normal')
                        tab.log_text.delete(1.0, tk.END)
                        tab.log_text.config(state='disabled')
                except:
                    pass
        self.update_status("All logs cleared")

    def show_about(self):
        """Show about dialog"""
        about_text = """Attendance & CSV Converter Tool
Version 3.0.0 - GUI Edition

A unified tool for:
• CSV to XLSX conversion with column extraction
• Attendance data processing from biometric logs

Features:
• User-friendly graphical interface
• Real-time progress feedback
• Comprehensive error handling
• Thread-safe processing

Development Team
© 2025"""

        messagebox.showinfo("About", about_text)

    def show_help(self):
        """Show help dialog"""
        help_text = """Quick Start Guide:

CSV Converter:
1. Select input CSV file
2. Choose output XLSX location
3. Click 'Convert'

Attendance Processor:
1. Select input Excel file with biometric data
2. Choose output location
3. Select config file (default: rule.yaml)
4. Click 'Process'

Keyboard Shortcuts:
• Ctrl+Q: Exit application
• F1: Show this help

For detailed help, contact IT support."""

        messagebox.showinfo("Help", help_text)

    def on_closing(self):
        """Handle window close event"""
        # Check if any operations are in progress
        operations_in_progress = False

        if hasattr(self, 'tabs'):
            for tab_name, tab in self.tabs.items():
                try:
                    if hasattr(tab, 'is_converting') and tab.is_converting:
                        operations_in_progress = True
                    if hasattr(tab, 'is_processing') and tab.is_processing:
                        operations_in_progress = True
                except:
                    pass

        if operations_in_progress:
            if messagebox.askokcancel(
                "Operations in Progress",
                "Some operations are still running.\n\n"
                "Are you sure you want to exit?\n"
                "Data may be lost."
            ):
                self.root.destroy()
        else:
            if messagebox.askokcancel("Quit", "Exit application?"):
                self.root.destroy()

    def run(self):
        """Start main event loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n\n{e}")
            self.root.destroy()


if __name__ == "__main__":
    # Test main window standalone
    app = MainWindow()
    app.run()