# Research Report: Burst Detection & Representation

## Executive Summary
Burst detection consolidates multiple rapid swipes (≤2min apart) into atomic units. CRITICAL: Must preserve both burst_start (earliest) and burst_end (latest) timestamps, as different logic uses different representations.

## Burst Detection Algorithm

### Current Implementation (Compare-Diff-Cumsum Pattern)
```python
# Efficient O(n) algorithm using pandas
threshold = pd.Timedelta(minutes=2)

# Calculate time diff between consecutive swipes
df['time_diff'] = df.groupby('Name')['timestamp'].diff()

# Mark burst boundaries (diff > threshold OR first row)
df['new_burst'] = (df['time_diff'] > threshold) | df['time_diff'].isna()

# Create burst group IDs
df['burst_id'] = df.groupby('Name')['new_burst'].cumsum()

# Aggregate: keep earliest AND latest per burst
burst_groups = df.groupby(['Name', 'burst_id']).agg({
    'timestamp': ['min', 'max']  # Both start and end!
})
```

### Why Both Timestamps Matter

```
Burst: 09:55, 09:56, 09:57, 09:58, 09:59, 10:01
→ burst_start = 09:55
→ burst_end = 10:01

Usage contexts:
1. Check-in detection → Use burst_start (earliest)
2. Check-out detection → Use burst_end (latest)
3. Break Out detection → Use burst_end (latest before gap)
4. Break In detection → Use burst_start (earliest after gap)
5. Gap calculation → burst[i].end to burst[i+1].start
```

## Data Structure

### Recommended Representation
```python
@dataclass
class Burst:
    burst_id: int
    burst_start: datetime  # Earliest swipe
    burst_end: datetime    # Latest swipe
    swipe_count: int       # Number of swipes in burst

# DataFrame columns after burst detection
columns = [
    'Name',
    'burst_id',
    'burst_start',    # Keep both!
    'burst_end',      # Keep both!
    'output_name',
    'output_id'
]
```

## Usage in Different Contexts

### 1. First In (Check-in)
```python
# Use burst_start (earliest timestamp)
first_in_candidates = bursts[in_check_in_range]
first_in = min(first_in_candidates['burst_start'])
```

### 2. Last Out (Check-out)
```python
# Use burst_end (latest timestamp)
last_out_candidates = bursts[in_check_out_range]
last_out = max(last_out_candidates['burst_end'])
```

### 3. Break Out (Before break)
```python
# Use burst_end (latest timestamp before gap/midpoint)
break_out_burst = bursts[before_gap_or_midpoint]
break_out = break_out_burst['burst_end']  # NOT burst_start!
```

Example from rule.yaml scenario_2:
```
Burst: 09:55-10:01 (6 swipes)
Break Out = 10:01  ← burst_end, NOT 09:55
```

### 4. Break In (After break)
```python
# Use burst_start (earliest timestamp after gap/midpoint)
break_in_burst = bursts[after_gap_or_midpoint]
break_in = break_in_burst['burst_start']  # NOT burst_end!
```

### 5. Gap Calculation
```python
# Gap = next burst_start - current burst_end
for i in range(len(bursts) - 1):
    gap = bursts[i+1].burst_start - bursts[i].burst_end
    if gap >= minimum_break_gap:
        break_out = bursts[i].burst_end      # End of burst before gap
        break_in = bursts[i+1].burst_start   # Start of burst after gap
```

## Edge Cases

### 1. Single-Swipe "Burst"
```python
# Still create burst record
burst_start = swipe_time
burst_end = swipe_time
swipe_count = 1
```

### 2. Midnight-Spanning Burst
```python
# Burst: 23:58, 23:59, 00:00, 00:01
# Belongs to shift starting on Day N (not fragmented)
burst_start = Day_N 23:58
burst_end = Day_N+1 00:01  # Next calendar day
```

### 3. Exactly 2-Minute Gap
```python
# ≤ 2 minutes = same burst (inclusive)
swipe1 = 10:00:00
swipe2 = 10:02:00  # Exactly 120 seconds
→ Same burst (10:00:00 - 10:02:00)

swipe3 = 10:02:01  # 121 seconds
→ New burst
```

## Current Code Issues

### Problem in processor.py line 140
```python
# CURRENT (WRONG):
burst_groups['timestamp'] = burst_groups['burst_start']

# This loses burst_end information!
# Later code uses 'timestamp' for ALL logic → always uses earliest
```

### Fix Required
```python
# Keep both timestamps
burst_groups['timestamp'] = burst_groups['burst_start']  # For shift classification
# But ALSO keep burst_end column for break detection!

# Or refactor to use appropriate timestamp contextually:
def find_break_out(bursts):
    return bursts['burst_end']  # Use latest

def find_break_in(bursts):
    return bursts['burst_start']  # Use earliest
```

## Implementation Complexity
- Time: O(n log n) for sorting + O(n) for grouping = O(n log n)
- Space: O(n) for burst records

## Validation Rules
1. burst_end >= burst_start (always)
2. All swipes within burst have time_diff ≤ 2 minutes
3. Consecutive bursts have gap > 2 minutes
4. Both timestamps preserved through pipeline
5. Context-appropriate timestamp used for each operation
