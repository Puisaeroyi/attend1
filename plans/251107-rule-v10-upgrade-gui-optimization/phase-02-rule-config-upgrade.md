# Phase 02: Rule v10.0 Config Upgrade

**Date:** 2025-11-07
**Priority:** HIGH
**Status:** ⏸ Pending
**Progress:** 0%

---

## Context Links

- [Main Plan](./plan.md)
- [Phase 01: Research](./phase-01-research-analysis.md)
- [Config Module](/home/silver/windows_project/config.py)
- [Rule YAML](/home/silver/windows_project/rule.yaml)

---

## Overview

Update configuration files + dataclasses for v10.0 terminology and late marking thresholds.

**Duration:** 3 hours
**Dependencies:** Phase 01
**Deliverable:** Updated config.py, rule.yaml with v10.0 spec

---

## Key Insights

### Configuration Changes Required

**1. ShiftConfig Dataclass**
Add fields for late marking thresholds:
```python
@dataclass
class ShiftConfig:
    # Existing fields...
    name: str
    display_name: str
    check_in_start: time
    check_in_end: time
    # ...

    # NEW FIELDS
    shift_start_time: time  # Official shift start (for late marking)
    grace_period_seconds: int  # 299 seconds (04:59)
    break_end_time: time  # Official break end time
```

**2. Rule YAML Structure**
```yaml
shift_structure:
  shifts:
    A:
      # Existing...
      window: "06:00-14:00"

      # NEW
      shift_start: "06:00"
      grace_period_seconds: 299  # 04:59

      # Updated terminology in comments
      check_in_search_range: "05:30-06:35"  # Was "First In search range"
      check_out_search_range: "13:30-14:35"  # Was "Last Out search range"

break_detection:
  parameters:
    A_shift:
      # Existing...
      window: "10:00-10:30"

      # NEW
      break_end_time: "10:30"
      grace_period_seconds: 299  # 04:59

      # C shift update
    C_shift:
      window: "02:00-02:45"
      search_range: "01:50-02:50"  # Changed from "01:50-02:45"
      break_end_time: "02:45"
      grace_period_seconds: 299  # 04:59 (until 02:49:59)
```

**3. Output Column Mapping**
```python
# config.py - Add output column configuration
OUTPUT_COLUMNS_V10 = [
    "Date",
    "ID",
    "Name",
    "Shift",
    "Check-in",  # Was "First In"
    "Check-in Status",  # NEW
    "Break Time Out",  # Was "Break Out"
    "Break Time In",  # Was "Break In"
    "Break Time In Status",  # NEW
    "Check Out Record",  # Was "Last Out"
]
```

---

## Requirements

**FR-02.1:** Add shift_start_time to ShiftConfig
**FR-02.2:** Add grace_period_seconds to ShiftConfig (299)
**FR-02.3:** Add break_end_time to break detection config
**FR-02.4:** Update C shift break search range to 01:50-02:50
**FR-02.5:** Update rule.yaml comments with new terminology
**FR-02.6:** Maintain backward compatibility (old configs still parse)

---

## Architecture

### Config Parsing Flow
```
rule.yaml (v10.0)
    ↓
RuleConfig.load_from_yaml()
    ↓
Parse shift_structure → ShiftConfig objects
    ↓
Parse break_detection → ShiftConfig.break_* fields
    ↓
Validate all time formats
    ↓
Return RuleConfig instance
```

### Dataclass Structure (Updated)
```python
@dataclass
class ShiftConfig:
    """Configuration for single shift (v10.0)"""
    # Identity
    name: str  # A/B/C
    display_name: str  # Morning/Afternoon/Night

    # Time windows
    window_start: time
    window_end: time
    check_in_start: time
    check_in_end: time
    check_out_start: time
    check_out_end: time

    # Late marking (NEW)
    shift_start_time: time
    grace_period_seconds: int

    # Break detection
    break_window_start: time
    break_window_end: time
    break_search_start: time
    break_search_end: time
    break_midpoint: time
    minimum_break_gap_minutes: int

    # Late marking for breaks (NEW)
    break_end_time: time
    break_grace_period_seconds: int

    # Methods
    def is_check_in_late(self, check_in: datetime) -> bool:
        """Determine if check-in is late"""
        threshold = datetime.combine(
            check_in.date(),
            self.shift_start_time
        ) + timedelta(seconds=self.grace_period_seconds)

        return check_in > threshold

    def is_break_in_late(self, break_in: datetime) -> bool:
        """Determine if break-in is late"""
        threshold = datetime.combine(
            break_in.date(),
            self.break_end_time
        ) + timedelta(seconds=self.grace_period_seconds)

        return break_in > threshold
```

---

## Related Code Files

- `/home/silver/windows_project/config.py` - ShiftConfig, RuleConfig
- `/home/silver/windows_project/rule.yaml` - Configuration file
- `/home/silver/windows_project/tests/test_config.py` - Config parsing tests

---

## Implementation Steps

### Step 1: Update ShiftConfig Dataclass (45 min)
```python
# config.py

from dataclasses import dataclass
from datetime import time, datetime, timedelta
from typing import Optional

@dataclass
class ShiftConfig:
    """Shift configuration with v10.0 late marking support"""

    # Existing fields (keep all)
    name: str
    display_name: str
    window_start: time
    window_end: time
    check_in_start: time
    check_in_end: time
    check_out_start: time
    check_out_end: time
    break_window_start: time
    break_window_end: time
    break_search_start: time
    break_search_end: time
    break_midpoint: time
    minimum_break_gap_minutes: int

    # NEW FIELDS for v10.0
    shift_start_time: time
    grace_period_seconds: int = 299  # 04:59 default
    break_end_time: time
    break_grace_period_seconds: int = 299  # 04:59 default

    def is_check_in_late(self, check_in: datetime) -> bool:
        """Check if check-in time exceeds grace period

        Args:
            check_in: Check-in datetime

        Returns:
            True if late (> shift_start + 04:59), False if on time

        Example:
            Shift A starts 06:00, grace 04:59
            06:04:59 → False (On Time)
            06:05:00 → True (Late)
        """
        # Handle midnight crossing for night shift
        shift_date = check_in.date()
        threshold = datetime.combine(shift_date, self.shift_start_time)

        # Add grace period (299 seconds = 00:04:59)
        threshold += timedelta(seconds=self.grace_period_seconds)

        # Late if strictly greater than threshold
        return check_in > threshold

    def is_break_in_late(self, break_in: datetime) -> bool:
        """Check if break-in time exceeds grace period

        Args:
            break_in: Break-in datetime

        Returns:
            True if late (> break_end + 04:59), False if on time

        Example:
            Shift A break ends 10:30, grace 04:59
            10:34:59 → False (On Time)
            10:35:00 → True (Late)
        """
        # Handle midnight crossing for night shift break
        break_date = break_in.date()
        threshold = datetime.combine(break_date, self.break_end_time)

        # Add grace period
        threshold += timedelta(seconds=self.grace_period_seconds)

        return break_in > threshold

    # Keep existing methods
    def is_in_check_in_range(self, t: time) -> bool:
        """Existing method - no changes"""
        # ... existing implementation
```

### Step 2: Update RuleConfig Parsing (60 min)
```python
# config.py - RuleConfig.load_from_yaml()

@classmethod
def load_from_yaml(cls, path: str) -> 'RuleConfig':
    """Load configuration from YAML file (v10.0 support)"""

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    # Parse shifts
    shifts = {}
    for shift_name, shift_data in data['shift_structure']['shifts'].items():
        # Existing parsing...
        window_start, window_end = shift_data['window'].split('-')
        # ...

        # NEW: Parse shift start time
        shift_start_str = shift_data.get('shift_start', window_start)
        shift_start_time = parse_time(shift_start_str)

        # NEW: Parse grace period (default 299 seconds)
        grace_period = shift_data.get('grace_period_seconds', 299)

        # NEW: Parse break end time
        break_params = data['break_detection']['parameters'][f'{shift_name}_shift']
        break_window = break_params['window']
        break_end_str = break_window.split('-')[1]
        break_end_time = parse_time(break_end_str)

        # NEW: Break grace period (default 299)
        break_grace = break_params.get('grace_period_seconds', 299)

        # Create ShiftConfig with new fields
        shifts[shift_name] = ShiftConfig(
            name=shift_name,
            display_name=shift_data['name'],
            # ... existing fields ...
            shift_start_time=shift_start_time,
            grace_period_seconds=grace_period,
            break_end_time=break_end_time,
            break_grace_period_seconds=break_grace,
        )

    return cls(
        burst_threshold_minutes=burst_threshold,
        valid_users=user_mapping,
        shifts=shifts,
        status_filter=status_filter
    )
```

### Step 3: Update rule.yaml (45 min)
```yaml
# rule.yaml v10.0

system_overview: |
  Process biometric swipe logs for 4 CCTV operators.
  v10.0 changes:
    - New terminology: Check-in, Break Time Out/In, Check Out Record
    - Late marking with grace period cutoff (04:59)
    - Status columns in output

# Update terminology in comments throughout

shift_structure:
  shifts:
    A:
      name: "Morning"
      window: "06:00-14:00"
      shift_start: "06:00"  # NEW
      grace_period_seconds: 299  # NEW (04:59)
      check_in_search_range: "05:30-06:35"  # Renamed from "First In"
      check_out_search_range: "13:30-14:35"  # Renamed from "Last Out"

    B:
      name: "Afternoon"
      window: "14:00-22:00"
      shift_start: "14:00"  # NEW
      grace_period_seconds: 299  # NEW
      check_in_search_range: "13:30-14:35"
      check_out_search_range: "21:30-22:35"

    C:
      name: "Night"
      window: "22:00-06:00"
      shift_start: "22:00"  # NEW
      grace_period_seconds: 299  # NEW
      check_in_search_range: "21:30-22:35"
      check_out_search_range: "05:30-06:35"

break_detection:
  parameters:
    A_shift:
      window: "10:00-10:30"
      search_range: "09:50-10:35"
      midpoint_checkpoint: "10:15"
      minimum_break_gap_minutes: 5
      break_end_time: "10:30"  # NEW
      grace_period_seconds: 299  # NEW

    B_shift:
      window: "18:00-18:30"
      search_range: "17:50-18:35"
      midpoint_checkpoint: "18:15"
      minimum_break_gap_minutes: 5
      break_end_time: "18:30"  # NEW
      grace_period_seconds: 299  # NEW

    C_shift:
      window: "02:00-02:45"
      search_range: "01:50-02:50"  # UPDATED from "01:50-02:45"
      midpoint_checkpoint: "02:22:30"
      minimum_break_gap_minutes: 5
      break_end_time: "02:45"  # NEW
      grace_period_seconds: 299  # NEW (until 02:49:59)

# Update output column names
output_columns:
  - Date
  - ID
  - Name
  - Shift
  - Check-in  # Was "First In"
  - Check-in Status  # NEW
  - Break Time Out  # Was "Break Out"
  - Break Time In  # Was "Break In"
  - Break Time In Status  # NEW
  - Check Out Record  # Was "Last Out"

# Add late marking documentation
late_marking:
  description: "Grace period is hard cutoff boundary"

  check_in_status:
    on_time: "<= shift_start + 04:59"
    late: ">= shift_start + 05:00"
    examples:
      shift_a: "06:04:59 = On Time, 06:05:00 = Late"
      shift_b: "14:04:59 = On Time, 14:05:00 = Late"
      shift_c: "22:04:59 = On Time, 22:05:00 = Late"

  break_time_in_status:
    on_time: "<= break_end + 04:59"
    late: ">= break_end + 05:00"
    examples:
      shift_a: "10:34:59 = On Time, 10:35:00 = Late"
      shift_b: "18:34:59 = On Time, 18:35:00 = Late"
      shift_c: "02:49:59 = On Time, 02:50:00 = Late"
```

### Step 4: Create Config Tests (30 min)
```python
# tests/test_config.py

def test_load_config_v10():
    """Test loading v10.0 config with new fields"""
    config = RuleConfig.load_from_yaml('rule.yaml')

    # Verify new fields loaded
    shift_a = config.shifts['A']
    assert shift_a.shift_start_time == time(6, 0)
    assert shift_a.grace_period_seconds == 299
    assert shift_a.break_end_time == time(10, 30)
    assert shift_a.break_grace_period_seconds == 299

def test_check_in_late_marking():
    """Test check-in late marking logic"""
    config = RuleConfig.load_from_yaml('rule.yaml')
    shift_a = config.shifts['A']

    # On time: 06:04:59
    on_time = datetime(2025, 11, 7, 6, 4, 59)
    assert not shift_a.is_check_in_late(on_time)

    # Late: 06:05:00
    late = datetime(2025, 11, 7, 6, 5, 0)
    assert shift_a.is_check_in_late(late)

    # Late: 06:05:01
    very_late = datetime(2025, 11, 7, 6, 5, 1)
    assert shift_a.is_check_in_late(very_late)

def test_break_in_late_marking():
    """Test break-in late marking logic"""
    config = RuleConfig.load_from_yaml('rule.yaml')
    shift_a = config.shifts['A']

    # On time: 10:34:59
    on_time = datetime(2025, 11, 7, 10, 34, 59)
    assert not shift_a.is_break_in_late(on_time)

    # Late: 10:35:00
    late = datetime(2025, 11, 7, 10, 35, 0)
    assert shift_a.is_break_in_late(late)

def test_c_shift_break_range_updated():
    """Test C shift break search range extended to 02:50"""
    config = RuleConfig.load_from_yaml('rule.yaml')
    shift_c = config.shifts['C']

    # Verify search range
    assert shift_c.break_search_end == time(2, 50)  # Was 02:45
```

---

## Todo List

- [ ] Update ShiftConfig dataclass (add 4 new fields)
- [ ] Implement is_check_in_late() method
- [ ] Implement is_break_in_late() method
- [ ] Update RuleConfig.load_from_yaml() to parse new fields
- [ ] Update rule.yaml with v10.0 structure
- [ ] Update C shift break range to 01:50-02:50
- [ ] Add late_marking section to rule.yaml
- [ ] Create config tests for new fields
- [ ] Run existing tests to ensure backward compatibility
- [ ] Document configuration changes

---

## Success Criteria

- ✅ ShiftConfig has new fields (shift_start_time, grace_period_seconds, break_end_time, break_grace_period_seconds)
- ✅ Late marking methods work correctly (boundary tests pass)
- ✅ rule.yaml parses without errors
- ✅ C shift break range = 01:50-02:50
- ✅ All existing config tests still pass
- ✅ New config tests pass (late marking logic)

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing config parsing | HIGH | LOW | Comprehensive tests, default values |
| Grace period calculation error | HIGH | MEDIUM | Extensive boundary testing |
| Midnight crossing issues | MEDIUM | MEDIUM | Test night shift specifically |
| YAML syntax errors | LOW | MEDIUM | Validate YAML before commit |

---

## Next Steps

After completion:
1. Commit config changes
2. Proceed to Phase 03 (Processing Logic)

---

**Phase Status:** PENDING
