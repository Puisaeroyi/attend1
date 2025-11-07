"""
CSV to XLSX Converter Tab

Provides GUI interface for converting CSV files to Excel format
with column extraction and renaming functionality.
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
    from csv_converter import convert_csv_to_xlsx, validate_input_file, validate_output_path
except ImportError:
    # Fallback functions if csv_converter not available
    def convert_csv_to_xlsx(input_path, output_path):
        raise ImportError("csv_converter module not available")
    def validate_input_file(path):
        pass
    def validate_output_path(path):
        pass


class CSVConverterTab(ttk.Frame):
    """CSV to XLSX conversion tab"""

    def __init__(self, parent):
        super().__init__(parent)
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.is_converting = False
        self.create_widgets()

    def create_widgets(self):
        """Build UI layout"""
        # Title
        ttk.Label(
            self,
            text="CSV to XLSX Converter",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=3, pady=10)

        # Input file row
        ttk.Label(self, text="Input CSV File:").grid(
            row=1, column=0, sticky='w', padx=10, pady=5
        )
        ttk.Entry(
            self, textvariable=self.input_path, width=50
        ).grid(row=1, column=1, padx=5)
        ttk.Button(
            self, text="Browse...", command=self.browse_input
        ).grid(row=1, column=2, padx=10)

        # Output file row
        ttk.Label(self, text="Output XLSX File:").grid(
            row=2, column=0, sticky='w', padx=10, pady=5
        )
        ttk.Entry(
            self, textvariable=self.output_path, width=50
        ).grid(row=2, column=1, padx=5)
        ttk.Button(
            self, text="Browse...", command=self.browse_output
        ).grid(row=2, column=2, padx=10)

        # Convert button
        self.convert_btn = ttk.Button(
            self, text="Convert", command=self.convert
        )
        self.convert_btn.grid(row=3, column=0, columnspan=3, pady=15)

        # Status text area
        ttk.Label(self, text="Status:").grid(
            row=4, column=0, sticky='nw', padx=10
        )
        self.status_text = tk.Text(
            self, height=15, width=70, state='disabled'
        )
        self.status_text.grid(row=5, column=0, columnspan=3, padx=10, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, command=self.status_text.yview)
        scrollbar.grid(row=5, column=3, sticky='ns')
        self.status_text.config(yscrollcommand=scrollbar.set)

    def browse_input(self):
        """Open file dialog for input CSV"""
        path = filedialog.askopenfilename(
            title="Select Input CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            self.input_path.set(path)

    def browse_output(self):
        """Open file dialog for output XLSX"""
        path = filedialog.asksaveasfilename(
            title="Save Output XLSX File",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if path:
            self.output_path.set(path)

    def log(self, message):
        """Write message to status text area"""
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')

    def validate_inputs(self):
        """Validate input and output file paths

        Returns:
            tuple: (is_valid, error_message)
        """
        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()

        if not input_path:
            return False, "Please select an input CSV file"

        if not output_path:
            return False, "Please select an output XLSX file"

        # Validate input file
        try:
            validate_input_file(input_path)
        except FileNotFoundError:
            return False, f"Input file not found:\n{input_path}"
        except ValueError as e:
            return False, f"Invalid input file:\n{e}"

        # Validate output path
        try:
            validate_output_path(output_path)
        except ValueError as e:
            return False, f"Invalid output file:\n{e}"
        except FileNotFoundError as e:
            return False, f"Output directory not found:\n{e}"

        # Check if input and output are the same
        if Path(input_path).resolve() == Path(output_path).resolve():
            return False, "Input and output files cannot be the same.\nPlease choose a different output location."

        return True, ""

    def convert(self):
        """Execute CSV to XLSX conversion"""
        if self.is_converting:
            messagebox.showwarning("Busy", "Conversion is already in progress.")
            return

        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()

        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            messagebox.showerror("Validation Error", error_message)
            return

        # Start conversion in background thread
        self.is_converting = True
        self.convert_btn.config(state='disabled', text="Converting...")
        self.log("=" * 50)
        self.log("🔄 Starting CSV to XLSX conversion...")
        self.log(f"📖 Input: {input_path}")
        self.log(f"💾 Output: {output_path}")
        self.log("=" * 50)

        # Run conversion in thread
        thread = threading.Thread(
            target=self._convert_worker,
            args=(input_path, output_path),
            daemon=True
        )
        thread.start()

    def _convert_worker(self, input_path, output_path):
        """Worker thread for CSV conversion

        Args:
            input_path: Path to input CSV file
            output_path: Path to output XLSX file
        """
        try:
            # Perform conversion
            self.log("📋 Reading CSV file...")
            row_count = convert_csv_to_xlsx(input_path, output_path)

            # Success
            self.log(f"✅ Success! Converted {row_count} rows")
            self.log(f"📁 Output saved to: {output_path}")
            self.log("=" * 50)
            self.log("Conversion completed successfully!")

            # Show success message in main thread
            self.after(0, self._show_success, row_count, output_path)

        except ImportError as e:
            error_msg = f"CSV converter module not available:\n{e}"
            self.log(f"❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        except FileNotFoundError as e:
            error_msg = f"File not found:\n{e}"
            self.log(f"❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        except ValueError as e:
            error_msg = f"Data validation error:\n{e}"
            self.log(f"❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        except PermissionError as e:
            error_msg = f"Permission denied:\n{e}"
            self.log(f"❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        except Exception as e:
            error_msg = f"Unexpected error:\n{e}"
            self.log(f"❌ Error: {error_msg}")
            self.after(0, self._show_error, error_msg)

        finally:
            # Re-enable button in main thread
            self.after(0, self._reset_button)

    def _show_success(self, row_count, output_path):
        """Show success message dialog

        Args:
            row_count: Number of rows converted
            output_path: Path to output file
        """
        messagebox.showinfo(
            "Conversion Complete",
            f"Successfully converted {row_count} rows!\n\n"
            f"Output saved to:\n{output_path}"
        )

    def _show_error(self, error_message):
        """Show error message dialog

        Args:
            error_message: Error message to display
        """
        messagebox.showerror("Conversion Error", error_message)

    def _reset_button(self):
        """Reset convert button to enabled state"""
        self.is_converting = False
        self.convert_btn.config(state='normal', text="Convert")