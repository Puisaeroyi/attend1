# Implementation Plan: Fix Code to Match rule.yaml v9.0

**Date**: 2025-11-04
**Status**: Ready for Implementation
**Estimated Effort**: 8-12 hours
**Priority**: CRITICAL

---

## Overview

Current code violates multiple critical requirements from rule.yaml v9.0. Main issues: shift-instance grouping not implemented (groups by calendar_date instead), gap-based break detection missing (only uses midpoint logic), burst representation incorrect (loses burst_end timestamps needed for Break Out detection).

---

## Summary of Updated Rules (rule.yaml v9.0)

### Key Changes from Previous Version
1. **Shift-instance grouping** (lines 51-72): One shift = one record, even crossing midnight
2. **Gap-based break detection** (lines 135-141): Priority 1 = gap detection, Priority 2 = midpoint fallback
3. **Burst representation** (lines 74-85): Must preserve both burst_start AND burst_end
4. **Night shift date attribution** (line 70-72): Use shift START date, not swipe calendar dates
5. **minimum_break_gap_minutes parameter** (lines 121, 125, 133): Required for gap detection

---

## Gap Analysis

### CRITICAL ISSUES

#### 1. Shift-Instance Grouping NOT Implemented
**Location**: `processor.py:144-161` (_classify_shifts method)
**Current Behavior**: Groups by `calendar_date`
```python
df['calendar_date'] = df['timestamp'].dt.date
first_timestamps = df.groupby(['Name', 'calendar_date'])['timestamp'].transform('first')
```

**Problem**: Night shift crossing midnight gets fragmented into TWO records (one for Day N, one for Day N+1)

**Rule Requirement** (lines 51-72):
- Shift instance begins with valid First In swipe
- Night shift (C): 21:30 Day_N → 06:35 Day_N+1 = ONE record with Date=Day_N
- All next-day swipes belong to previous day's shift

**Impact**: BREAKING - Output violates core requirement of "one shift = one complete record"

---

#### 2. Gap-Based Break Detection Missing
**Location**: `processor.py:228-264` (_detect_breaks method)
**Current Behavior**: Only midpoint logic implemented
```python
before_midpoint = break_swipes[break_swipes['time_only'] <= midpoint]
after_midpoint = break_swipes[break_swipes['time_only'] > midpoint]
break_out = before_midpoint['timestamp'].max()
break_in = after_midpoint['timestamp'].min()
```

**Problem**: No gap detection before falling back to midpoint

**Rule Requirement** (lines 135-141):
- Priority 1: Detect gap >= minimum_break_gap_minutes between consecutive swipes/bursts
- Priority 2: Fall back to midpoint logic ONLY if no qualifying gap found

**Impact**: CRITICAL - Inaccurate break detection when clear time gaps exist

**Example Failure** (scenario_3, lines 266-278):
```
Input: 06:00, 10:20, 10:29, 14:00
Gap: 9 minutes between 10:20-10:29 (both after midpoint 10:15)

Current Output:
  Break Out = "" (no swipes before midpoint)
  Break In = 10:20 (earliest after midpoint)

Expected Output:
  Break Out = 10:20 (before 9-min gap)
  Break In = 10:29 (after 9-min gap)
```

---

#### 3. Burst Representation Loses burst_end
**Location**: `processor.py:113-142` (_detect_bursts method)
**Current Behavior**: Line 140 discards burst_end
```python
burst_groups['timestamp'] = burst_groups['burst_start']  # Only keeps start!
```

**Problem**: burst_end needed for Break Out detection (scenario_2, lines 251-263)

**Rule Requirement**:
- Burst from 09:55-10:01 → Break Out should use 10:01 (burst_end), NOT 09:55
- Gap calculation: current.burst_end to next.burst_start

**Impact**: CRITICAL - Break Out times incorrect when bursts involved

**Example Failure** (scenario_2):
```
Burst: 09:55, 09:56, 09:57, 09:58, 09:59, 10:01

Current Output:
  Break Out = 09:55 (burst_start used for all logic)

Expected Output:
  Break Out = 10:01 (burst_end for events before break)
```

---

#### 4. minimum_break_gap_minutes Parameter Missing
**Location**: `config.py:10-97` (ShiftConfig, RuleConfig)
**Current Behavior**: Parameter not parsed from rule.yaml

**Rule Requirement** (lines 121, 125, 133):
```yaml
A_shift:
  minimum_break_gap_minutes: 5
B_shift:
  minimum_break_gap_minutes: 5
C_shift:
  minimum_break_gap_minutes: 5
```

**Impact**: BLOCKING - Cannot implement gap detection without threshold

---

#### 5. Night Shift Date Attribution Wrong
**Location**: `processor.py:146` (_classify_shifts method)
**Current Behavior**: Uses swipe calendar_date
```python
df['calendar_date'] = df['timestamp'].dt.date  # Wrong for night shift!
```

**Problem**: Night shift swipes on Day_N+1 assigned to Day_N+1 instead of Day_N

**Rule Requirement** (lines 70-72):
- Night shift First In at 2025-11-03 21:55
- Swipes at 2025-11-04 02:00, 02:44, 06:03
- Output Date = 2025-11-03 (shift START date)

**Impact**: CRITICAL - Date column incorrect for night shifts

---

### MEDIUM PRIORITY ISSUES

#### 6. Midpoint Fallback Logic Incomplete
**Location**: `processor.py:228-264` (_detect_breaks method)
**Current Behavior**: Only handles "swipes spanning midpoint" case

**Missing Cases** (lines 151-167):
- All swipes before midpoint WITH gap >= minimum → use gap
- All swipes before midpoint WITHOUT gap → Break Out = latest, Break In = ""
- All swipes after midpoint WITH gap >= minimum → use gap
- All swipes after midpoint WITHOUT gap → Break Out = "", Break In = earliest

**Impact**: MEDIUM - Edge cases not handled correctly

---

#### 7. Strict Time Window Enforcement Unclear
**Location**: `processor.py:266-282` (_time_in_range method)
**Current Behavior**: Uses >= and <=
```python
return (time_series >= start) & (time_series <= end)
```

**Rule Requirement** (line 113):
- "strict_exclusion: Ignore all swipes outside defined ranges"
- Boundary precision matters (06:35:00 vs 06:35:01)

**Impact**: LOW - Minor edge case, but needs clarification

---

## Architecture Changes Required

### Data Flow Changes

**CURRENT PIPELINE**:
```
1. Load Excel
2. Filter status/users
3. Detect bursts (loses burst_end)
4. Classify shifts (by calendar_date) ← WRONG
5. Extract events (midpoint only) ← INCOMPLETE
6. Output
```

**NEW PIPELINE**:
```
1. Load Excel
2. Filter status/users
3. Detect bursts (preserve burst_start AND burst_end) ← FIX
4. Detect shift instances (not calendar_date) ← REPLACE
   a. Find all First In swipes (shift starts)
   b. Define activity windows (handle midnight crossing)
   c. Assign swipes to shift instances
5. Extract events per shift instance ← ENHANCE
   a. First In: earliest burst_start in check-in range
   b. Last Out: latest burst_end in check-out range
   c. Break Out/In: gap detection → midpoint fallback
6. Output (with shift_date, not calendar_date)
```

---

## Implementation Steps

### Phase 1: Config Updates (2 hours)

#### Task 1.1: Add minimum_break_gap_minutes to ShiftConfig
**File**: `config.py`
**Lines**: 10-20

**Current**:
```python
@dataclass
class ShiftConfig:
    name: str
    display_name: str
    check_in_start: time
    check_in_end: time
    check_out_start: time
    check_out_end: time
    break_search_start: time
    break_search_end: time
    midpoint: time
```

**New**:
```python
@dataclass
class ShiftConfig:
    name: str
    display_name: str
    check_in_start: time
    check_in_end: time
    check_out_start: time
    check_out_end: time
    break_search_start: time
    break_search_end: time
    midpoint: time
    minimum_break_gap_minutes: int  # ADD THIS
```

#### Task 1.2: Parse minimum_break_gap_minutes from rule.yaml
**File**: `config.py`
**Lines**: 60-97

**Add after line 82**:
```python
# Parse minimum break gap
minimum_break_gap = int(break_info['minimum_break_gap_minutes'])
```

**Update ShiftConfig instantiation** (add parameter):
```python
shifts[shift_code] = ShiftConfig(
    name=shift_code,
    display_name=display_names[shift_code],
    check_in_start=check_in_start,
    check_in_end=check_in_end,
    check_out_start=check_out_start,
    check_out_end=check_out_end,
    break_search_start=break_search_start,
    break_search_end=break_search_end,
    midpoint=midpoint,
    minimum_break_gap_minutes=minimum_break_gap  # ADD THIS
)
```

**Test**: Run config parsing, verify parameter loaded correctly

---

### Phase 2: Burst Detection Fix (2 hours)

#### Task 2.1: Preserve burst_end in DataFrame
**File**: `processor.py`
**Lines**: 113-142

**Current** (line 140):
```python
burst_groups['timestamp'] = burst_groups['burst_start']
```

**New** (keep BOTH columns, don't discard burst_end):
```python
# Keep both burst_start and burst_end
# Use burst_start as primary timestamp for shift classification
burst_groups['timestamp'] = burst_groups['burst_start']
# burst_end column automatically preserved from aggregation
```

**Verify columns after burst detection**:
- burst_start ✓
- burst_end ✓
- timestamp (= burst_start) ✓

**Test**: Check burst_groups DataFrame has all three timestamp columns

---

### Phase 3: Shift-Instance Grouping (4 hours) - CRITICAL

#### Task 3.1: Replace calendar_date grouping with shift_instance grouping
**File**: `processor.py`
**Method**: `_classify_shifts` (lines 144-161)

**COMPLETE REWRITE REQUIRED**

**New Method**: `_detect_shift_instances`

```python
def _detect_shift_instances(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect shift instances based on First In swipes, handle midnight crossing.

    Returns DataFrame with columns:
        - All original columns
        - shift_instance_id: unique ID per shift instance
        - shift_code: A/B/C
        - shift_date: date of First In (shift START date)
    """
    results = []

    for username, user_df in df.groupby('Name'):
        user_df = user_df.sort_values('timestamp').reset_index(drop=True)
        shift_instance_id = 0

        for idx, row in user_df.iterrows():
            ts = row['timestamp']
            t = ts.time()

            # Check if this swipe is a shift start (in any check_in_search_range)
            shift_code = None
            for code, shift_cfg in self.config.shifts.items():
                if shift_cfg.is_in_check_in_range(t):
                    shift_code = code
                    break

            if shift_code:
                # New shift instance detected
                shift_instance_id += 1
                shift_date = ts.date()  # Shift START date

                # Define activity window for this shift instance
                activity_start, activity_end = self._get_activity_window(
                    shift_code, shift_date
                )

                # Collect all swipes in this activity window
                shift_swipes = self._collect_shift_swipes(
                    user_df[idx:], activity_start, activity_end
                )

                # Mark each swipe with shift_instance_id
                for swipe_idx in shift_swipes.index:
                    results.append({
                        **user_df.loc[swipe_idx].to_dict(),
                        'shift_instance_id': f"{username}_{shift_instance_id}",
                        'shift_code': shift_code,
                        'shift_date': shift_date
                    })

    return pd.DataFrame(results)

def _get_activity_window(self, shift_code: str, shift_date: date) -> Tuple[datetime, datetime]:
    """
    Get activity window boundaries for a shift instance.

    Handles midnight crossing for C_shift.
    """
    shift_cfg = self.config.shifts[shift_code]

    if shift_code == 'A':
        # 05:30 Day_N → 14:35 Day_N (same day)
        activity_start = datetime.combine(shift_date, shift_cfg.check_in_start)
        activity_end = datetime.combine(shift_date, shift_cfg.check_out_end)

    elif shift_code == 'B':
        # 13:30 Day_N → 22:35 Day_N (same day)
        activity_start = datetime.combine(shift_date, shift_cfg.check_in_start)
        activity_end = datetime.combine(shift_date, shift_cfg.check_out_end)

    elif shift_code == 'C':
        # 21:30 Day_N → 06:35 Day_N+1 (CROSSES MIDNIGHT!)
        activity_start = datetime.combine(shift_date, shift_cfg.check_in_start)
        next_day = shift_date + timedelta(days=1)
        activity_end = datetime.combine(next_day, shift_cfg.check_out_end)

    return activity_start, activity_end

def _collect_shift_swipes(self, df: pd.DataFrame,
                          activity_start: datetime,
                          activity_end: datetime) -> pd.DataFrame:
    """
    Collect all swipes within activity window.
    """
    mask = (df['timestamp'] >= activity_start) & (df['timestamp'] <= activity_end)
    return df[mask]
```

**Replace groupby in _extract_attendance_events**:

**Current** (line 173):
```python
for (username, cal_date, shift_code), group in df.groupby(['Name', 'calendar_date', 'shift']):
```

**New**:
```python
for shift_instance_id, group in df.groupby('shift_instance_id'):
    username = group['Name'].iloc[0]
    shift_date = group['shift_date'].iloc[0]  # Shift START date
    shift_code = group['shift_code'].iloc[0]
```

**Test Cases**:
1. Night shift starting 2025-11-03 21:55 with swipes on 2025-11-04 → Date = 2025-11-03 ✓
2. User with both A and B shifts on same calendar day → Two separate records ✓
3. Orphan swipes outside check-in ranges → Ignored ✓

---

### Phase 4: Gap-Based Break Detection (3 hours) - CRITICAL

#### Task 4.1: Implement two-tier break detection algorithm
**File**: `processor.py`
**Method**: `_detect_breaks` (lines 228-264)

**COMPLETE REWRITE REQUIRED**

```python
def _detect_breaks(self, group: pd.DataFrame, shift_cfg: ShiftConfig) -> Tuple[str, str]:
    """
    Two-tier break detection:
    Priority 1: Gap detection (gap >= minimum_break_gap_minutes)
    Priority 2: Midpoint logic (fallback)
    """
    minimum_gap = pd.Timedelta(minutes=shift_cfg.minimum_break_gap_minutes)
    midpoint = shift_cfg.midpoint

    # Filter swipes in break search window
    mask = self._time_in_range(
        group['time_only'],
        shift_cfg.break_search_start,
        shift_cfg.break_search_end
    )
    break_swipes = group[mask].sort_values('timestamp').reset_index(drop=True)

    if len(break_swipes) == 0:
        return "", ""

    # PRIORITY 1: GAP DETECTION
    gap_result = self._detect_break_by_gap(break_swipes, minimum_gap)
    if gap_result:
        return gap_result

    # PRIORITY 2: MIDPOINT FALLBACK
    return self._detect_break_by_midpoint(break_swipes, midpoint, minimum_gap)

def _detect_break_by_gap(self, swipes: pd.DataFrame,
                         minimum_gap: pd.Timedelta) -> Tuple[str, str] | None:
    """
    Detect break via time gap >= minimum_gap between consecutive bursts.

    Returns (break_out, break_in) if qualifying gap found, else None.
    """
    for i in range(len(swipes) - 1):
        current = swipes.iloc[i]
        next_swipe = swipes.iloc[i + 1]

        # Gap = next.burst_start - current.burst_end
        gap = next_swipe['timestamp'] - current['burst_end']

        if gap >= minimum_gap:
            # Found qualifying gap!
            break_out = current['burst_end'].strftime('%H:%M:%S')  # Use burst_end!
            break_in = next_swipe['timestamp'].strftime('%H:%M:%S')  # Use burst_start
            return (break_out, break_in)

    return None  # No qualifying gap found

def _detect_break_by_midpoint(self, swipes: pd.DataFrame,
                               midpoint: time,
                               minimum_gap: pd.Timedelta) -> Tuple[str, str]:
    """
    Fallback: Detect break using midpoint logic with complex branching.

    Handles:
    - Swipes spanning midpoint
    - All swipes before midpoint (with/without gap)
    - All swipes after midpoint (with/without gap)
    - Single swipe
    """
    # Split by midpoint
    before_midpoint = swipes[swipes['time_only'] <= midpoint]
    after_midpoint = swipes[swipes['time_only'] > midpoint]

    # Case 1: Swipes span midpoint
    if len(before_midpoint) > 0 and len(after_midpoint) > 0:
        break_out = before_midpoint.iloc[-1]['burst_end'].strftime('%H:%M:%S')  # Latest before/at
        break_in = after_midpoint.iloc[0]['timestamp'].strftime('%H:%M:%S')  # Earliest after
        return (break_out, break_in)

    # Case 2: All swipes before midpoint
    if len(before_midpoint) > 0 and len(after_midpoint) == 0:
        # Check for gap within before group
        gap_result = self._detect_break_by_gap(before_midpoint, minimum_gap)
        if gap_result:
            return gap_result
        # No qualifying gap
        break_out = before_midpoint.iloc[-1]['burst_end'].strftime('%H:%M:%S')  # Latest
        return (break_out, "")

    # Case 3: All swipes after midpoint
    if len(before_midpoint) == 0 and len(after_midpoint) > 0:
        # Check for gap within after group
        gap_result = self._detect_break_by_gap(after_midpoint, minimum_gap)
        if gap_result:
            return gap_result
        # No qualifying gap
        break_in = after_midpoint.iloc[0]['timestamp'].strftime('%H:%M:%S')  # Earliest
        return ("", break_in)

    # Case 4: No swipes in range (shouldn't reach here but handle gracefully)
    return ("", "")
```

**Test Cases**:
1. Scenario 3 (lines 266-278): Swipes at 10:20, 10:29 with 9-min gap → Break Out=10:20, Break In=10:29 ✓
2. Scenario 2 (lines 251-263): Burst 09:55-10:01, gap to 10:25 → Break Out=10:01 (burst_end) ✓
3. Single swipe before midpoint → Break Out only ✓
4. Single swipe after midpoint → Break In only ✓

---

### Phase 5: First In / Last Out Fixes (1 hour)

#### Task 5.1: Update First In to use burst_start
**File**: `processor.py`
**Lines**: 200-212

**Current**:
```python
ts = candidates['timestamp'].min()
```

**New** (explicitly use burst_start):
```python
ts = candidates['burst_start'].min()  # Earliest burst start
```

**Test**: First In uses earliest timestamp in burst ✓

---

#### Task 5.2: Update Last Out to use burst_end
**File**: `processor.py`
**Lines**: 214-226

**Current**:
```python
ts = candidates['timestamp'].max()
```

**New** (explicitly use burst_end):
```python
ts = candidates['burst_end'].max()  # Latest burst end
```

**Test**: Last Out uses latest timestamp in burst ✓

---

### Phase 6: Update _extract_attendance_events (1 hour)

#### Task 6.1: Remove time_only column creation
**File**: `processor.py`
**Lines**: 178-180

**Current**:
```python
group = group.copy()
group['time_only'] = group['timestamp'].dt.time
```

**Problem**: time_only doesn't make sense for bursts (which timestamp?)

**New**:
```python
group = group.copy()
# Create time_only from appropriate timestamp for each context
# For break detection, will use burst_start/burst_end contextually
```

**Or better**: Remove time_only entirely, use timestamp.time() directly in filter methods

---

### Phase 7: Testing & Validation (2 hours)

#### Task 7.1: Create test cases for all scenarios
**File**: `tests/test_processor_v9.py` (NEW FILE)

**Test Coverage**:
1. Scenario 1 (normal day shift) - lines 237-249
2. Scenario 2 (burst with breaks) - lines 251-263
3. Scenario 3 (late break after midpoint) - lines 265-278
4. Scenario 4 (night shift crossing midnight) - lines 280-294
5. Scenario 5 (single swipe before midpoint) - lines 296-307
6. Scenario 6 (no break taken) - lines 309-319

**Create test data fixture**:
```python
import pytest
import pandas as pd
from datetime import datetime

@pytest.fixture
def scenario_4_input():
    """Night shift crossing midnight - scenario_4 from rule.yaml"""
    return pd.DataFrame([
        {'Name': 'Capone', 'timestamp': datetime(2025, 11, 3, 21, 55, 28), 'Status': 'Success'},
        {'Name': 'Capone', 'timestamp': datetime(2025, 11, 4, 2, 0, 35), 'Status': 'Success'},
        {'Name': 'Capone', 'timestamp': datetime(2025, 11, 4, 2, 44, 51), 'Status': 'Success'},
        {'Name': 'Capone', 'timestamp': datetime(2025, 11, 4, 6, 3, 14), 'Status': 'Success'},
    ])

def test_scenario_4_night_shift_midnight_crossing(scenario_4_input, config):
    processor = AttendanceProcessor(config)
    result = processor._detect_shift_instances(scenario_4_input)

    # All swipes belong to ONE shift instance
    assert len(result['shift_instance_id'].unique()) == 1

    # Shift date = 2025-11-03 (START date, not 2025-11-04)
    assert result['shift_date'].iloc[0] == date(2025, 11, 3)

    # Shift code = C (Night)
    assert result['shift_code'].iloc[0] == 'C'

    # All 4 swipes included
    assert len(result) == 4
```

**Run all tests**:
```bash
pytest tests/test_processor_v9.py -v
```

---

#### Task 7.2: Integration test with real data
**File**: Manual testing

**Create test input** matching scenario_4:
```
2025-11-03, Capone, 21:55:28, Success
2025-11-04, Capone, 02:00:35, Success
2025-11-04, Capone, 02:44:51, Success
2025-11-04, Capone, 06:03:14, Success
```

**Expected output**:
```
Date: 2025-11-03
ID: TPL0002
Name: Pham Tan Phat
Shift: Night
First In: 21:55:28
Break Out: 02:00:35
Break In: 02:44:51
Last Out: 06:03:14
```

**Run**:
```bash
python main.py test_night_shift.xlsx output.xlsx
```

**Verify**:
- Date = 2025-11-03 (not 2025-11-04) ✓
- Single row output ✓
- All times correct ✓

---

## Files to Modify/Create/Delete

### Modified Files
1. **config.py**
   - Lines 10-20: Add `minimum_break_gap_minutes` to ShiftConfig
   - Lines 60-97: Parse new parameter from rule.yaml

2. **processor.py**
   - Lines 113-142: Preserve burst_end in _detect_bursts
   - Lines 144-161: REPLACE _classify_shifts with _detect_shift_instances (complete rewrite)
   - Lines 163-198: Update _extract_attendance_events grouping logic
   - Lines 200-212: Update _find_first_in to use burst_start
   - Lines 214-226: Update _find_last_out to use burst_end
   - Lines 228-264: REPLACE _detect_breaks (complete rewrite with two-tier algorithm)
   - NEW: Add _get_activity_window method
   - NEW: Add _collect_shift_swipes method
   - NEW: Add _detect_break_by_gap method
   - NEW: Add _detect_break_by_midpoint method

### New Files
1. **tests/test_processor_v9.py**
   - Test all 6 scenarios from rule.yaml
   - Test shift-instance grouping
   - Test gap-based break detection
   - Test midnight crossing

### No Files Deleted

---

## Testing Strategy

### Unit Tests
- `test_config.py`: Test minimum_break_gap_minutes parsing
- `test_processor_v9.py`: Test all 6 rule.yaml scenarios
- `test_shift_instances.py`: Test shift instance detection and grouping
- `test_gap_detection.py`: Test gap-based break detection algorithm
- `test_midnight_crossing.py`: Test night shift date attribution

### Integration Tests
- Full pipeline with scenario_4 input (night shift)
- Full pipeline with scenario_2 input (burst + breaks)
- Full pipeline with mixed shifts (A, B, C on different days)

### Manual Validation
- Run with /home/silver/output1.xlsx
- Compare output against expected results
- Verify Date column for night shifts
- Verify Break Out/In times match gap detection

---

## Security Considerations

No security concerns - internal data processing tool, no external API calls or user authentication.

---

## Performance Considerations

### Time Complexity Changes
- Shift instance detection: O(n²) worst case (nested loop checking windows)
  - Optimization: Track last processed timestamp, skip already-assigned swipes
- Gap detection: O(n) per shift instance (linear scan)
- Overall: Still O(n log n) dominated by initial sorting

### Memory Usage
- Additional columns: shift_instance_id, shift_date, shift_code, burst_end
- Negligible impact (4 extra columns × n rows)

### Expected Performance
- 90-row dataset: <0.5s (unchanged)
- 1,000-row dataset: ~1-2s (slight increase due to shift instance logic)
- 10,000-row dataset: ~8-12s (acceptable)

---

## Risks & Mitigations

### Risk 1: Shift Instance Detection Complexity
**Risk**: Complex logic for midnight crossing, potential bugs
**Mitigation**: Comprehensive unit tests for all edge cases, manual validation with scenario_4

### Risk 2: Breaking Existing Functionality
**Risk**: Complete rewrite of core methods may introduce regressions
**Mitigation**: Keep existing tests passing, add new tests, thorough manual testing

### Risk 3: Performance Degradation
**Risk**: Shift instance detection may slow down processing
**Mitigation**: Optimize grouping logic, benchmark with large datasets

### Risk 4: Edge Case Handling
**Risk**: Unforeseen edge cases in real data
**Mitigation**: Extensive logging, permissive error handling, user warnings

---

## Implementation Checklist

### Phase 1: Config (2h)
- [ ] Add minimum_break_gap_minutes to ShiftConfig dataclass
- [ ] Parse minimum_break_gap_minutes from rule.yaml
- [ ] Test config parsing with pytest

### Phase 2: Burst Detection (2h)
- [ ] Preserve burst_end column in _detect_bursts
- [ ] Verify burst_groups DataFrame has burst_start, burst_end, timestamp
- [ ] Test burst detection preserves both timestamps

### Phase 3: Shift-Instance Grouping (4h)
- [ ] Implement _get_activity_window method
- [ ] Implement _collect_shift_swipes method
- [ ] Implement _detect_shift_instances method (replace _classify_shifts)
- [ ] Update _extract_attendance_events to group by shift_instance_id
- [ ] Test night shift date attribution (scenario_4)
- [ ] Test multiple shifts same calendar day

### Phase 4: Gap-Based Break Detection (3h)
- [ ] Implement _detect_break_by_gap method
- [ ] Implement _detect_break_by_midpoint method
- [ ] Rewrite _detect_breaks to use two-tier algorithm
- [ ] Test gap detection (scenario_3)
- [ ] Test burst + gap interaction (scenario_2)
- [ ] Test single swipe edge cases (scenario_5)

### Phase 5: First In / Last Out (1h)
- [ ] Update _find_first_in to use burst_start
- [ ] Update _find_last_out to use burst_end
- [ ] Test check-in/out with bursts

### Phase 6: Extract Events Update (1h)
- [ ] Update grouping in _extract_attendance_events
- [ ] Handle time_only column correctly for bursts
- [ ] Test full pipeline

### Phase 7: Testing (2h)
- [ ] Create test_processor_v9.py with all 6 scenarios
- [ ] Run all unit tests, ensure 100% pass rate
- [ ] Integration test with real data
- [ ] Manual validation with /home/silver/output1.xlsx
- [ ] Performance benchmark

---

## Unresolved Questions

1. **Boundary precision**: Swipe at exactly 06:35:00 - inclusive or exclusive for night shift window?
   - Rule.yaml suggests inclusive (<=) based on validation_rules line 230
   - Needs confirmation from user

2. **Multiple breaks per shift**: rule.yaml says "NOT implemented" (line 329), but what if data shows multiple breaks?
   - Current plan: Use first qualifying gap only
   - Ignore subsequent gaps

3. **Orphan swipes**: Swipes outside ALL check-in ranges - completely ignored or logged as warnings?
   - Current plan: Silently ignore (don't create shift instances)
   - Could add logging for transparency

4. **Burst spanning midnight**: How to represent burst from 23:59 to 00:01?
   - Current plan: Treat as single burst with burst_start (Day_N) and burst_end (Day_N+1)
   - Assign to shift based on burst_start time

5. **Gap calculation at midnight boundary**: Gap from 23:58 to 00:03 = 5 minutes, not negative?
   - Current plan: Use datetime objects, gaps always positive
   - Natural handling with datetime arithmetic

---

## Acceptance Criteria

### Must Pass
1. ✓ All 6 scenarios from rule.yaml produce expected output
2. ✓ Night shift (scenario_4) outputs Date = shift START date
3. ✓ Burst + break (scenario_2) uses burst_end for Break Out
4. ✓ Gap detection (scenario_3) detects 9-min gap correctly
5. ✓ All unit tests pass (target: 100%)
6. ✓ Integration test with /home/silver/output1.xlsx succeeds

### Should Pass
1. ✓ Performance remains <0.5s for 90-row dataset
2. ✓ No regressions in existing test coverage
3. ✓ Code follows existing patterns and style

### Nice to Have
1. Comprehensive logging for debugging
2. Performance metrics collection
3. Edge case documentation

---

## Post-Implementation

### Documentation Updates
1. Update README.md with v9.0 changes
2. Update docs/tech-stack.md with algorithm details
3. Create docs/shift-instance-grouping.md explaining new logic

### Code Review Checklist
1. All TODOs resolved
2. No hardcoded values
3. Error handling comprehensive
4. Logging adequate
5. Tests cover edge cases
6. Comments explain complex logic

### Deployment
1. Backup current version
2. Deploy updated code
3. Run integration tests
4. Monitor first production run
5. Validate output manually

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Config | 2 hours | None |
| Phase 2: Burst Fix | 2 hours | Phase 1 |
| Phase 3: Shift Grouping | 4 hours | Phase 2 |
| Phase 4: Gap Detection | 3 hours | Phase 2 |
| Phase 5: First/Last | 1 hour | Phase 2 |
| Phase 6: Extract Events | 1 hour | Phase 3, 4, 5 |
| Phase 7: Testing | 2 hours | All above |
| **TOTAL** | **15 hours** | Sequential |

**Recommended Approach**: Implement sequentially (dependencies), test each phase before proceeding.

**Estimated Calendar Time**: 2-3 days (with testing and validation)

---

## Conclusion

Current implementation violates 5 critical requirements from rule.yaml v9.0. Most severe: shift-instance grouping not implemented (groups by calendar_date instead), causing night shifts to fragment across multiple records. Gap-based break detection missing (only midpoint logic exists). Burst representation loses burst_end timestamps needed for accurate Break Out times.

Implementation requires complete rewrite of shift classification and break detection logic, plus updates to burst handling and event extraction. Estimated 15 hours effort over 2-3 days. High confidence in feasibility given well-defined requirements and comprehensive test scenarios in rule.yaml.

**Recommended Priority**: CRITICAL - implement immediately to comply with ruleset.
