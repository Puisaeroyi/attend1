"""
Attendance Data Processor Tab

Provides GUI interface for processing biometric attendance data
into structured attendance records with real-time logging.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import RuleConfig
    from processor import AttendanceProcessor
    from gui.utils import TextRedirector
except ImportError:
    # Fallback if modules not available
    RuleConfig = None
    AttendanceProcessor = None
    TextRedirector = None


class AttendanceProcessorTab(ttk.Frame):
    """Attendance data processing tab"""

    def __init__(self, parent):
        super().__init__(parent)
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.config_path = tk.StringVar(value="rule.yaml")
        self.is_processing = False
        self.create_widgets()

    def create_widgets(self):
        """Build UI layout"""
        # Title
        ttk.Label(
            self,
            text="Attendance Data Processor",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=4, pady=10)

        # Input file row
        ttk.Label(self, text="Input Excel File:").grid(
            row=1, column=0, sticky='w', padx=10, pady=5
        )
        ttk.Entry(
            self, textvariable=self.input_path, width=45
        ).grid(row=1, column=1, padx=5)
        ttk.Button(
            self, text="Browse...", command=self.browse_input
        ).grid(row=1, column=2, padx=5)

        # Output file row
        ttk.Label(self, text="Output Excel File:").grid(
            row=2, column=0, sticky='w', padx=10, pady=5
        )
        ttk.Entry(
            self, textvariable=self.output_path, width=45
        ).grid(row=2, column=1, padx=5)
        ttk.Button(
            self, text="Browse...", command=self.browse_output
        ).grid(row=2, column=2, padx=5)

        # Config file row
        ttk.Label(self, text="Config File:").grid(
            row=3, column=0, sticky='w', padx=10, pady=5
        )
        ttk.Entry(
            self, textvariable=self.config_path, width=45
        ).grid(row=3, column=1, padx=5)
        ttk.Button(
            self, text="Browse...", command=self.browse_config
        ).grid(row=3, column=2, padx=5)
        ttk.Button(
            self, text="Default", command=self.use_default_config
        ).grid(row=3, column=3, padx=5)

        # Process button
        self.process_btn = ttk.Button(
            self, text="Process", command=self.process
        )
        self.process_btn.grid(row=4, column=0, columnspan=4, pady=15)

        # Processing log
        ttk.Label(self, text="Processing Log:").grid(
            row=5, column=0, sticky='nw', padx=10
        )
        self.log_text = tk.Text(
            self, height=15, width=75, state='disabled'
        )
        self.log_text.grid(row=6, column=0, columnspan=4, padx=10, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=6, column=4, sticky='ns')
        self.log_text.config(yscrollcommand=scrollbar.set)

    def browse_input(self):
        """Open file dialog for input Excel"""
        path = filedialog.askopenfilename(
            title="Select Input Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if path:
            self.input_path.set(path)

    def browse_output(self):
        """Open file dialog for output Excel"""
        path = filedialog.asksaveasfilename(
            title="Save Output Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if path:
            self.output_path.set(path)

    def browse_config(self):
        """Open file dialog for config YAML"""
        path = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("YAML Files", "*.yaml *.yml"), ("All Files", "*.*")]
        )
        if path:
            self.config_path.set(path)

    def use_default_config(self):
        """Reset to default config"""
        self.config_path.set("rule.yaml")

    def log(self, message):
        """Write message to log text area"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.update_idletasks()

    def validate_inputs(self):
        """Validate input and output file paths

        Returns:
            tuple: (is_valid, error_message)
        """
        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()
        config_path = self.config_path.get().strip()

        if not input_path:
            return False, "Please select an input Excel file"

        if not output_path:
            return False, "Please select an output Excel file"

        if not config_path:
            return False, "Please select a config file or use default"

        # Validate input file exists
        if not Path(input_path).exists():
            return False, f"Input file not found:\n{input_path}"

        # Validate input file extension
        if not input_path.lower().endswith(('.xlsx', '.xls')):
            return False, "Input file must be Excel format (.xlsx or .xls)"

        # Validate output file extension
        if not output_path.lower().endswith('.xlsx'):
            return False, "Output file must be Excel format (.xlsx)"

        # Validate output directory exists
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            return False, f"Output directory not found:\n{output_dir}"

        # Validate config file exists
        if not Path(config_path).exists():
            return False, f"Config file not found:\n{config_path}"

        # Check if input and output are the same
        if Path(input_path).resolve() == Path(output_path).resolve():
            return False, "Input and output files cannot be the same.\nPlease choose a different output location."

        return True, ""

    def process(self):
        """Execute attendance data processing"""
        if self.is_processing:
            messagebox.showwarning("Busy", "Processing is already in progress.")
            return

        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()
        config_path = self.config_path.get().strip()

        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            messagebox.showerror("Validation Error", error_message)
            return

        # Check if required modules are available
        if not all([RuleConfig, AttendanceProcessor, TextRedirector]):
            error_msg = "Required modules not available. Please ensure processor.py and config.py are in the correct location."
            messagebox.showerror("Module Error", error_msg)
            return

        # Start processing in background thread
        self.is_processing = True
        self.process_btn.config(state='disabled', text="Processing...")
        self.log("=" * 70)
        self.log("🚀 Starting attendance processing pipeline")
        self.log("=" * 70)

        # Run processing in thread
        thread = threading.Thread(
            target=self._process_worker,
            args=(input_path, output_path, config_path),
            daemon=True
        )
        thread.start()

    def _process_worker(self, input_path, output_path, config_path):
        """Worker thread for attendance processing

        Args:
            input_path: Path to input Excel file
            output_path: Path to output Excel file
            config_path: Path to config YAML file
        """
        original_stdout = sys.stdout

        try:
            # Redirect stdout to GUI log widget
            if TextRedirector:
                sys.stdout = TextRedirector(self.log_text)
                sys.stderr = TextRedirector(self.log_text)

            # Load configuration
            print(f"🔧 Loading configuration: {config_path}")
            config = RuleConfig.load_from_yaml(config_path)
            print(f"   ✓ Loaded config: {len(config.shifts)} shifts, {len(config.valid_users)} valid users")

            # Validate input file
            print(f"📋 Validating input file: {input_path}")
            # Validation is done in validate_inputs method
            print("   ✓ Input file validated")

            print()
            print("=" * 70)
            print("🚀 Starting processing pipeline")
            print("=" * 70)

            # Process attendance data
            processor = AttendanceProcessor(config)
            processor.process(input_path, output_path)

            print()
            print("=" * 70)
            print(f"✅ Success! Output written to: {output_path}")
            print("=" * 70)

            # Show success message in main thread
            self.after(0, self._show_success, output_path)

        except ImportError as e:
            error_msg = f"Required module not available:\n{e}"
            print(f"\n❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        except FileNotFoundError as e:
            error_msg = f"File not found:\n{e}"
            print(f"\n❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        except ValueError as e:
            error_msg = f"Configuration error:\n{e}"
            print(f"\n❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        except Exception as e:
            error_msg = f"Processing error:\n{e}"
            print(f"\n❌ Error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.after(0, self._show_error, error_msg)

        finally:
            # Restore stdout and re-enable button in main thread
            sys.stdout = original_stdout
            sys.stderr = original_stdout
            self.after(0, self._reset_button)

    def _show_success(self, output_path):
        """Show success message dialog

        Args:
            output_path: Path to output file
        """
        messagebox.showinfo(
            "Processing Complete",
            f"Attendance processing completed successfully!\n\n"
            f"Output saved to:\n{output_path}"
        )

    def _show_error(self, error_message):
        """Show error message dialog

        Args:
            error_message: Error message to display
        """
        messagebox.showerror("Processing Error", error_message)

    def _reset_button(self):
        """Reset process button to enabled state"""
        self.is_processing = False
        self.process_btn.config(state='normal', text="Process")