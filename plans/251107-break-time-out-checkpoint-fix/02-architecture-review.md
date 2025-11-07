# Phase 2: Architecture Review - Current Break Detection Logic

## Code Flow Analysis

### Entry Point: `_detect_breaks()`
**File:** processor.py:353-495
**Responsibility:** Two-tier break detection (gap-based → midpoint fallback)

### Current Implementation Structure

```
_detect_breaks(group, shift_cfg)
├── Filter break search window (lines 374-384)
├── PRIORITY 1: Gap-based detection (lines 389-434)
│   ├── Calculate gaps between consecutive bursts
│   ├── Filter qualifying gaps (≥ min_gap)
│   └── Select gap with Break Time In closest to cutoff ← PROBLEM
└── PRIORITY 2: Midpoint fallback (lines 436-495)
    ├── Case 1: Swipes span midpoint
    ├── Case 2: All before midpoint
    ├── Case 3: All after midpoint
    └── Case 4: No swipes
```

## Problematic Code Section

### Location: Lines 402-434

```python
# Enhanced logic: Choose gap with Break Time In closest to cutoff
cutoff_time = shift_cfg.break_in_on_time_cutoff

# Calculate distance from cutoff for each qualifying gap
best_gap = None
min_distance_to_cutoff = float('inf')

for gap_idx in qualifying_gaps.index:
    break_in_ts = break_swipes.loc[gap_idx + 1, 'burst_start']
    break_in_time = break_in_ts.time()

    # Calculate distance from cutoff (in seconds)
    if break_in_time <= cutoff_time:
        distance = (cutoff_time.hour * 3600 + ...) - (break_in_time.hour * 3600 + ...)
    else:
        distance = (break_in_time.hour * 3600 + ...) - (cutoff_time.hour * 3600 + ...)

    # Choose the gap with minimum distance to cutoff
    if distance < min_distance_to_cutoff:
        min_distance_to_cutoff = distance
        best_gap = gap_idx

if best_gap is not None:
    break_out_ts = break_swipes.loc[best_gap, 'burst_end']  # ← USES SELECTED GAP
    break_in_ts = break_swipes.loc[best_gap + 1, 'burst_start']
    return (break_out_ts.strftime('%H:%M:%S'), break_in_ts.strftime('%H:%M:%S'), ...)
```

**Problem:**
- Entire gap selection based ONLY on Break Time In proximity to cutoff
- Break Time Out timestamp inherits from selected gap (wrong criteria)

## Configuration Data Flow

### Current ShiftConfig Structure (config.py:11-43)

```python
@dataclass
class ShiftConfig:
    name: str                          # A/B/C
    display_name: str                  # Morning/Afternoon/Night
    check_in_start: time
    check_in_end: time
    check_in_shift_start: time
    check_in_on_time_cutoff: time
    check_in_late_threshold: time
    check_out_start: time
    check_out_end: time
    break_search_start: time           # ← Currently used
    break_search_end: time
    break_end_time: time
    break_in_on_time_cutoff: time      # ← Used for selection
    break_in_late_threshold: time
    midpoint: time
    minimum_break_gap_minutes: int

    # MISSING: break_out_checkpoint ← NEEDED
```

### Configuration Loading (config.py:67-95)

**Current parsing logic:**
```python
'break_search_start': parse_time(break_params['break_out']['search_range'].split('-')[0]),
'break_search_end': parse_time(break_params['break_in']['search_range'].split('-')[1]),
'break_in_on_time_cutoff': parse_time(break_params['break_in']['on_time_cutoff']),

# MISSING: break_out_checkpoint parsing
```

## Data Structures

### Break Swipes DataFrame
**Columns:**
- `burst_start`: Earliest timestamp in burst (used for Break Time In)
- `burst_end`: Latest timestamp in burst (used for Break Time Out)
- `time_start`: Time component of burst_start
- `time_end`: Time component of burst_end
- `next_burst_start`: Shifted burst_start (for gap calculation)
- `gap_minutes`: Gap duration between consecutive bursts

### Gap Selection Logic Flow

**Current (INCORRECT):**
```
qualifying_gaps → filter by cutoff proximity → select best gap → extract both timestamps
                  (only considers Break Time In)
```

**Required (CORRECT):**
```
qualifying_gaps → score by checkpoint proximity → select Break Time Out
                → score by cutoff proximity → select Break Time In
                (independent selection OR paired with priority)
```

## Time Distance Calculation

### Current Implementation (lines 413-419)

```python
# Calculate distance from cutoff (in seconds)
if break_in_time <= cutoff_time:
    distance = (cutoff_time seconds) - (break_in_time seconds)
else:
    distance = (break_in_time seconds) - (cutoff_time seconds)
```

**Issues:**
1. Only calculates cutoff distance (for Break Time In)
2. No checkpoint distance calculation (for Break Time Out)
3. Absolute distance used (always positive)

### Required Implementation

**Need TWO distance calculations:**

```python
# For Break Time Out: distance from checkpoint
checkpoint_time = shift_cfg.break_out_checkpoint
break_out_time = burst_end.time()
checkpoint_distance = abs(time_to_seconds(break_out_time) - time_to_seconds(checkpoint_time))

# For Break Time In: distance from cutoff (existing)
cutoff_time = shift_cfg.break_in_on_time_cutoff
break_in_time = burst_start.time()
cutoff_distance = abs(time_to_seconds(break_in_time) - time_to_seconds(cutoff_time))
```

## Integration Points

### Called By
- `_extract_attendance_events()` (processor.py:285)
- Groups by `shift_instance_id`
- Returns tuple: `(break_out_str, break_in_str, break_in_time)`

### Dependencies
- `shift_cfg: ShiftConfig` - configuration object
- `group: pd.DataFrame` - bursts for single shift instance
- `_time_in_range()` - helper for window filtering

### Return Value
```python
return (
    break_out_str,    # HH:MM:SS or ""
    break_in_str,     # HH:MM:SS or ""
    break_in_time     # time object or None (for status calculation)
)
```

## Algorithm Complexity

### Current Implementation
- **Time Complexity:** O(n) where n = number of qualifying gaps
- **Space Complexity:** O(n) for gap calculations
- **Performance:** Negligible overhead (~0.02-0.04s per test)

### Proposed Changes Impact
- **Additional calculations:** 2 × distance calculations per gap
- **Expected overhead:** < 5% increase
- **Still O(n):** No algorithmic complexity change

## Affected Test Files

### test_processor.py
**Tests requiring updates:**
- `test_detect_breaks_multiple_swipes` (line ~)
- `test_edge_case_multiple_breaks` (line ~)
- New tests for checkpoint priority

### test_scenarios.py
**Scenarios affected:**
- Scenario 3: Late break with gap detection
- Scenario 4: Night shift crossing midnight
- May need expectation updates

## Design Patterns in Use

### Two-Tier Fallback Pattern
```
Try Priority 1 (Gap Detection)
  └─ If no qualifying gaps
       └─ Fall back to Priority 2 (Midpoint Logic)
```

**Fix location:** Within Priority 1 only
**No changes needed:** Priority 2 (midpoint fallback)

### Diff-Cumsum Pattern
- Used in burst detection (not affected)
- Gap detection uses shift operations (affected slightly)

## Related Code Sections

### Helper: `_time_in_range()` (lines 497-513)
- Used for filtering break search window
- No changes needed

### Time Parsing: `parse_time()` (config.py:97-103)
- Used for config loading
- May need to parse new `checkpoint` field

## Consistency Requirements

### Shift Symmetry
All three shifts must have checkpoint configuration:
- **Shift A:** checkpoint = 10:00:00 (window start)
- **Shift B:** checkpoint = 18:00:00 (window start)
- **Shift C:** checkpoint = 02:00:00 (window start)

### Configuration Validation
Need to ensure:
- Checkpoint within search range
- Checkpoint ≤ cutoff (time ordering)
- All required fields present

## Migration Path

### Breaking Changes
1. **ShiftConfig dataclass:** New required field `break_out_checkpoint`
2. **rule.yaml:** New configuration parameter under `break_out:`
3. **Gap selection logic:** Different behavior (may affect existing results)

### Backward Compatibility
**NOT backward compatible** - requires:
- Updated rule.yaml
- Updated config.py
- Existing configs will fail validation

### Rollback Plan
1. Git revert to commit 07164ca (before this fix)
2. Restore old gap selection logic
3. Keep existing test expectations

## Code Quality Considerations

### Method Length
- Current `_detect_breaks()`: ~140 lines
- After fix: ~160 lines (adds ~20 lines)
- Still acceptable (< 200 line threshold for complex algorithms)

### Readability
Proposed refactoring for clarity:
```python
def _detect_breaks(...):
    # ... filtering ...

    # PRIORITY 1: Gap-based detection
    if len(break_swipes) >= 2:
        qualifying_gaps = self._find_qualifying_gaps(break_swipes, min_gap)

        if len(qualifying_gaps) > 0:
            break_out = self._select_break_out(qualifying_gaps, shift_cfg)
            break_in = self._select_break_in(qualifying_gaps, shift_cfg)
            return (break_out, break_in, break_in_time)

    # PRIORITY 2: Midpoint fallback
    return self._midpoint_fallback(...)
```

**Benefits:**
- Clearer separation of concerns
- Easier testing
- Better maintainability

**Cost:**
- More methods to maintain
- Slightly more complex call stack

**Decision:** Recommend inline fix first, refactor later if complexity grows

## Unresolved Architecture Questions

1. **Should Break Out and Break In come from same gap?**
   - Current: Both from same gap (paired)
   - Option: Allow different gaps (independent)
   - **Impact:** Fundamental algorithm change

2. **Should we extract helper methods?**
   - `_select_break_out_from_gaps()`
   - `_select_break_in_from_gaps()`
   - **Impact:** Code organization only

3. **Should checkpoint be derived or explicit?**
   - Derive: checkpoint = window_start_time
   - Explicit: Configure in rule.yaml
   - **Impact:** Configuration complexity vs. flexibility
