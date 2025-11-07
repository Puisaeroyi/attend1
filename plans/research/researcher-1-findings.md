# Research Report: Shift-Instance Grouping & Night Shift Handling

## Executive Summary
Shift-instance grouping requires tracking shift boundaries across calendar days. Industry best practice: group by shift START timestamp, include all activity until shift END boundary (even on next calendar day).

## Recommended Algorithm

### 1. Shift Start Detection
```
For each swipe (chronologically sorted):
  If swipe time in ANY check_in_search_range:
    Create new shift instance
    Set shift_date = calendar_date of this swipe
    Set shift_code based on which range matched
```

### 2. Activity Window Definition
```
A_shift: activity from 05:30 Day_N through 14:35 Day_N (same day)
B_shift: activity from 13:30 Day_N through 22:35 Day_N (same day)
C_shift: activity from 21:30 Day_N through 06:35 Day_N+1 (crosses midnight!)
```

### 3. Grouping Logic
```
For C_shift starting 2025-11-03:
  shift_date = 2025-11-03 (START date)
  activity_window = [2025-11-03 21:30:00, 2025-11-04 06:35:00]

All swipes in this window belong to ONE shift instance with Date=2025-11-03
```

## Data Structure
```python
shift_instance = {
    'shift_date': date,          # START date
    'shift_code': 'C',
    'activity_start': datetime,  # First valid check-in
    'activity_end': datetime,    # Window boundary
    'swipes': []                 # All swipes in window
}
```

## Edge Cases

### 1. Orphan Swipes
Swipes OUTSIDE check_in_search_ranges → no shift instance created → ignored

### 2. Boundary Precision
- Swipe at exactly 06:35:00 → belongs to night shift (use <=)
- Swipe at 06:35:01 → outside window (use strict boundaries)

### 3. Multiple Shifts Same Day
User can have Shift A (06:00-14:00) AND Shift B (14:00-22:00) on same calendar day
→ Two separate shift instances, two separate output rows

### 4. Night Shift Date Attribution
CRITICAL: All next-day swipes before 06:35 attributed to PREVIOUS calendar day's shift
Example: Swipe at 2025-11-04 02:00 belongs to 2025-11-03 night shift

## Implementation Strategy

### Step 1: Sort all swipes chronologically
```python
df.sort_values(['Name', 'timestamp'], inplace=True)
```

### Step 2: Detect shift starts
```python
for user_swipes:
    for swipe in swipes:
        if is_shift_start(swipe):
            create_shift_instance(swipe)
```

### Step 3: Assign swipes to instances
```python
for shift_instance:
    collect all swipes within activity_window
    handle midnight crossing for C_shift
```

### Step 4: Output with shift_date
```python
output['Date'] = shift_instance.shift_date  # NOT swipe calendar dates!
```

## Algorithm Complexity
- Time: O(n log n) for sorting + O(n) for linear scan = O(n log n)
- Space: O(n) for storing shift instances

## Validation Rules
1. Every shift instance MUST have at least one check-in swipe
2. Shift date MUST be date of First In swipe
3. C_shift MUST include next-day swipes until 06:35
4. No swipe belongs to multiple shift instances
5. Swipes outside activity windows are excluded (not ignored entirely, just from that shift)
