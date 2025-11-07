# Phase 03: Rule v10.0 Processing Logic

**Date:** 2025-11-07
**Priority:** HIGH
**Status:** ⏸ Pending
**Progress:** 0%

---

## Context Links

- [Main Plan](./plan.md)
- [Phase 02: Config Upgrade](./phase-02-rule-config-upgrade.md)
- [Processor Module](/home/silver/windows_project/processor.py)

---

## Overview

Implement late marking logic + terminology updates in processor.py.

**Duration:** 6 hours
**Dependencies:** Phase 02
**Deliverable:** Updated processor.py with status calculation

---

## Key Insights

### Processing Changes

**1. Method Renaming**
```python
# Old (v9.0)                    # New (v10.0)
_find_first_in()        →       _find_check_in()
_find_last_out()        →       _find_check_out()
# _detect_breaks()              # Keep same (internal name OK)
```

**2. Status Calculation Functions (NEW)**
```python
def _calculate_check_in_status(self, check_in: datetime, shift_cfg: ShiftConfig) -> str:
    """Calculate check-in status: On Time or Late"""

def _calculate_break_in_status(self, break_in: datetime, shift_cfg: ShiftConfig) -> str:
    """Calculate break-in status: On Time or Late"""
```

**3. Event Extraction Updates**
```python
# _extract_attendance_events() modifications:
# - Call renamed methods
# - Calculate statuses
# - Add status columns to output
# - Handle blank values (no status for blank times)
```

---

## Requirements

**FR-03.1:** Rename _find_first_in → _find_check_in
**FR-03.2:** Rename _find_last_out → _find_check_out
**FR-03.3:** Implement _calculate_check_in_status
**FR-03.4:** Implement _calculate_break_in_status
**FR-03.5:** Update _extract_attendance_events to add status columns
**FR-03.6:** Handle blank values (return empty string for status)
**FR-03.7:** Maintain performance (no regression)

---

## Architecture

### Status Calculation Flow
```
_extract_attendance_events()
    ↓
For each shift instance:
    ├─ Extract Check-in time
    │   ├─ If found: Calculate status
    │   └─ If blank: status = ""
    │
    ├─ Extract Break Time Out
    │
    ├─ Extract Break Time In
    │   ├─ If found: Calculate status
    │   └─ If blank: status = ""
    │
    └─ Extract Check Out Record
```

### Status Logic
```python
def _calculate_check_in_status(check_in: datetime, shift_cfg: ShiftConfig) -> str:
    if not check_in or pd.isna(check_in):
        return ""

    # Use ShiftConfig.is_check_in_late()
    if shift_cfg.is_check_in_late(check_in):
        return "Late"
    else:
        return "On Time"
```

---

## Implementation Steps

### Step 1: Rename Methods (30 min)
```python
# processor.py

# OLD
def _find_first_in(self, group, shift_cfg):
    """Find First In timestamp"""

# NEW
def _find_check_in(self, group, shift_cfg):
    """Find Check-in timestamp (v10.0 terminology)

    Args:
        group: DataFrame group for shift instance
        shift_cfg: ShiftConfig for the shift

    Returns:
        str: Formatted time (HH:MM:SS) or empty string
    """
    # Implementation unchanged, just renamed
    # Filter bursts in check-in range
    check_in_bursts = group[
        self._time_in_range(
            group['time_start'],
            shift_cfg.check_in_start,
            shift_cfg.check_in_end
        )
    ]

    if len(check_in_bursts) == 0:
        return ""

    # Return earliest burst_start
    earliest = check_in_bursts['burst_start'].min()
    return earliest.strftime('%H:%M:%S')

# OLD
def _find_last_out(self, group, shift_cfg):
    """Find Last Out timestamp"""

# NEW
def _find_check_out(self, group, shift_cfg):
    """Find Check Out Record timestamp (v10.0 terminology)

    Args:
        group: DataFrame group for shift instance
        shift_cfg: ShiftConfig for the shift

    Returns:
        str: Formatted time (HH:MM:SS) or empty string
    """
    # Implementation unchanged, just renamed
    check_out_bursts = group[
        self._time_in_range(
            group['time_end'],
            shift_cfg.check_out_start,
            shift_cfg.check_out_end
        )
    ]

    if len(check_out_bursts) == 0:
        return ""

    # Return latest burst_end
    latest = check_out_bursts['burst_end'].max()
    return latest.strftime('%H:%M:% S')
```

### Step 2: Implement Status Calculation (90 min)
```python
# processor.py

def _calculate_check_in_status(self, check_in_str: str, shift_date: date,
                                shift_cfg: ShiftConfig) -> str:
    """Calculate check-in status: On Time or Late

    Args:
        check_in_str: Check-in time string (HH:MM:SS) or empty
        shift_date: Date of shift start
        shift_cfg: ShiftConfig for the shift

    Returns:
        str: "On Time", "Late", or "" (if check_in blank)

    Example:
        Shift A, date 2025-11-07, check_in "06:04:59"
        → "On Time"

        Shift A, date 2025-11-07, check_in "06:05:00"
        → "Late"
    """
    if not check_in_str or check_in_str == "":
        return ""

    # Parse check-in time
    try:
        check_in_time = datetime.strptime(check_in_str, '%H:%M:%S').time()
        check_in_dt = datetime.combine(shift_date, check_in_time)
    except ValueError:
        return ""  # Invalid format

    # Use ShiftConfig method
    if shift_cfg.is_check_in_late(check_in_dt):
        return "Late"
    else:
        return "On Time"


def _calculate_break_in_status(self, break_in_str: str, shift_date: date,
                                 shift_cfg: ShiftConfig) -> str:
    """Calculate break-in status: On Time or Late

    Args:
        break_in_str: Break-in time string (HH:MM:SS) or empty
        shift_date: Date for timestamp construction
        shift_cfg: ShiftConfig for the shift

    Returns:
        str: "On Time", "Late", or "" (if break_in blank)

    Note:
        For night shift, break_in may be on shift_date + 1.
        Handled by using actual calendar date from data.

    Example:
        Shift A, break_in "10:34:59"
        → "On Time"

        Shift A, break_in "10:35:00"
        → "Late"
    """
    if not break_in_str or break_in_str == "":
        return ""

    # Parse break-in time
    try:
        break_in_time = datetime.strptime(break_in_str, '%H:%M:%S').time()

        # For night shift, break might be on next day
        # Use shift_date as base (will be shift_date+1 for night shift breaks)
        break_in_dt = datetime.combine(shift_date, break_in_time)

        # Adjust for night shift if needed
        # (Break detection already handles this in data)

    except ValueError:
        return ""  # Invalid format

    # Use ShiftConfig method
    if shift_cfg.is_break_in_late(break_in_dt):
        return "Late"
    else:
        return "On Time"
```

### Step 3: Update Event Extraction (120 min)
```python
# processor.py - _extract_attendance_events()

def _extract_attendance_events(self, df: pd.DataFrame) -> pd.DataFrame:
    """Extract attendance events with status columns (v10.0)

    Changes from v9.0:
    - Renamed columns: Check-in, Break Time Out/In, Check Out Record
    - Added: Check-in Status, Break Time In Status
    - Uses renamed methods: _find_check_in, _find_check_out

    Args:
        df: DataFrame with shift instances

    Returns:
        DataFrame with attendance records including status columns
    """
    if len(df) == 0:
        return pd.DataFrame()

    results = []

    # Group by shift instance
    for (shift_code, shift_date, shift_instance_id), group in df.groupby(
        ['shift_code', 'shift_date', 'shift_instance_id']
    ):
        shift_cfg = self.config.shifts[shift_code]

        # Extract timestamps (renamed methods)
        check_in = self._find_check_in(group, shift_cfg)  # Was _find_first_in
        break_out, break_in = self._detect_breaks(group, shift_cfg)
        check_out = self._find_check_out(group, shift_cfg)  # Was _find_last_out

        # Calculate statuses (NEW)
        check_in_status = self._calculate_check_in_status(
            check_in, shift_date, shift_cfg
        )
        break_in_status = self._calculate_break_in_status(
            break_in, shift_date, shift_cfg
        )

        # Get user info
        output_name = group.iloc[0]['output_name']
        output_id = group.iloc[0]['output_id']

        # Build record with new column names
        record = {
            'Date': shift_date.strftime('%Y-%m-%d'),
            'ID': output_id,
            'Name': output_name,
            'Shift': shift_cfg.display_name,
            'Check-in': check_in,  # Was "First In"
            'Check-in Status': check_in_status,  # NEW
            'Break Time Out': break_out,  # Was "Break Out"
            'Break Time In': break_in,  # Was "Break In"
            'Break Time In Status': break_in_status,  # NEW
            'Check Out Record': check_out,  # Was "Last Out"
        }

        results.append(record)

    return pd.DataFrame(results)
```

### Step 4: Handle Night Shift Edge Cases (90 min)
```python
# Special handling for night shift break status calculation

def _calculate_break_in_status(self, break_in_str: str, shift_date: date,
                                 shift_cfg: ShiftConfig) -> str:
    """Calculate break-in status with night shift support

    Night shift special handling:
    - Shift starts on Day N (e.g., 2025-11-03 22:00)
    - Break occurs on Day N+1 (e.g., 2025-11-04 02:30)
    - Need to use Day N+1 for status calculation

    Solution: Extract actual date from break_in timestamp in data
    """
    if not break_in_str or break_in_str == "":
        return ""

    try:
        # Parse time
        break_in_time = datetime.strptime(break_in_str, '%H:%M:%S').time()

        # Determine actual date
        # For night shift C: break is on shift_date + 1
        if shift_cfg.name == 'C':
            # Night shift: break on next day
            actual_date = shift_date + timedelta(days=1)
        else:
            # Day shifts: same day
            actual_date = shift_date

        break_in_dt = datetime.combine(actual_date, break_in_time)

    except ValueError:
        return ""

    # Calculate status
    if shift_cfg.is_break_in_late(break_in_dt):
        return "Late"
    else:
        return "On Time"
```

### Step 5: Update Print Statements (30 min)
```python
# Update terminology in print statements throughout processor.py

# OLD
print("⏰ Extracting attendance events")
print(f"   First In: {first_in}")
print(f"   Last Out: {last_out}")

# NEW
print("⏰ Extracting attendance events with status calculation")
print(f"   Check-in: {check_in} ({check_in_status})")
print(f"   Check Out Record: {check_out}")
```

---

## Todo List

- [ ] Rename _find_first_in → _find_check_in
- [ ] Rename _find_last_out → _find_check_out
- [ ] Implement _calculate_check_in_status
- [ ] Implement _calculate_break_in_status
- [ ] Handle night shift date offset for break status
- [ ] Update _extract_attendance_events with status columns
- [ ] Update output column names
- [ ] Update print statements with new terminology
- [ ] Test with scenario data
- [ ] Verify no performance regression

---

## Success Criteria

- ✅ Methods renamed (check_in, check_out)
- ✅ Status calculation methods work correctly
- ✅ Night shift break status calculated correctly
- ✅ Output has 10 columns (not 8)
- ✅ Status columns show "On Time" or "Late" correctly
- ✅ Blank values handled (empty string for status)
- ✅ No performance regression (<0.5s for 199 rows)

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Night shift date confusion | HIGH | HIGH | Comprehensive night shift tests |
| Status calculation errors | HIGH | MEDIUM | Boundary value testing |
| Performance regression | MEDIUM | LOW | Benchmark before/after |
| Breaking existing tests | MEDIUM | HIGH | Update tests incrementally |

---

## Next Steps

After completion:
1. Run full test suite
2. Proceed to Phase 04 (Output Columns)

---

**Phase Status:** PENDING
