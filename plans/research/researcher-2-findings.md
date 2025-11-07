# Research Report: Gap-Based Break Detection Algorithms

## Executive Summary
Two-tier break detection: Priority 1 = gap detection (objective measure), Priority 2 = midpoint logic (fallback heuristic). Gap detection provides more accurate break periods when clear time separation exists.

## Algorithm Overview

### Priority 1: Gap Detection (Lines 135-141 in rule.yaml)
```
IF any gap >= minimum_break_gap_minutes exists between consecutive swipes/bursts:
  Break Out = swipe/burst immediately BEFORE gap
  Break In = swipe/burst immediately AFTER gap
  RETURN (Break Out, Break In)
```

### Priority 2: Midpoint Logic (Fallback)
Only apply if NO qualifying gap found. Complex branching based on swipe distribution around midpoint.

## Detailed Algorithm

### Step 1: Filter swipes in break search range
```python
break_swipes = filter_by_time_range(
    all_swipes,
    shift_cfg.break_search_start,
    shift_cfg.break_search_end
)
```

### Step 2: Try gap detection FIRST
```python
for i in range(len(break_swipes) - 1):
    gap = break_swipes[i+1].time - break_swipes[i].time
    if gap >= minimum_break_gap:
        break_out = break_swipes[i]      # Before gap
        break_in = break_swipes[i+1]     # After gap
        return (break_out, break_in)
```

### Step 3: Fallback to midpoint logic
```python
if no_gap_found:
    swipes_before = [s for s in break_swipes if s.time <= midpoint]
    swipes_after = [s for s in break_swipes if s.time > midpoint]

    if swipes_before and swipes_after:
        # Spanning case
        break_out = max(swipes_before)  # Latest before/at midpoint
        break_in = min(swipes_after)    # Earliest after midpoint

    elif swipes_before only:
        # Check for gap within before group
        gap = find_max_gap(swipes_before)
        if gap >= minimum_break_gap:
            break_out = swipe_before_gap
            break_in = swipe_after_gap
        else:
            # No qualifying gap
            break_out = max(swipes_before)  # Latest
            break_in = ""  # Blank

    elif swipes_after only:
        # Check for gap within after group
        gap = find_max_gap(swipes_after)
        if gap >= minimum_break_gap:
            break_out = swipe_before_gap
            break_in = swipe_after_gap
        else:
            # No qualifying gap
            break_out = ""  # Blank
            break_in = min(swipes_after)  # Earliest

    else:
        # No swipes in range
        break_out = ""
        break_in = ""
```

## Decision Tree

```
┌─ Swipes in break range?
│  NO → Break Out = "", Break In = ""
│  YES ↓
│
├─ Gap >= minimum_break_gap exists?
│  YES → Use gap-based detection → DONE
│  NO ↓
│
├─ Swipes span midpoint?
│  YES → Break Out = latest ≤ midpoint, Break In = earliest > midpoint
│  NO ↓
│
├─ All swipes before midpoint?
│  YES ↓
│  ├─ Gap >= minimum exists in group?
│  │  YES → Use gap within group
│  │  NO → Break Out = latest, Break In = ""
│
├─ All swipes after midpoint?
│  YES ↓
│  ├─ Gap >= minimum exists in group?
│  │  YES → Use gap within group
│  │  NO → Break Out = "", Break In = earliest
```

## Burst Handling

CRITICAL: Gaps calculated between BURSTS, not individual swipes within bursts.

```python
# After burst consolidation
bursts = [
    {start: 09:55, end: 10:01},  # 6-swipe burst
    {start: 10:25, end: 10:25}   # Single swipe
]

# Gap calculation
gap = burst[1].start - burst[0].end  # 10:25 - 10:01 = 24 minutes ✓

# NOT like this (wrong):
# gap = burst[1].start - burst[0].start  # 10:25 - 09:55 = 30 minutes ✗
```

## Edge Cases

### Single Swipe in Range
```python
if len(break_swipes) == 1:
    if swipe.time <= midpoint:
        break_out = swipe.time
        break_in = ""
    else:
        break_out = ""
        break_in = swipe.time
```

### Exactly at Midpoint
```python
# Use <= for before, > for after
if swipe.time == midpoint:
    counts_as_before = True  # Latest before/AT midpoint
```

### Multiple Gaps
```python
# Use FIRST qualifying gap (earliest in break window)
for i in range(len(break_swipes) - 1):
    if gap[i] >= minimum:
        return gap[i]  # Don't keep searching
```

## Implementation Complexity
- Time: O(n) for linear gap search
- Space: O(1) additional space

## Validation
1. Gap detection MUST be tried before midpoint logic
2. minimum_break_gap_minutes parameter required from config
3. Gaps calculated between burst_end and next burst_start
4. Empty strings for missing values (not None/NULL)
