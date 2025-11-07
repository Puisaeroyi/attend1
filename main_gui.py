#!/usr/bin/env python3
"""
GUI Entry Point for Attendance & CSV Converter Tool

Windows-friendly graphical interface for non-technical users.
Provides tabbed interface with CSV Converter and Attendance Processor.

Author: Development Team
Version: 3.0.0 (GUI Edition)
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from gui.main_window import MainWindow
    from gui.styles import apply_default_styling
except ImportError as e:
    print(f"Error importing GUI modules: {e}", file=sys.stderr)
    print("Make sure all GUI files are present in the gui/ directory.", file=sys.stderr)
    sys.exit(1)


def main():
    """Launch GUI application"""
    try:
        # Create main window
        app = MainWindow()

        # Apply default styling
        apply_default_styling(app.root)

        # Start main event loop
        app.run()
        return 0

    except KeyboardInterrupt:
        print("\nApplication interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        print("\nFull traceback:", file=sys.stderr)
        traceback.print_exc()

        # Try to show error dialog if GUI is available
        try:
            import tkinter as tk
            from tkinter import messagebox

            error_root = tk.Tk()
            error_root.withdraw()  # Hide the main window
            messagebox.showerror(
                "Fatal Error",
                f"The application encountered a fatal error:\n\n{e}\n\n"
                "Please contact IT support for assistance."
            )
            error_root.destroy()
        except:
            pass  # Failed to show error dialog

        return 1


if __name__ == '__main__':
    sys.exit(main())