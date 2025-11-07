# Phase 01: Research & Analysis

**Date:** 2025-11-07
**Priority:** HIGH
**Status:** ⏸ Pending
**Progress:** 0%

---

## Context Links

- [Main Plan](./plan.md)
- [Codebase Summary](/home/silver/windows_project/docs/codebase-summary.md)
- [Code Standards](/home/silver/windows_project/docs/code-standards.md)
- [Current Rule v9.0](/home/silver/windows_project/rule.yaml)

---

## Overview

Deep dive into rule v9.0 → v10.0 differences + GUI performance bottlenecks.

**Duration:** 2 hours
**Dependencies:** None
**Deliverable:** Research report with findings, recommendations

---

## Key Insights

### Rule v10.0 Changes

**1. Terminology Mapping**
```
Old (v9.0)          → New (v10.0)
------------------    ---------------------
First In            → Check-in
Break Out           → Break Time Out
Break In            → Break Time In
Last Out            → Check Out Record
```

**2. Late Marking Logic (NEW FEATURE)**

**Current (v9.0):**
- Grace period = advisory buffer (no enforcement)
- No late marking in output
- Grace period mentioned but not implemented

**Target (v10.0):**
- Grace period = hard cutoff boundary
- Late status calculated, displayed in output
- Two status columns: "Check-in Status", "Break Time In Status"

**Rules:**
```python
# Check-in Status
if check_in_time <= (shift_start + timedelta(minutes=4, seconds=59)):
    status = "On Time"
elif check_in_time >= (shift_start + timedelta(minutes=5)):
    status = "Late"

# Shift-specific examples
# Shift A (starts 06:00):
#   06:04:59 = On Time
#   06:05:00 = Late

# Shift B (starts 14:00):
#   14:04:59 = On Time
#   14:05:00 = Late

# Shift C (starts 22:00):
#   22:04:59 = On Time
#   22:05:00 = Late
```

```python
# Break Time In Status
if break_in_time <= (break_end_time + timedelta(minutes=4, seconds=59)):
    status = "On Time"
elif break_in_time >= (break_end_time + timedelta(minutes=5)):
    status = "Late"

# Shift-specific examples
# Shift A break ends 10:30:
#   10:34:59 = On Time
#   10:35:00 = Late

# Shift B break ends 18:30:
#   18:34:59 = On Time
#   18:35:00 = Late

# Shift C break ends 02:45:
#   02:49:59 = On Time
#   02:50:00 = Late
```

**3. C Shift Break Search Range Extension**
- Old: `01:50-02:45`
- New: `01:50-02:50`
- Impact: Captures break-ins up to 02:50 (grace period 05:00 after 02:45)

**4. Output Schema Changes**
```
Old Columns:
Date | ID | Name | Shift | First In | Break Out | Break In | Last Out

New Columns:
Date | ID | Name | Shift | Check-in | Check-in Status | Break Time Out | Break Time In | Break Time In Status | Check Out Record
```

### GUI Performance Issues

**Current Architecture (v3.0.0):**
- Threading: `threading.Thread` with daemon mode
- Output redirection: `TextRedirector` class (custom stdout wrapper)
- Update mechanism: `self.after(0, callback)` for UI updates
- Progress feedback: Print statements during processing

**Identified Bottlenecks:**

1. **Text Widget Updates (MAJOR)**
   - Every print statement triggers UI update
   - No buffering/debouncing
   - `self.log_text.insert()` + `self.log_text.see()` on every line
   - For 1000-row dataset: ~50+ print statements = 50+ UI updates

2. **File I/O Blocking (MEDIUM)**
   - Excel read/write operations block worker thread
   - No progress indication during I/O
   - Large files (10k+ rows) cause perceived freeze

3. **Single Worker Thread (MINOR)**
   - Only one thread per operation
   - CSV + Attendance tabs can't run parallel
   - No thread pool for reusability

4. **No Progress Indicators (UX)**
   - No progress bar
   - No row count updates
   - No percentage completion
   - Users don't know if app is frozen or working

**Performance Measurements Needed:**
- Baseline: Process 10k rows, measure time + UI lag
- Profile: Identify hotspots with cProfile
- Memory: Check for leaks during large file processing

---

## Requirements

### Functional Requirements

**FR-01:** Update all internal variables from v9.0 → v10.0 terminology
**FR-02:** Implement late marking logic with 04:59/05:00 boundary
**FR-03:** Add "Check-in Status" column to output
**FR-04:** Add "Break Time In Status" column to output
**FR-05:** Extend C shift break search range to 01:50-02:50
**FR-06:** Calculate status for blank values (handle missing check-in/break-in)
**FR-07:** GUI must remain responsive during processing
**FR-08:** Progress feedback must update in real-time

### Non-Functional Requirements

**NFR-01:** No performance regression (< current 0.202s for 199 rows)
**NFR-02:** GUI response time < 100ms for user actions
**NFR-03:** Support files up to 50k rows without freezing
**NFR-04:** Thread-safe operations (no race conditions)
**NFR-05:** Backward compatible with existing tests
**NFR-06:** Memory usage < 200MB for 10k rows

---

## Architecture

### Rule v10.0 Architecture

**Affected Components:**

```
config.py (ShiftConfig)
├── Add: check_in_late_threshold (timedelta)
├── Add: break_in_late_threshold (timedelta)
└── Modify: break search ranges (C shift)

processor.py (AttendanceProcessor)
├── Rename: _find_first_in() → _find_check_in()
├── Rename: _find_last_out() → _find_check_out()
├── Add: _calculate_check_in_status()
├── Add: _calculate_break_in_status()
└── Modify: _extract_attendance_events() (add status columns)

rule.yaml
├── Update: terminology (comments, field names)
├── Add: late_marking section
└── Modify: C_shift break_search_range
```

**Data Flow (New):**
```
Extract Check-in → Calculate Time Difference → Determine Status → Output
                        ↓
                  shift_start + grace_period
                        ↓
                  On Time | Late
```

### GUI Optimization Architecture

**Threading Model (Enhanced):**
```
Main Thread (Tk event loop)
│
├─ Worker Thread (processing)
│  │
│  ├─ File I/O (chunked reads)
│  ├─ Processing (processor.py)
│  └─ Progress Queue (updates)
│     │
│     └→ Main Thread (queue polling)
│
└─ UI Update Thread (debounced)
   │
   ├─ Batch log updates (every 100ms)
   ├─ Progress bar updates
   └─ Status text updates
```

**Optimization Strategy:**
1. **Queue-based updates:** Worker → Queue → Main thread polling
2. **Debouncing:** Batch UI updates (max 10/sec)
3. **Chunked processing:** Process in batches, update progress
4. **Async I/O:** Non-blocking file operations (if needed)

---

## Related Code Files

### Rule v10.0 Upgrade
- `/home/silver/windows_project/config.py` (ShiftConfig dataclass)
- `/home/silver/windows_project/processor.py` (processing logic)
- `/home/silver/windows_project/rule.yaml` (configuration)
- `/home/silver/windows_project/tests/test_scenarios.py` (scenario tests)

### GUI Optimization
- `/home/silver/windows_project/gui/attendance_tab.py` (worker thread)
- `/home/silver/windows_project/gui/csv_tab.py` (worker thread)
- `/home/silver/windows_project/gui/main_window.py` (UI management)
- `/home/silver/windows_project/gui/utils.py` (TextRedirector)

---

## Implementation Steps

### Step 1: Document Current Behavior (30 min)
- [ ] Profile current processing time (199 rows, 10k rows)
- [ ] Measure GUI responsiveness (time from click to feedback)
- [ ] Document current output schema
- [ ] List all uses of old terminology in codebase

### Step 2: Analyze Late Marking Requirements (45 min)
- [ ] Clarify boundary conditions (exactly 05:00 = Late?)
- [ ] Define behavior for missing values (blank check-in)
- [ ] Determine status for night shift (across midnight)
- [ ] Create truth table for all edge cases

### Step 3: Profile GUI Performance (45 min)
- [ ] Use cProfile on attendance processing (10k rows)
- [ ] Identify top 10 hotspots
- [ ] Measure TextRedirector overhead
- [ ] Test with/without log redirection

### Step 4: Summarize Findings (30 min)
- [ ] Create comparison table (v9.0 vs v10.0)
- [ ] Document GUI bottlenecks with evidence
- [ ] Recommend optimization priorities
- [ ] Identify risks and mitigations

---

## Todo List

- [ ] Profile current performance (199 rows, 10k rows)
- [ ] Measure GUI responsiveness baseline
- [ ] Document all v9.0 terminology locations
- [ ] Create late marking truth table
- [ ] Profile GUI with cProfile
- [ ] Identify top performance bottlenecks
- [ ] Document findings in research report
- [ ] Get stakeholder approval for approach

---

## Success Criteria

- ✅ Complete understanding of v9.0 → v10.0 changes
- ✅ All edge cases identified and documented
- ✅ Performance baseline established
- ✅ Bottlenecks identified with profiling data
- ✅ Optimization strategy validated
- ✅ Risks identified and mitigations planned

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Misunderstanding requirements | HIGH | MEDIUM | Validate with stakeholders early |
| Boundary confusion (04:59 vs 05:00) | HIGH | HIGH | Create comprehensive test cases |
| Performance baseline incorrect | MEDIUM | LOW | Multiple measurements, averaged |
| GUI profiling inconclusive | MEDIUM | LOW | Use multiple profiling tools |

---

## Security Considerations

- No security changes in this phase
- Existing validation remains (file paths, types)
- No new user input vectors

---

## Next Steps

After completion:
1. Create research report summary
2. Review findings with team
3. Proceed to Phase 02 (Config Upgrade)
4. Proceed to Phase 06 (GUI Performance Analysis) in parallel

---

**Phase Status:** PENDING
**Blocking Issues:** None
**Dependencies Met:** Yes
