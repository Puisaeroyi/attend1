# Phase 07: GUI Threading Optimization

**Date:** 2025-11-07
**Priority:** HIGH
**Status:** ⏸ Pending
**Progress:** 0%

---

## Context Links

- [Main Plan](./plan.md)
- [Phase 06: Performance Analysis](./phase-06-gui-performance-analysis.md)
- [Attendance Tab](/home/silver/windows_project/gui/attendance_tab.py)
- [Utils Module](/home/silver/windows_project/gui/utils.py)

---

## Overview

Optimize threading architecture for better UI responsiveness and performance.

**Duration:** 6 hours
**Dependencies:** Phase 06
**Deliverable:** Optimized threading with queue-based updates

---

## Key Insights

### Current Issues

**1. Blocking Text Updates**
```python
# Current TextRedirector - BLOCKS UI
class TextRedirector:
    def write(self, message):
        self.text_widget.config(state='normal')
        self.text_widget.insert(tk.END, message)  # BLOCKS main thread
        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')
        self.text_widget.update_idletasks()  # BLOCKS main thread
```

**2. No Buffering**
- Every print() → immediate UI update
- 100 print statements = 100 UI updates = 1-5s overhead

**3. Thread Safety Issues**
- Worker thread modifies UI directly (via self.after)
- No proper synchronization

---

## Requirements

**FR-07.1:** Implement queue-based logging (worker → main thread)
**FR-07.2:** Buffer log updates (batch every 100ms)
**FR-07.3:** Thread-safe UI updates only in main thread
**FR-07.4:** Progress reporting via queue
**FR-07.5:** Maintain all existing functionality

**NFR-07.1:** UI remains responsive (<100ms for user actions)
**NFR-07.2:** No race conditions or deadlocks
**NFR-07.3:** Memory usage doesn't grow unbounded

---

## Architecture

### New Threading Model

```
Main Thread (Tk event loop)
│
├─ Queue Polling (every 50ms)
│  │
│  ├─ Read log messages from queue
│  ├─ Batch update text widget (max 10 msgs/update)
│  └─ Update progress bar
│
└─ Worker Thread (daemon=False)
   │
   ├─ Processing logic
   ├─ Write logs → Queue (non-blocking)
   ├─ Send progress → Queue
   └─ Signal completion → Queue
```

### Queue-Based Communication

```python
import queue
from threading import Thread

class OptimizedAttendanceTab:
    def __init__(self, parent):
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.worker_thread = None

    def process(self):
        # Start worker
        self.worker_thread = Thread(target=self._worker, daemon=False)
        self.worker_thread.start()

        # Start queue polling
        self.poll_queues()

    def poll_queues(self):
        """Poll queues and update UI (runs in main thread)"""
        try:
            # Batch process log messages (max 10 per poll)
            messages = []
            for _ in range(10):
                try:
                    msg = self.log_queue.get_nowait()
                    messages.append(msg)
                except queue.Empty:
                    break

            if messages:
                self._update_log_batch(messages)

            # Check progress
            try:
                progress = self.progress_queue.get_nowait()
                self._update_progress(progress)
            except queue.Empty:
                pass

        except Exception as e:
            print(f"Error polling queues: {e}")

        # Continue polling if worker alive
        if self.worker_thread and self.worker_thread.is_alive():
            self.after(50, self.poll_queues)  # Poll every 50ms
```

---

## Implementation Steps

### Step 1: Create Queue-Based Logger (90 min)
```python
# gui/utils.py - Enhanced with queue support

import queue
import sys
from typing import Optional

class QueuedTextRedirector:
    """Queue-based stdout redirector for thread-safe GUI logging

    Usage:
        log_queue = queue.Queue()
        sys.stdout = QueuedTextRedirector(log_queue)

        # In main thread:
        while not log_queue.empty():
            message = log_queue.get()
            log_text.insert(tk.END, message)
    """

    def __init__(self, log_queue: queue.Queue):
        """Initialize redirector

        Args:
            log_queue: Queue to send messages to main thread
        """
        self.log_queue = log_queue
        self.buffer = []
        self.buffer_size = 5  # Buffer up to 5 lines before sending

    def write(self, message: str):
        """Write message to queue (thread-safe)

        Args:
            message: Text to log
        """
        if message and message.strip():
            self.buffer.append(message)

            # Flush buffer if full or at newline
            if len(self.buffer) >= self.buffer_size or '\n' in message:
                self.flush()

    def flush(self):
        """Flush buffered messages to queue"""
        if self.buffer:
            combined = ''.join(self.buffer)
            self.log_queue.put(combined)
            self.buffer = []

    def isatty(self):
        return False


class ProgressReporter:
    """Progress reporting for worker threads

    Usage:
        progress_queue = queue.Queue()
        reporter = ProgressReporter(progress_queue, total=1000)

        for i in range(1000):
            # ... do work ...
            reporter.update(i + 1)
    """

    def __init__(self, progress_queue: queue.Queue, total: int):
        """Initialize progress reporter

        Args:
            progress_queue: Queue to send progress updates
            total: Total number of items to process
        """
        self.progress_queue = progress_queue
        self.total = total
        self.current = 0
        self.last_reported = -1

    def update(self, current: int, message: str = ""):
        """Update progress

        Args:
            current: Current progress (0 to total)
            message: Optional status message
        """
        self.current = current
        percent = int((current / self.total) * 100) if self.total > 0 else 0

        # Only send update if progress changed significantly
        if percent != self.last_reported:
            self.progress_queue.put({
                'current': current,
                'total': self.total,
                'percent': percent,
                'message': message
            })
            self.last_reported = percent

    def complete(self, message: str = "Complete"):
        """Mark as complete

        Args:
            message: Completion message
        """
        self.progress_queue.put({
            'current': self.total,
            'total': self.total,
            'percent': 100,
            'message': message,
            'complete': True
        })
```

### Step 2: Update AttendanceProcessorTab (120 min)
```python
# gui/attendance_tab.py - Optimized version

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import sys
import os
from pathlib import Path

from config import RuleConfig
from processor import AttendanceProcessor
from gui.utils import QueuedTextRedirector, ProgressReporter


class AttendanceProcessorTab(ttk.Frame):
    """Optimized attendance processor tab with queue-based updates"""

    def __init__(self, parent):
        super().__init__(parent)
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.config_path = tk.StringVar(value="rule.yaml")

        # Threading and queue
        self.is_processing = False
        self.worker_thread = None
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()

        self.create_widgets()

    def create_widgets(self):
        """Build UI with progress bar"""
        # ... existing widgets ...

        # Process button
        self.process_btn = ttk.Button(
            self, text="Process", command=self.process
        )
        self.process_btn.grid(row=4, column=0, columnspan=4, pady=15)

        # Progress bar (NEW)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self,
            mode='determinate',
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(row=5, column=0, columnspan=4, padx=10, pady=5, sticky='ew')

        # Progress label (NEW)
        self.progress_label = ttk.Label(self, text="Ready")
        self.progress_label.grid(row=6, column=0, columnspan=4)

        # Processing log
        ttk.Label(self, text="Processing Log:").grid(
            row=7, column=0, sticky='nw', padx=10
        )
        self.log_text = tk.Text(
            self, height=12, width=75, state='disabled'
        )
        self.log_text.grid(row=8, column=0, columnspan=4, padx=10, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.grid(row=8, column=4, sticky='ns')
        self.log_text.config(yscrollcommand=scrollbar.set)

    def process(self):
        """Execute attendance data processing"""
        if self.is_processing:
            messagebox.showwarning("Busy", "Processing already in progress.")
            return

        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            messagebox.showerror("Validation Error", error_message)
            return

        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()
        config_path = self.config_path.get().strip()

        # Clear previous logs
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text="Starting...")

        # Start worker thread
        self.is_processing = True
        self.process_btn.config(state='disabled', text="Processing...")

        self.worker_thread = threading.Thread(
            target=self._worker,
            args=(input_path, output_path, config_path),
            daemon=False  # Changed from True for proper cleanup
        )
        self.worker_thread.start()

        # Start queue polling
        self.poll_queues()

    def _worker(self, input_path, output_path, config_path):
        """Worker thread with queue-based logging

        Args:
            input_path: Path to input Excel
            output_path: Path to output Excel
            config_path: Path to config YAML
        """
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            # Redirect stdout to queue
            sys.stdout = QueuedTextRedirector(self.log_queue)
            sys.stderr = QueuedTextRedirector(self.log_queue)

            # Load config
            print(f"🔧 Loading configuration: {config_path}")
            config = RuleConfig.load_from_yaml(config_path)
            print(f"   ✓ Loaded config: {len(config.shifts)} shifts, {len(config.valid_users)} users")

            # Create progress reporter
            # (Will need to integrate with processor for accurate progress)
            self.progress_queue.put({
                'percent': 10,
                'message': 'Configuration loaded'
            })

            print()
            print("=" * 70)
            print("🚀 Starting processing pipeline")
            print("=" * 70)

            # Process
            processor = AttendanceProcessor(config)
            processor.process(input_path, output_path)

            self.progress_queue.put({
                'percent': 100,
                'message': 'Processing complete',
                'complete': True
            })

            print()
            print("=" * 70)
            print(f"✅ Success! Output: {output_path}")
            print("=" * 70)

            # Signal success
            sys.stdout.flush()
            self.log_queue.put(('SUCCESS', output_path))

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

            # Signal error
            sys.stdout.flush()
            self.log_queue.put(('ERROR', str(e)))

        finally:
            # Restore stdout
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def poll_queues(self):
        """Poll queues and update UI (main thread only)"""
        try:
            # Process log messages (batch up to 10)
            messages = []
            for _ in range(10):
                try:
                    item = self.log_queue.get_nowait()

                    # Check for special messages
                    if isinstance(item, tuple):
                        status, data = item
                        if status == 'SUCCESS':
                            self.after(0, self._show_success, data)
                        elif status == 'ERROR':
                            self.after(0, self._show_error, data)
                    else:
                        messages.append(item)

                except queue.Empty:
                    break

            # Batch update log
            if messages:
                combined = ''.join(messages)
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, combined)
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')

            # Process progress updates
            try:
                progress = self.progress_queue.get_nowait()
                self.progress_var.set(progress['percent'])
                self.progress_label.config(
                    text=f"{progress['percent']}% - {progress.get('message', '')}"
                )

                # Check if complete
                if progress.get('complete'):
                    self._reset_button()

            except queue.Empty:
                pass

        except Exception as e:
            print(f"Error in poll_queues: {e}", file=sys.__stdout__)

        # Continue polling if worker alive
        if self.worker_thread and self.worker_thread.is_alive():
            self.after(50, self.poll_queues)  # Poll every 50ms
        else:
            # Worker finished, do final cleanup
            self.after(100, self._reset_button)

    def _show_success(self, output_path):
        """Show success dialog"""
        messagebox.showinfo(
            "Success",
            f"Processing complete!\n\nOutput: {output_path}"
        )

    def _show_error(self, error_msg):
        """Show error dialog"""
        messagebox.showerror("Error", f"Processing failed:\n\n{error_msg}")

    def _reset_button(self):
        """Reset UI to ready state"""
        self.is_processing = False
        self.process_btn.config(state='normal', text="Process")
        self.progress_label.config(text="Ready")
```

### Step 3: Update CSVConverterTab Similarly (60 min)
```python
# gui/csv_tab.py - Apply same queue-based pattern

# ... similar changes as attendance_tab.py ...
```

### Step 4: Add Progress Reporting to Processor (60 min)
```python
# processor.py - Optional: Add progress hooks

class AttendanceProcessor:
    def __init__(self, config: RuleConfig, progress_callback=None):
        self.config = config
        self.progress_callback = progress_callback

    def _report_progress(self, current, total, message=""):
        """Report progress to callback"""
        if self.progress_callback:
            self.progress_callback(current, total, message)

    def process(self, input_path, output_path):
        """Process with progress reporting"""
        df = self._load_excel(input_path)
        total_steps = 7

        self._report_progress(1, total_steps, "Filtering status")
        df = self._filter_valid_status(df)

        self._report_progress(2, total_steps, "Filtering users")
        df = self._filter_valid_users(df)

        self._report_progress(3, total_steps, "Detecting bursts")
        df = self._detect_bursts(df)

        # ... etc
```

---

## Todo List

- [ ] Create QueuedTextRedirector class
- [ ] Create ProgressReporter class
- [ ] Update AttendanceProcessorTab with queues
- [ ] Add progress bar to UI
- [ ] Update CSVConverterTab with queues
- [ ] Add progress reporting to processor (optional)
- [ ] Test with 10k rows (measure responsiveness)
- [ ] Verify no race conditions
- [ ] Test thread cleanup on cancel
- [ ] Update documentation

---

## Success Criteria

- ✅ UI remains responsive during processing (<100ms)
- ✅ No GUI freezing with large files (50k rows)
- ✅ Progress bar updates smoothly
- ✅ Log updates batched (not per-line)
- ✅ Thread-safe (no race conditions)
- ✅ Proper cleanup (no zombie threads)
- ✅ No memory leaks (queue doesn't grow unbounded)

---

## Performance Targets

| Metric | Before | Target | After |
|--------|--------|--------|-------|
| UI response time | 500-2000ms | <100ms | TBD |
| Processing 10k rows | ~30s | <30s | TBD |
| Log update overhead | 20-30% | <5% | TBD |
| Memory usage | ~150MB | <200MB | TBD |

---

## Next Steps

After completion:
1. Benchmark performance improvements
2. Proceed to Phase 08 (Additional Responsiveness)
3. Integration testing with rule v10.0

---

**Phase Status:** PENDING
