# Windows GUI Wrapper Implementation Plan

**Project:** Attendance & CSV Converter Tool - Windows GUI Wrapper
**Version:** 3.0.0 (GUI Edition)
**Date:** 2025-11-06
**Target Platform:** Windows 10/11
**Target Users:** Non-technical staff (zero coding/CLI knowledge)

---

## Overview

Transform existing CLI-based attendance processor (v2.1.0) into user-friendly Windows desktop application with point-and-click interface. Preserve ALL existing functionality while eliminating need for command-line knowledge.

**Scope:**
- GUI wrapper for existing processor.py + csv_converter.py
- Native Windows file dialogs (browse buttons)
- Double-click executable (no Python installation required)
- Real-time progress feedback
- Error handling with user-friendly messages

**Out of Scope:**
- Rewriting core logic (processor.py stays unchanged)
- Web-based interface
- Multi-platform support (Linux/macOS)
- Advanced features (scheduling, batch processing)

---

## Executive Summary - Framework Selection

**RECOMMENDED: tkinter**

**Justification:**
- Built into Python (no additional dependencies)
- Native Windows look-and-feel
- Excellent file dialog support (tkinter.filedialog)
- Simple for target use case (forms, buttons, text display)
- Lightweight binaries with PyInstaller (~15-20MB)
- Well-documented, stable, mature

**Rejected Alternatives:**
- PyQt5/PySide6: Overkill (100MB+ binaries), steep learning curve
- wxPython: Extra dependency, larger binaries
- PySimpleGUI: Licensing concerns (paid for commercial), limited customization

---

## Requirements

### Functional Requirements

**FR1: Main Window**
- Menu/tab selection: CSV Converter | Attendance Processor
- Clear visual separation between tools
- Application title, version display
- Status bar for messages

**FR2: CSV Converter Interface**
- Input file browser (CSV files only)
- Output file browser (XLSX files only)
- "Convert" button (disabled until paths valid)
- Progress indicator during conversion
- Success/error feedback with details

**FR3: Attendance Processor Interface**
- Input file browser (XLSX files only)
- Output file browser (XLSX files only)
- Config file browser (YAML files, default: rule.yaml)
- "Process" button (disabled until paths valid)
- Real-time progress log (scrollable text area)
- Success/error feedback

**FR4: File Validation**
- Check file existence (input files)
- Check file extensions (.csv, .xlsx, .yaml)
- Check write permissions (output paths)
- Display validation errors to user

**FR5: Error Handling**
- Catch all exceptions from backend
- Display user-friendly error dialogs
- Log technical details to file (debug.log)
- Never crash silently

### Non-Functional Requirements

**NFR1: Usability**
- Zero command-line knowledge required
- Intuitive layout (top-to-bottom flow)
- Clear labels, tooltips on hover
- Responsive (no freezing during processing)

**NFR2: Performance**
- GUI overhead <100ms
- Processing performance unchanged from CLI
- No memory leaks (handle large files same as CLI)

**NFR3: Packaging**
- Single-file executable (.exe)
- No Python installation required
- Bundle rule.yaml in executable
- Executable size <25MB

**NFR4: Compatibility**
- Windows 10 (64-bit) minimum
- Windows 11 support
- No admin rights required for execution

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   GUI Layer (NEW)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  main_gui.py (tkinter application)              │   │
│  │  - MainWindow (root window, menu)               │   │
│  │  - CSVConverterTab (file pickers, convert btn)  │   │
│  │  - AttendanceTab (file pickers, process btn)    │   │
│  │  - ProgressDialog (async feedback)              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        │
                        │ (calls existing functions)
                        ↓
┌─────────────────────────────────────────────────────────┐
│             Backend Layer (EXISTING)                    │
│  ┌────────────────────┐   ┌──────────────────────┐     │
│  │  csv_converter.py  │   │  processor.py        │     │
│  │  - convert_csv_to  │   │  - AttendanceProc    │     │
│  │    _xlsx()         │   │  - process()         │     │
│  └────────────────────┘   └──────────────────────┘     │
│                                                          │
│  ┌────────────────────┐   ┌──────────────────────┐     │
│  │  config.py         │   │  validators.py       │     │
│  │  - RuleConfig      │   │  - validate_input    │     │
│  └────────────────────┘   └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

**Design Pattern: Adapter Pattern**
- GUI adapts existing CLI backend
- No changes to processor.py, csv_converter.py
- GUI handles user interaction → backend does processing

---

### Component Design

#### 1. MainWindow (Root Application)

**Purpose:** Top-level window container

**Components:**
- ttk.Notebook (tabbed interface)
- Tab 1: CSV Converter
- Tab 2: Attendance Processor
- Status bar (bottom)
- Menu bar (File → Exit, Help → About)

**Responsibilities:**
- Initialize tkinter root
- Create tabs
- Handle window close event
- Display global status messages

---

#### 2. CSVConverterTab

**Purpose:** CSV → XLSX conversion interface

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  CSV to XLSX Converter                                  │
│                                                          │
│  Input CSV File:                                        │
│  [________________________] [Browse...]                 │
│                                                          │
│  Output XLSX File:                                      │
│  [________________________] [Browse...]                 │
│                                                          │
│                    [Convert]                            │
│                                                          │
│  Status:                                                │
│  [Text area - scrollable, read-only]                   │
└─────────────────────────────────────────────────────────┘
```

**Widgets:**
- 2x Entry widgets (file paths, read-only)
- 2x Button widgets ("Browse...", "Convert")
- 1x Text widget (status output)
- Labels for descriptions

**Logic:**
- Browse button → tkinter.filedialog.askopenfilename() / asksaveasfilename()
- Convert button → calls csv_converter.convert_csv_to_xlsx()
- Run in thread (prevent UI freeze)
- Update status text with progress/results

---

#### 3. AttendanceProcessorTab

**Purpose:** Attendance data processing interface

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Attendance Data Processor                              │
│                                                          │
│  Input Excel File (.xlsx):                              │
│  [________________________] [Browse...]                 │
│                                                          │
│  Output Excel File (.xlsx):                             │
│  [________________________] [Browse...]                 │
│                                                          │
│  Config File (rule.yaml):                               │
│  [________________________] [Browse...] [Default]       │
│                                                          │
│                    [Process]                            │
│                                                          │
│  Processing Log:                                        │
│  [Text area - scrollable, read-only]                   │
└─────────────────────────────────────────────────────────┘
```

**Widgets:**
- 3x Entry widgets (file paths)
- 4x Button widgets ("Browse..." x3, "Default", "Process")
- 1x Text widget (log output with scrollbar)
- Labels, tooltips

**Logic:**
- Browse buttons → file dialogs with filters (.xlsx, .yaml)
- "Default" button → sets config to "rule.yaml" (bundled)
- Process button → calls AttendanceProcessor.process()
- Redirect processor print statements to Text widget
- Run in thread (async processing)

---

#### 4. Threading Strategy

**Problem:** Long-running operations freeze GUI

**Solution:** Run backend calls in separate threads

**Implementation:**
```python
import threading

def process_attendance(input_path, output_path, config_path, log_widget):
    """Run in worker thread"""
    try:
        # Redirect stdout to log widget
        sys.stdout = TextRedirector(log_widget)

        # Process (existing code)
        config = RuleConfig.load_from_yaml(config_path)
        processor = AttendanceProcessor(config)
        processor.process(input_path, output_path)

        # Success message
        messagebox.showinfo("Success", f"Output: {output_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        sys.stdout = sys.__stdout__  # Restore

def on_process_click():
    """Button click handler"""
    thread = threading.Thread(
        target=process_attendance,
        args=(input_path, output_path, config_path, log_widget)
    )
    thread.daemon = True
    thread.start()
```

**Benefits:**
- GUI remains responsive
- User can see real-time progress
- Can implement "Cancel" button (future)

---

#### 5. TextRedirector (Helper Class)

**Purpose:** Redirect print() statements to GUI Text widget

**Implementation:**
```python
class TextRedirector:
    """Redirect stdout/stderr to tkinter Text widget"""

    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Auto-scroll
        self.text_widget.update_idletasks()

    def flush(self):
        pass  # Required for file-like object
```

**Usage:** Capture processor.py print statements without modifying processor.py

---

## File Structure Changes

### New Files

```
windows_project/
├── gui/                          # NEW: GUI module
│   ├── __init__.py
│   ├── main_window.py           # MainWindow class
│   ├── csv_tab.py               # CSVConverterTab widget
│   ├── attendance_tab.py        # AttendanceProcessorTab widget
│   ├── utils.py                 # TextRedirector, helpers
│   └── styles.py                # ttk styles, colors, fonts
│
├── main_gui.py                  # NEW: GUI entry point
├── icon.ico                     # NEW: Application icon (Windows)
├── build_exe.py                 # NEW: PyInstaller build script
│
├── main.py                      # EXISTING: CLI entry point (keep)
├── processor.py                 # EXISTING: No changes
├── csv_converter.py             # EXISTING: No changes
├── config.py                    # EXISTING: No changes
├── validators.py                # EXISTING: No changes
├── utils.py                     # EXISTING: No changes
├── rule.yaml                    # EXISTING: Bundle in .exe
├── requirements.txt             # UPDATE: Add pyinstaller
└── requirements-gui.txt         # NEW: GUI-specific deps
```

### Modified Files

**requirements.txt** (add):
```
# Existing dependencies
openpyxl>=3.1.0
pandas>=2.0.0
pyyaml>=6.0
xlsxwriter>=3.0.0
pytest>=7.4.0
pytest-cov

# NEW: GUI packaging
pyinstaller>=6.0.0
```

---

## Implementation Steps

### Phase 1: Setup & Prototyping (2 hours)

**Step 1.1: Create GUI Module Structure**
```bash
mkdir -p gui
touch gui/__init__.py
touch gui/main_window.py
touch gui/csv_tab.py
touch gui/attendance_tab.py
touch gui/utils.py
touch gui/styles.py
touch main_gui.py
```

**Step 1.2: Create Minimal Prototype**
- Basic tkinter window with "Hello World"
- Test window creation, closing
- Verify tkinter available on Windows

**Step 1.3: Test File Dialogs**
- Implement file browser button
- Test tkinter.filedialog on Windows
- Verify file path handling (spaces, special chars)

**Acceptance Criteria:**
- ✅ Window opens and closes cleanly
- ✅ File browser shows native Windows dialog
- ✅ Selected file paths display correctly

---

### Phase 2: CSV Converter GUI (3 hours)

**Step 2.1: Create CSVConverterTab Widget**

File: `gui/csv_tab.py`

```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
import csv_converter

class CSVConverterTab(ttk.Frame):
    """CSV to XLSX conversion tab"""

    def __init__(self, parent):
        super().__init__(parent)
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        """Build UI layout"""
        # Title
        ttk.Label(self, text="CSV to XLSX Converter",
                  font=("Arial", 14, "bold")).grid(row=0, column=0,
                  columnspan=3, pady=10)

        # Input file row
        ttk.Label(self, text="Input CSV File:").grid(row=1, column=0,
                  sticky='w', padx=10, pady=5)
        ttk.Entry(self, textvariable=self.input_path,
                  width=50).grid(row=1, column=1, padx=5)
        ttk.Button(self, text="Browse...",
                   command=self.browse_input).grid(row=1, column=2,
                   padx=10)

        # Output file row
        ttk.Label(self, text="Output XLSX File:").grid(row=2, column=0,
                  sticky='w', padx=10, pady=5)
        ttk.Entry(self, textvariable=self.output_path,
                  width=50).grid(row=2, column=1, padx=5)
        ttk.Button(self, text="Browse...",
                   command=self.browse_output).grid(row=2, column=2,
                   padx=10)

        # Convert button
        self.convert_btn = ttk.Button(self, text="Convert",
                                      command=self.convert)
        self.convert_btn.grid(row=3, column=0, columnspan=3, pady=15)

        # Status text area
        ttk.Label(self, text="Status:").grid(row=4, column=0,
                  sticky='nw', padx=10)
        self.status_text = tk.Text(self, height=15, width=70,
                                    state='disabled')
        self.status_text.grid(row=5, column=0, columnspan=3,
                              padx=10, pady=5)

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

    def convert(self):
        """Execute conversion in background thread"""
        input_path = self.input_path.get()
        output_path = self.output_path.get()

        # Validate
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select both files")
            return

        # Disable button during processing
        self.convert_btn.config(state='disabled')
        self.log("Starting conversion...")

        # Run in thread
        thread = threading.Thread(target=self._convert_worker,
                                   args=(input_path, output_path))
        thread.daemon = True
        thread.start()

    def _convert_worker(self, input_path, output_path):
        """Worker thread for conversion"""
        try:
            # Call existing converter
            row_count = csv_converter.convert_csv_to_xlsx(input_path,
                                                          output_path)

            # Success
            self.log(f"✅ Success! Converted {row_count} rows")
            self.log(f"Output: {output_path}")
            messagebox.showinfo("Success",
                               f"Converted {row_count} rows\n{output_path}")

        except Exception as e:
            # Error
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))

        finally:
            # Re-enable button
            self.convert_btn.config(state='normal')
```

**Step 2.2: Integrate Tab into MainWindow**

**Step 2.3: Test CSV Conversion**
- Test valid CSV → XLSX conversion
- Test invalid inputs (missing files, wrong extensions)
- Test error handling (malformed CSV)
- Test UI responsiveness during conversion

**Acceptance Criteria:**
- ✅ File browsers work correctly
- ✅ Conversion succeeds for valid inputs
- ✅ Errors display user-friendly messages
- ✅ UI remains responsive during conversion

---

### Phase 3: Attendance Processor GUI (4 hours)

**Step 3.1: Create AttendanceProcessorTab Widget**

File: `gui/attendance_tab.py`

Similar structure to CSVConverterTab, additional features:
- Config file picker (default: rule.yaml)
- TextRedirector integration (capture print statements)
- Real-time log updates

```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
from pathlib import Path

from config import RuleConfig
from processor import AttendanceProcessor
from gui.utils import TextRedirector

class AttendanceProcessorTab(ttk.Frame):
    """Attendance data processing tab"""

    def __init__(self, parent):
        super().__init__(parent)
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.config_path = tk.StringVar(value="rule.yaml")
        self.create_widgets()

    def create_widgets(self):
        """Build UI layout"""
        # Title
        ttk.Label(self, text="Attendance Data Processor",
                  font=("Arial", 14, "bold")).grid(row=0, column=0,
                  columnspan=4, pady=10)

        # Input file row
        ttk.Label(self, text="Input Excel File:").grid(row=1, column=0,
                  sticky='w', padx=10, pady=5)
        ttk.Entry(self, textvariable=self.input_path,
                  width=45).grid(row=1, column=1, padx=5)
        ttk.Button(self, text="Browse...",
                   command=self.browse_input).grid(row=1, column=2,
                   padx=5)

        # Output file row
        ttk.Label(self, text="Output Excel File:").grid(row=2, column=0,
                  sticky='w', padx=10, pady=5)
        ttk.Entry(self, textvariable=self.output_path,
                  width=45).grid(row=2, column=1, padx=5)
        ttk.Button(self, text="Browse...",
                   command=self.browse_output).grid(row=2, column=2,
                   padx=5)

        # Config file row
        ttk.Label(self, text="Config File:").grid(row=3, column=0,
                  sticky='w', padx=10, pady=5)
        ttk.Entry(self, textvariable=self.config_path,
                  width=45).grid(row=3, column=1, padx=5)
        ttk.Button(self, text="Browse...",
                   command=self.browse_config).grid(row=3, column=2,
                   padx=5)
        ttk.Button(self, text="Default",
                   command=self.use_default_config).grid(row=3, column=3,
                   padx=5)

        # Process button
        self.process_btn = ttk.Button(self, text="Process",
                                      command=self.process)
        self.process_btn.grid(row=4, column=0, columnspan=4, pady=15)

        # Processing log
        ttk.Label(self, text="Processing Log:").grid(row=5, column=0,
                  sticky='nw', padx=10)
        self.log_text = tk.Text(self, height=15, width=75,
                                state='disabled')
        self.log_text.grid(row=6, column=0, columnspan=4,
                           padx=10, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=6, column=4, sticky='ns')
        self.log_text.config(yscrollcommand=scrollbar.set)

    def browse_input(self):
        """Open file dialog for input Excel"""
        path = filedialog.askopenfilename(
            title="Select Input Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"),
                      ("All Files", "*.*")]
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
            filetypes=[("YAML Files", "*.yaml *.yml"),
                      ("All Files", "*.*")]
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

    def process(self):
        """Execute processing in background thread"""
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        config_path = self.config_path.get()

        # Validate
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select input/output files")
            return

        if not Path(input_path).exists():
            messagebox.showerror("Error", f"Input file not found:\n{input_path}")
            return

        # Disable button during processing
        self.process_btn.config(state='disabled')
        self.log("=" * 70)
        self.log("🚀 Starting processing pipeline")
        self.log("=" * 70)

        # Run in thread
        thread = threading.Thread(target=self._process_worker,
                                   args=(input_path, output_path, config_path))
        thread.daemon = True
        thread.start()

    def _process_worker(self, input_path, output_path, config_path):
        """Worker thread for processing"""
        original_stdout = sys.stdout

        try:
            # Redirect print statements to log widget
            sys.stdout = TextRedirector(self.log_text)

            # Load config
            print(f"🔧 Loading configuration: {config_path}")
            config = RuleConfig.load_from_yaml(config_path)
            print(f"   ✓ Loaded config: {len(config.shifts)} shifts, "
                  f"{len(config.valid_users)} valid users")

            # Process (existing code)
            processor = AttendanceProcessor(config)
            processor.process(input_path, output_path)

            print()
            print("=" * 70)
            print(f"✅ Success! Output written to: {output_path}")
            print("=" * 70)

            # Success message
            messagebox.showinfo("Success",
                               f"Processing complete!\n\nOutput: {output_path}")

        except Exception as e:
            # Error
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc(file=sys.stdout)
            messagebox.showerror("Error", str(e))

        finally:
            # Restore stdout, re-enable button
            sys.stdout = original_stdout
            self.process_btn.config(state='normal')
```

**Step 3.2: Implement TextRedirector**

File: `gui/utils.py`

```python
import tkinter as tk

class TextRedirector:
    """Redirect stdout/stderr to tkinter Text widget"""

    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        """Write message to text widget (thread-safe)"""
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')
        self.text_widget.update_idletasks()

    def flush(self):
        """Required for file-like object interface"""
        pass
```

**Step 3.3: Test Attendance Processing**
- Test with real data (output1.xlsx)
- Test with invalid inputs
- Verify real-time log updates
- Test error scenarios (missing columns, invalid config)

**Acceptance Criteria:**
- ✅ Processing succeeds for valid inputs
- ✅ Log updates in real-time (no freezing)
- ✅ Errors display clearly
- ✅ Success message shows output path

---

### Phase 4: Main Window Integration (2 hours)

**Step 4.1: Create MainWindow**

File: `gui/main_window.py`

```python
import tkinter as tk
from tkinter import ttk, messagebox
from gui.csv_tab import CSVConverterTab
from gui.attendance_tab import AttendanceProcessorTab

class MainWindow:
    """Main application window"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Attendance & CSV Converter Tool v3.0.0")
        self.root.geometry("850x650")

        # Set icon (if available)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass  # Icon optional

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Build main window layout"""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=10, pady=10)

        title_label = ttk.Label(title_frame,
                                text="Attendance & CSV Converter Tool",
                                font=("Arial", 16, "bold"))
        title_label.pack()

        version_label = ttk.Label(title_frame,
                                  text="Version 3.0.0 - GUI Edition",
                                  font=("Arial", 10))
        version_label.pack()

        # Notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Add tabs
        self.csv_tab = CSVConverterTab(self.notebook)
        self.notebook.add(self.csv_tab, text="CSV Converter")

        self.attendance_tab = AttendanceProcessorTab(self.notebook)
        self.notebook.add(self.attendance_tab, text="Attendance Processor")

        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready",
                                    relief='sunken', anchor='w')
        self.status_bar.pack(fill='x', side='bottom')

    def on_closing(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Exit application?"):
            self.root.destroy()

    def run(self):
        """Start main event loop"""
        self.root.mainloop()
```

**Step 4.2: Create GUI Entry Point**

File: `main_gui.py`

```python
#!/usr/bin/env python3
"""GUI Entry Point for Attendance & CSV Converter Tool

Windows-friendly graphical interface for non-technical users.

Author: Development Team
Version: 3.0.0 (GUI Edition)
"""

import sys
from gui.main_window import MainWindow

def main():
    """Launch GUI application"""
    try:
        app = MainWindow()
        app.run()
        return 0
    except Exception as e:
        import traceback
        print(f"Fatal error: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

**Step 4.3: Test Complete Application**
- Test tab switching
- Test both tools end-to-end
- Test window resizing, closing
- Test on clean Windows VM

**Acceptance Criteria:**
- ✅ Both tabs functional
- ✅ Window closes gracefully
- ✅ No console window appears (after packaging)

---

### Phase 5: Packaging & Distribution (3 hours)

**Step 5.1: Create Application Icon**

Create `icon.ico` (256x256 recommended):
- Use online converter (PNG → ICO)
- Simple icon: spreadsheet + clock symbol
- Save as `icon.ico` in project root

**Step 5.2: Create PyInstaller Spec File**

File: `build_exe.py`

```python
#!/usr/bin/env python3
"""Build standalone Windows executable using PyInstaller"""

import PyInstaller.__main__
import os
from pathlib import Path

def build():
    """Build executable"""

    # Paths
    project_root = Path(__file__).parent
    icon_path = project_root / "icon.ico"
    rule_yaml = project_root / "rule.yaml"

    # PyInstaller arguments
    args = [
        'main_gui.py',                     # Entry point
        '--name=AttendanceProcessor',      # Executable name
        '--onefile',                       # Single file
        '--windowed',                      # No console window
        f'--icon={icon_path}',            # Application icon
        f'--add-data={rule_yaml};.',      # Bundle rule.yaml
        '--clean',                         # Clean cache
        '--noconfirm',                     # Overwrite without prompt

        # Hidden imports (if needed)
        '--hidden-import=openpyxl',
        '--hidden-import=pandas',
        '--hidden-import=yaml',
        '--hidden-import=xlsxwriter',
    ]

    print("Building executable...")
    print(f"Icon: {icon_path}")
    print(f"Config: {rule_yaml}")

    PyInstaller.__main__.run(args)

    print("\n" + "=" * 70)
    print("Build complete!")
    print("Executable: dist/AttendanceProcessor.exe")
    print("=" * 70)

if __name__ == '__main__':
    build()
```

**Step 5.3: Build Executable**

```bash
# Install PyInstaller
pip install pyinstaller

# Run build script
python build_exe.py

# Test executable
./dist/AttendanceProcessor.exe
```

**Step 5.4: Test Packaged Executable**

**Test on Clean Windows VM:**
- No Python installed
- No dependencies installed
- Fresh Windows 10/11 install

**Test Cases:**
1. Double-click AttendanceProcessor.exe → opens without errors
2. CSV conversion works end-to-end
3. Attendance processing works end-to-end
4. Error handling works (invalid files)
5. File dialogs show correctly
6. rule.yaml bundled correctly (default config works)

**Acceptance Criteria:**
- ✅ Executable runs on clean Windows (no Python)
- ✅ No console window appears
- ✅ All features work identically to source version
- ✅ Executable size <25MB
- ✅ No missing DLL errors

---

### Phase 6: Documentation & Deployment (1 hour)

**Step 6.1: Create User Guide**

File: `docs/user-guide-gui.md`

```markdown
# User Guide - Attendance & CSV Converter Tool (GUI)

## Installation

1. Download `AttendanceProcessor.exe` from [shared folder]
2. Save to desired location (e.g., Desktop, Documents)
3. Double-click to launch

**No installation required!**

## Using CSV Converter

1. Launch AttendanceProcessor.exe
2. Select "CSV Converter" tab
3. Click "Browse..." next to Input CSV File
4. Select your CSV file
5. Click "Browse..." next to Output XLSX File
6. Choose save location and filename
7. Click "Convert"
8. Wait for success message
9. Open output file in Excel

## Using Attendance Processor

1. Launch AttendanceProcessor.exe
2. Select "Attendance Processor" tab
3. Click "Browse..." next to Input Excel File
4. Select biometric log file (.xlsx)
5. Click "Browse..." next to Output Excel File
6. Choose save location and filename
7. (Optional) Change config file (or leave default)
8. Click "Process"
9. Watch processing log for progress
10. Wait for success message
11. Open output file in Excel

## Troubleshooting

**Error: "File not found"**
- Check input file path is correct
- Ensure file is not open in Excel

**Error: "Permission denied"**
- Close output file if open in Excel
- Choose different output location

**Processing takes too long**
- Large files (>10,000 rows) may take 10-20 seconds
- Watch log for progress updates

**Application won't open**
- Ensure Windows 10 or later
- Try running as Administrator (right-click → Run as administrator)

## Support

Contact IT Support for assistance.
```

**Step 6.2: Create README-GUI.md**

File: `README-GUI.md`

**Content:** Overview of GUI version, screenshots (if available), installation instructions for end users

**Step 6.3: Update Main README.md**

Add section:
```markdown
## GUI Version (Windows)

For non-technical users, download the standalone Windows application:

**Download:** [AttendanceProcessor.exe](link)

**Features:**
- ✅ No Python installation required
- ✅ Point-and-click interface
- ✅ Native Windows file dialogs
- ✅ Real-time progress updates
- ✅ User-friendly error messages

**Usage:** Double-click AttendanceProcessor.exe and follow on-screen instructions.

See [GUI User Guide](docs/user-guide-gui.md) for detailed instructions.
```

**Acceptance Criteria:**
- ✅ User guide covers all features
- ✅ Troubleshooting section addresses common issues
- ✅ README updated with GUI info

---

## Testing Strategy

### Manual Testing Checklist

**GUI Functionality:**
- [ ] Window opens without errors
- [ ] Tabs switch correctly
- [ ] File browsers open native Windows dialogs
- [ ] Selected paths display in entry fields
- [ ] Buttons enable/disable correctly
- [ ] Status/log text updates in real-time
- [ ] Window closes gracefully

**CSV Converter:**
- [ ] Valid CSV → XLSX conversion succeeds
- [ ] Invalid CSV shows error message
- [ ] Missing input file shows error
- [ ] Output file path validation works
- [ ] Success message displays correctly
- [ ] UI remains responsive during conversion

**Attendance Processor:**
- [ ] Valid input → processing succeeds
- [ ] Invalid input shows error message
- [ ] Config file loading works
- [ ] Default config (rule.yaml) works
- [ ] Real-time log updates work
- [ ] Success message displays output path
- [ ] UI remains responsive during processing

**Error Handling:**
- [ ] Missing files show clear error
- [ ] Invalid file types show error
- [ ] Malformed data shows error
- [ ] Errors don't crash application
- [ ] Error messages user-friendly (no stack traces)

**Packaging:**
- [ ] Executable builds without errors
- [ ] Executable size <25MB
- [ ] No console window appears (--windowed)
- [ ] Icon displays correctly
- [ ] rule.yaml bundled correctly
- [ ] Works on clean Windows VM (no Python)

---

### Automated Testing (Future)

**Unit Tests:**
- Test TextRedirector class
- Test file path validation logic
- Test threading behavior (mock processing)

**Integration Tests:**
- Test CSV converter integration
- Test attendance processor integration
- Test config loading

**Note:** GUI testing difficult to automate, prioritize manual testing

---

## Security Considerations

**Input Validation:**
- ✅ File existence checked before processing
- ✅ File extensions validated (.csv, .xlsx, .yaml)
- ✅ Write permissions checked for output paths
- ✅ User whitelist enforced (existing validators.py)

**Packaging Security:**
- ✅ PyInstaller bundles dependencies (no external downloads)
- ✅ No network access required
- ✅ No admin rights required
- ✅ Executable signed (optional, recommended for production)

**Known Risks:**
- ⚠️ Excel formula injection (existing risk from CLI version)
- ⚠️ No file size limits (existing risk from CLI version)

**Mitigations:** Same as CLI version (see code-standards.md)

---

## Performance Considerations

**GUI Overhead:**
- Threading: +50ms startup overhead (negligible)
- Widget creation: +100ms (one-time)
- Text widget updates: +10ms per log line (acceptable)
- Total overhead: <200ms (acceptable for user workflow)

**Processing Performance:**
- Identical to CLI version (same backend code)
- Threading prevents UI freeze
- Large files (10,000+ rows): 10-20s processing time
- Memory usage: Same as CLI version

**Optimization Opportunities:**
- Add progress bar (% complete)
- Implement "Cancel" button
- Batch processing mode (future)

---

## Deployment Plan

### Distribution Method

**Option 1: Shared Network Drive** (Recommended for internal use)
```
\\company\shared\Tools\AttendanceProcessor\
├── AttendanceProcessor.exe
├── README.txt
└── UserGuide.pdf
```

**Option 2: Email Distribution**
- Zip AttendanceProcessor.exe + README
- Email to users with installation instructions
- Note: Some email systems block .exe files (use .zip)

**Option 3: Internal Software Repository**
- Upload to company software portal
- Users download from portal
- Centralized version control

---

### Version Control

**Semantic Versioning:**
- v3.0.0: Initial GUI release
- v3.0.x: Bug fixes
- v3.x.0: New GUI features
- v4.0.0: Major changes (breaking)

**Release Process:**
1. Test on development machine
2. Build executable with build_exe.py
3. Test on clean Windows VM
4. Update version in main_gui.py, README
5. Create release notes
6. Distribute executable

---

### Update Strategy

**Minor Updates (Bug Fixes):**
1. Fix code
2. Rebuild executable
3. Replace old .exe with new .exe
4. Notify users via email

**Major Updates (New Features):**
1. Develop features
2. Test thoroughly
3. Update documentation
4. Rebuild executable
5. Distribute with changelog
6. Provide migration guide (if needed)

---

## Risks & Mitigations

### Risk 1: PyInstaller Antivirus False Positives

**Probability:** Medium
**Impact:** High (users can't run executable)

**Mitigation:**
- Code-sign executable with certificate (recommended)
- Submit to antivirus vendors for whitelisting
- Document antivirus exclusion instructions
- Provide VirusTotal scan link for verification

---

### Risk 2: Windows Updates Break Compatibility

**Probability:** Low
**Impact:** Medium

**Mitigation:**
- Test on latest Windows 10/11 before release
- Pin PyInstaller version (>=6.0.0)
- Include Windows version in system requirements
- Maintain Windows VM for testing

---

### Risk 3: Missing Dependencies in Packaged Executable

**Probability:** Low
**Impact:** High (features don't work)

**Mitigation:**
- Specify --hidden-import for all dependencies
- Test executable on clean VM (no Python)
- Include comprehensive manual test checklist
- Log errors to debug.log file

---

### Risk 4: GUI Freezing During Processing

**Probability:** Low (mitigated by threading)
**Impact:** Medium (bad user experience)

**Mitigation:**
- Use threading for all long-running operations
- Test with large files (10,000+ rows)
- Add "Processing..." status message
- Consider progress bar (future enhancement)

---

### Risk 5: User Overwrites Input File

**Probability:** Low
**Impact:** Medium (data loss)

**Mitigation:**
- Output file browser defaults to different name
- Warn if output path equals input path
- Recommend saving output to different folder (documentation)

---

## Estimated Timeline

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Setup & Prototyping | 2 hours |
| 2 | CSV Converter GUI | 3 hours |
| 3 | Attendance Processor GUI | 4 hours |
| 4 | Main Window Integration | 2 hours |
| 5 | Packaging & Distribution | 3 hours |
| 6 | Documentation | 1 hour |
| **Total** | **Development** | **15 hours** |
| | Testing | 3 hours |
| | Deployment | 1 hour |
| **Grand Total** | | **19 hours** |

**Complexity:** Medium
- Straightforward tkinter GUI
- No changes to core logic
- Well-documented packaging tools
- Comprehensive testing required

---

## Future Enhancements (Out of Scope)

**v3.1.0:**
- [ ] Progress bar with % complete
- [ ] "Cancel" button for long-running tasks
- [ ] Drag-and-drop file support
- [ ] Recent files list
- [ ] Settings dialog (save preferences)

**v3.2.0:**
- [ ] Batch processing (multiple files)
- [ ] Excel file preview (first 10 rows)
- [ ] Config editor GUI (edit rule.yaml)
- [ ] Export debug log button

**v4.0.0:**
- [ ] Multi-language support
- [ ] Scheduled processing (Windows Task Scheduler integration)
- [ ] Email notifications
- [ ] Cloud storage integration (OneDrive, SharePoint)

---

## Unresolved Questions

1. **Icon Design:** Who creates icon.ico? (External designer or placeholder?)
   - **Recommendation:** Use simple placeholder icon initially (Excel sheet + clock), improve later

2. **Code Signing:** Do we need signed executable for corporate environment?
   - **Recommendation:** Check with IT security team, may be required for enterprise deployment

3. **Distribution Method:** Network drive vs email vs software portal?
   - **Recommendation:** Network drive for MVP, migrate to software portal later

4. **Support Process:** Who handles user support requests?
   - **Recommendation:** Document common issues in user guide, escalate complex issues to development team

5. **Testing Environment:** Is Windows VM available for testing?
   - **Recommendation:** Use company VM infrastructure or local VirtualBox/Hyper-V

---

## Conclusion

This plan provides comprehensive, actionable roadmap for Windows GUI wrapper. Implementation straightforward using tkinter (built-in, lightweight). Packaging with PyInstaller creates standalone executable requiring no installation.

**Key Strengths:**
- Zero changes to core logic (processor.py unchanged)
- Minimal dependencies (tkinter built-in)
- Single executable distribution (easy deployment)
- Preserves all CLI functionality
- Threading prevents UI freezing

**Key Recommendations:**
- Use tkinter (not PyQt/wxPython)
- Package with PyInstaller --onefile --windowed
- Test thoroughly on clean Windows VM
- Consider code signing for enterprise deployment
- Start with MVP, iterate based on user feedback

**Next Steps:**
1. Review plan with stakeholders
2. Set up development environment (Windows machine)
3. Begin Phase 1 (Setup & Prototyping)
4. Iterate through phases 2-6
5. Deploy to pilot user group
6. Gather feedback, iterate

---

**Plan saved to:** `/home/silver/windows_project/plans/251106-windows-gui-wrapper-plan.md`
**Ready for implementation!**
