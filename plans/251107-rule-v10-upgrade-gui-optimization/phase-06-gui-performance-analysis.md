# Phase 06: GUI Performance Analysis

**Date:** 2025-11-07
**Priority:** HIGH
**Status:** ⏸ Pending
**Progress:** 0%

---

## Context Links

- [Main Plan](./plan.md)
- [Phase 01: Research](./phase-01-research-analysis.md)
- [Attendance Tab](/home/silver/windows_project/gui/attendance_tab.py)
- [CSV Tab](/home/silver/windows_project/gui/csv_tab.py)

---

## Overview

Profile GUI performance, identify bottlenecks, establish optimization priorities.

**Duration:** 3 hours
**Dependencies:** None (can run parallel with rule upgrade)
**Deliverable:** Performance report with profiling data, optimization recommendations

---

## Key Insights

### Current Architecture Analysis

**Threading Model:**
```python
# attendance_tab.py - Current implementation

def process(self):
    # Main thread
    thread = threading.Thread(
        target=self._process_worker,
        args=(input_path, output_path, config_path),
        daemon=True
    )
    thread.start()

def _process_worker(self, ...):
    # Worker thread
    sys.stdout = TextRedirector(self.log_text)  # Redirect output
    processor.process(input_path, output_path)  # Process data
    self.after(0, self._show_success, output_path)  # Update UI
```

**Identified Issues:**

1. **Text Widget Updates (CRITICAL)**
   - Every `print()` → `TextRedirector.write()` → `log_text.insert()`
   - No buffering → immediate UI update
   - Main thread must process every insert via `self.after(0, ...)`
   - For 10k rows: ~100+ print statements = 100+ UI updates
   - Each update blocks main thread for ~10-50ms
   - Total overhead: 1-5 seconds of UI lag

2. **No Progress Indicators (UX)**
   - User can't tell if processing or frozen
   - No percentage completion
   - No row count updates
   - No ETA estimation

3. **File I/O in Worker Thread (MINOR)**
   - Excel read/write blocks worker thread
   - No chunk-based processing
   - Large files (50k rows) cause long silence

4. **Thread Management (MINOR)**
   - Creates new thread per operation
   - No thread pool reuse
   - Daemon threads (can't clean up properly)

---

## Requirements

**FR-06.1:** Profile current GUI with cProfile (10k rows)
**FR-06.2:** Measure UI responsiveness (click-to-feedback time)
**FR-06.3:** Identify top 10 performance hotspots
**FR-06.4:** Measure TextRedirector overhead
**FR-06.5:** Document baseline performance metrics

**NFR-06.1:** Profiling doesn't interfere with normal operation
**NFR-06.2:** Results reproducible across multiple runs

---

## Architecture

### Profiling Strategy

**1. cProfile Analysis**
```python
import cProfile
import pstats

# Profile worker thread
def profile_processing():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run processing
    processor.process(input_path, output_path)

    profiler.disable()

    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

**2. UI Responsiveness Testing**
```python
import time

# Measure click-to-feedback time
start = time.perf_counter()
# Simulate button click
process_btn.invoke()
# Wait for first log update
while log_text.get('1.0', 'end').strip() == '':
    time.sleep(0.001)
end = time.perf_counter()

responsiveness_ms = (end - start) * 1000
```

**3. TextRedirector Overhead**
```python
# Test with and without redirection
import io

# Without redirection
start = time.perf_counter()
processor.process(input_path, output_path)
time_without = time.perf_counter() - start

# With redirection
sys.stdout = TextRedirector(log_text)
start = time.perf_counter()
processor.process(input_path, output_path)
time_with = time.perf_counter() - start

overhead_percent = ((time_with - time_without) / time_without) * 100
```

---

## Implementation Steps

### Step 1: Setup Profiling Environment (30 min)
```python
# Create profiling script: tools/profile_gui.py

import sys
import os
import cProfile
import pstats
import tkinter as tk
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import RuleConfig
from processor import AttendanceProcessor
from gui.utils import TextRedirector

def profile_processing(input_path, output_path, config_path):
    """Profile attendance processing with GUI redirection"""

    # Create dummy text widget
    root = tk.Tk()
    log_text = tk.Text(root)

    # Setup profiler
    profiler = cProfile.Profile()

    # Redirect output
    sys.stdout = TextRedirector(log_text)

    # Profile
    profiler.enable()

    config = RuleConfig.load_from_yaml(config_path)
    processor = AttendanceProcessor(config)
    processor.process(input_path, output_path)

    profiler.disable()

    # Restore stdout
    sys.stdout = sys.__stdout__

    # Analyze
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')

    print("\n=== TOP 20 FUNCTIONS BY CUMULATIVE TIME ===")
    stats.print_stats(20)

    print("\n=== TOP 20 FUNCTIONS BY TOTAL TIME ===")
    stats.sort_stats('tottime')
    stats.print_stats(20)

    # Clean up
    root.destroy()

if __name__ == '__main__':
    # Test with 10k row dataset
    profile_processing(
        'data/test_10k_rows.xlsx',
        'output/profiled.xlsx',
        'rule.yaml'
    )
```

### Step 2: Generate Test Datasets (30 min)
```python
# Create test data generator: tools/generate_test_data.py

import pandas as pd
from datetime import datetime, timedelta
import random

def generate_attendance_data(num_rows: int, output_path: str):
    """Generate realistic attendance test data

    Args:
        num_rows: Number of swipes to generate
        output_path: Output Excel file path
    """
    users = ['Silver_Bui', 'Capone', 'Minh', 'Trieu']
    shifts = ['A', 'B', 'C']

    records = []
    start_date = datetime(2025, 11, 1)

    for i in range(num_rows):
        user = random.choice(users)
        shift = random.choice(shifts)

        # Generate realistic timestamps
        day_offset = i // (len(users) * 4)  # 4 swipes per user per day
        date = start_date + timedelta(days=day_offset)

        if shift == 'A':
            base_time = datetime.combine(date, datetime.strptime('06:00', '%H:%M').time())
        elif shift == 'B':
            base_time = datetime.combine(date, datetime.strptime('14:00', '%H:%M').time())
        else:  # C
            base_time = datetime.combine(date, datetime.strptime('22:00', '%H:%M').time())

        # Add random offset
        offset = random.randint(-30, 480)  # -30min to +8hrs
        timestamp = base_time + timedelta(minutes=offset)

        record = {
            'ID': random.randint(1, 99),
            'Name': user,
            'Date': timestamp.strftime('%Y.%m.%d'),
            'Time': timestamp.strftime('%H:%M:%S'),
            'Type': 'F1',
            'Status': 'Success'
        }
        records.append(record)

    df = pd.DataFrame(records)
    df.to_excel(output_path, index=False)
    print(f"Generated {num_rows} records → {output_path}")

if __name__ == '__main__':
    # Generate test datasets
    generate_attendance_data(199, 'data/test_199_rows.xlsx')
    generate_attendance_data(1000, 'data/test_1k_rows.xlsx')
    generate_attendance_data(10000, 'data/test_10k_rows.xlsx')
    generate_attendance_data(50000, 'data/test_50k_rows.xlsx')
```

### Step 3: Run Profiling Tests (60 min)
```bash
# Profile different dataset sizes

# Baseline (199 rows)
python tools/profile_gui.py data/test_199_rows.xlsx output/199.xlsx rule.yaml > reports/profile_199.txt

# 1k rows
python tools/profile_gui.py data/test_1k_rows.xlsx output/1k.xlsx rule.yaml > reports/profile_1k.txt

# 10k rows
python tools/profile_gui.py data/test_10k_rows.xlsx output/10k.xlsx rule.yaml > reports/profile_10k.txt

# 50k rows
python tools/profile_gui.py data/test_50k_rows.xlsx output/50k.xlsx rule.yaml > reports/profile_50k.txt
```

### Step 4: Measure UI Responsiveness (30 min)
```python
# tools/measure_responsiveness.py

import tkinter as tk
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.attendance_tab import AttendanceProcessorTab

def measure_responsiveness():
    """Measure UI responsiveness metrics"""

    root = tk.Tk()
    tab = AttendanceProcessorTab(root)
    tab.pack()

    # Set test inputs
    tab.input_path.set('data/test_1k_rows.xlsx')
    tab.output_path.set('output/test.xlsx')
    tab.config_path.set('rule.yaml')

    # Measure click-to-first-log time
    start = time.perf_counter()

    # Simulate button click
    tab.process_btn.invoke()

    # Wait for first log entry
    while tab.log_text.get('1.0', 'end').strip() == '':
        root.update()
        time.sleep(0.001)

    first_log = time.perf_counter() - start

    print(f"Click-to-first-log: {first_log * 1000:.2f} ms")

    # Wait for completion
    while tab.is_processing:
        root.update()
        time.sleep(0.1)

    total_time = time.perf_counter() - start
    print(f"Total processing time: {total_time:.2f} s")

    root.destroy()

if __name__ == '__main__':
    measure_responsiveness()
```

### Step 5: Analyze Results (30 min)
```python
# tools/analyze_profile_results.py

import re
from pathlib import Path

def parse_profile_output(file_path):
    """Parse cProfile output and extract key metrics"""

    with open(file_path) as f:
        content = f.read()

    # Extract top functions
    cumulative_pattern = r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)\s+([\w.]+)'
    matches = re.findall(cumulative_pattern, content)

    print(f"\n=== Analysis: {file_path} ===")
    print(f"Top 10 functions by cumulative time:")

    for i, (cumtime, tottime, ncalls, funcname) in enumerate(matches[:10]):
        print(f"{i+1}. {funcname}")
        print(f"   Cumulative: {cumtime}s, Total: {tottime}s, Calls: {ncalls}")

    # Identify GUI-related functions
    gui_functions = [m for m in matches if 'Text' in m[3] or 'insert' in m[3] or 'Tk' in m[3]]

    if gui_functions:
        print(f"\nGUI-related hotspots:")
        for cumtime, tottime, ncalls, funcname in gui_functions[:5]:
            print(f"- {funcname}: {cumtime}s ({ncalls} calls)")

if __name__ == '__main__':
    for profile in Path('reports').glob('profile_*.txt'):
        parse_profile_output(profile)
```

---

## Todo List

- [ ] Create profiling script (profile_gui.py)
- [ ] Create test data generator
- [ ] Generate test datasets (199, 1k, 10k, 50k rows)
- [ ] Run profiling tests for each dataset
- [ ] Measure UI responsiveness
- [ ] Analyze cProfile output
- [ ] Identify top 10 bottlenecks
- [ ] Measure TextRedirector overhead
- [ ] Create performance report
- [ ] Prioritize optimization targets

---

## Success Criteria

- ✅ Profiling data collected for all dataset sizes
- ✅ Top 10 bottlenecks identified
- ✅ UI responsiveness measured (<100ms target?)
- ✅ TextRedirector overhead quantified
- ✅ Optimization priorities established
- ✅ Baseline metrics documented for comparison

---

## Expected Findings

Based on code review, expect to find:

1. **Text widget operations** - 30-50% of total time
2. **Pandas operations** - 20-30% (groupby, agg)
3. **Excel I/O** - 15-25% (openpyxl read/write)
4. **TextRedirector overhead** - 10-20%
5. **Datetime parsing** - 5-10%

---

## Next Steps

After completion:
1. Review findings with team
2. Proceed to Phase 07 (Threading Optimization)
3. Proceed to Phase 08 (Responsiveness Enhancement)

---

**Phase Status:** PENDING
