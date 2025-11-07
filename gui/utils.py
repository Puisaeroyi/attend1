"""
GUI Utility Functions and Classes

Contains helper classes and functions for the GUI interface,
including optimized text redirection for performance.
"""

import tkinter as tk
import sys
import queue
import threading
from pathlib import Path


class QueuedTextRedirector:
    """Redirect stdout/stderr to tkinter Text widget using queue for performance

    This implementation uses a queue to buffer messages and batch updates,
    preventing GUI freezing during heavy processing.
    """

    def __init__(self, text_widget, parent_widget):
        """Initialize queued text redirector

        Args:
            text_widget: tkinter Text widget to redirect output to
            parent_widget: Parent widget for scheduling updates
        """
        self.text_widget = text_widget
        self.parent_widget = parent_widget
        self.message_queue = queue.Queue()
        self.is_running = True

        # Start queue polling in main thread (50ms intervals)
        self._schedule_update()

    def write(self, message):
        """Write message to queue (called from worker thread)

        Args:
            message: Message to write
        """
        if message.strip():  # Only queue non-empty messages
            self.message_queue.put(message)

    def flush(self):
        """Required for file-like object interface"""
        pass

    def _schedule_update(self):
        """Schedule next UI update using after() - runs in main thread"""
        if self.is_running:
            self._process_queue()
            self.parent_widget.after(50, self._schedule_update)

    def _process_queue(self):
        """Process all queued messages and update UI - runs in main thread"""
        messages_to_write = []

        # Collect all available messages (up to 20 per batch)
        try:
            for _ in range(20):
                message = self.message_queue.get_nowait()
                messages_to_write.append(message)
        except queue.Empty:
            pass

        # Batch update UI if we have messages
        if messages_to_write:
            self.text_widget.config(state='normal')
            for msg in messages_to_write:
                self.text_widget.insert(tk.END, msg)
            self.text_widget.see(tk.END)
            self.text_widget.config(state='disabled')

    def stop(self):
        """Stop queue polling"""
        self.is_running = False


class TextRedirector:
    """Legacy redirect stdout/stderr to tkinter Text widget (kept for compatibility)"""

    def __init__(self, text_widget):
        """Initialize text redirector

        Args:
            text_widget: tkinter Text widget to redirect output to
        """
        self.text_widget = text_widget

    def write(self, message):
        """Write message to text widget (thread-safe)

        Args:
            message: Message to write
        """
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')
        self.text_widget.update_idletasks()

    def flush(self):
        """Required for file-like object interface"""
        pass


def validate_file_path(file_path, extensions=None, must_exist=True):
    """Validate file path and extension

    Args:
        file_path: Path to validate
        extensions: List of allowed extensions (e.g., ['.csv', '.xlsx'])
        must_exist: If True, file must exist

    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_path:
        return False, "No file path provided"

    path = Path(file_path)

    # Check if file exists (if required)
    if must_exist and not path.exists():
        return False, f"File not found: {file_path}"

    # Check extension
    if extensions:
        if path.suffix.lower() not in [ext.lower() for ext in extensions]:
            return False, f"Invalid file extension. Allowed: {', '.join(extensions)}"

    return True, ""


def check_write_permissions(directory_path):
    """Check if we have write permissions to directory

    Args:
        directory_path: Directory path to check

    Returns:
        tuple: (can_write, error_message)
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return False, "Directory does not exist"

        # Try to create a test file
        test_file = path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True, ""
    except Exception as e:
        return False, f"No write permission: {e}"


def center_window(window):
    """Center a tkinter window on screen

    Args:
        window: tkinter window to center
    """
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


def get_file_filters(file_types):
    """Convert file types list to tkinter filedialog format

    Args:
        file_types: Dictionary of file types
        e.g., {'CSV Files': '*.csv', 'Excel Files': '*.xlsx'}

    Returns:
        List of tuples for filedialog
    """
    filters = []
    for label, pattern in file_types.items():
        filters.append((label, pattern))
    filters.append(("All Files", "*.*"))
    return filters


def format_file_size(size_bytes):
    """Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"