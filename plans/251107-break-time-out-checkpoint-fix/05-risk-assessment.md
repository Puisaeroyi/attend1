# Phase 5: Risk Assessment & Rollback Plan

## Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| Configuration breaking change | HIGH | HIGH | 🔴 CRITICAL | Validation, migration guide |
| Incorrect gap selection | MEDIUM | HIGH | 🟠 HIGH | Comprehensive testing |
| Performance degradation | LOW | MEDIUM | 🟡 MEDIUM | Benchmarking |
| Test regression | MEDIUM | MEDIUM | 🟡 MEDIUM | Baseline comparison |
| Documentation outdated | LOW | LOW | 🟢 LOW | Review checklist |

## Detailed Risk Analysis

### RISK 1: Configuration Breaking Change 🔴 CRITICAL

**Description:**
Adding required `checkpoint` field to rule.yaml breaks existing configurations

**Probability:** HIGH (100% - field is required)

**Impact:** HIGH
- Existing rule.yaml files won't work
- Production deployments will fail
- Users must update configuration manually

**Symptoms:**
```python
KeyError: 'checkpoint'
# or
AttributeError: 'ShiftConfig' object has no attribute 'break_out_checkpoint'
```

**Mitigation Strategies:**

**Strategy 1: Provide default value (RECOMMENDED)**
```python
# config.py
'break_out_checkpoint': parse_time(
    break_params['break_out'].get('checkpoint',
    break_params['window'].split('-')[0])  # Default to window start
)
```

**Benefits:**
- Backward compatible
- Existing configs work without changes
- Migration optional

**Strategy 2: Explicit validation with clear error**
```python
# config.py
if 'checkpoint' not in break_params['break_out']:
    raise ValueError(
        f"Missing required field 'checkpoint' in break_out for shift {shift_name}. "
        f"Add 'checkpoint: \"{window_start}\"' to rule.yaml"
    )
```

**Benefits:**
- Forces explicit configuration
- Clear error message with solution
- No silent defaults

**Recommendation:** Strategy 1 (backward compatible with defaults)

**Rollback Plan:**
1. Restore old config.py (remove checkpoint field)
2. Restore old rule.yaml (remove checkpoint entries)
3. Restore old processor.py gap selection logic
4. Run tests to verify: `pytest tests/ -v`

---

### RISK 2: Incorrect Gap Selection 🟠 HIGH

**Description:**
New checkpoint priority logic selects wrong gap, producing incorrect Break Time Out

**Probability:** MEDIUM (30%)
- Algorithm is straightforward
- But edge cases may exist

**Impact:** HIGH
- Incorrect attendance records
- Business rule violations
- User trust issues

**Symptoms:**
- Break Time Out not closest to checkpoint
- Test failures in scenario tests
- User reports incorrect break times

**Root Causes:**
1. **Distance calculation error**
   - Off-by-one errors
   - Incorrect absolute value
   - Time overflow (midnight crossing)

2. **Gap pairing error**
   - Break Out and Break In from different gaps
   - Wrong gap index selected

3. **Edge case handling**
   - Ties (equal distances)
   - Single gap
   - No gaps (should fall back to midpoint)

**Mitigation Strategies:**

**Strategy 1: Comprehensive testing (PRIMARY)**
- Unit tests for distance calculation
- Scenario tests for real-world cases
- Edge case tests (ties, single gap, no gaps)
- Integration tests with real data

**Strategy 2: Add debug logging (SECONDARY)**
```python
# processor.py (development only)
import logging
logger = logging.getLogger(__name__)

for gap_idx in qualifying_gaps.index:
    checkpoint_distance = self._calculate_time_distance(...)
    logger.debug(
        f"Gap {gap_idx}: Break Out {break_out_time} "
        f"distance from checkpoint {checkpoint_time}: {checkpoint_distance}s"
    )
logger.debug(f"Selected gap {best_gap} with distance {min_checkpoint_distance}s")
```

**Strategy 3: Manual verification checklist**
- [ ] Process testting.xlsx
- [ ] Verify Silver_Bui 2025-11-06 Break Time Out = 02:01:45
- [ ] Spot-check 5 other records
- [ ] Compare with previous algorithm results

**Rollback Plan:**
1. Identify incorrect records
2. Revert gap selection logic (lines 402-434)
3. Re-process data with old logic
4. Compare results to identify root cause

---

### RISK 3: Performance Degradation 🟡 MEDIUM

**Description:**
Additional distance calculations slow down processing

**Probability:** LOW (10%)
- Only adds 1-2 operations per gap
- Vectorized operations still dominant

**Impact:** MEDIUM
- Slower processing for large datasets
- May exceed 0.5s target for 200 rows

**Current Baseline:**
- 199 rows: 0.202s (5.4x faster than target)
- Large margin (0.298s buffer)

**Expected Overhead:**
- Distance calculation: ~0.001s per gap
- Typical dataset: 5-10 gaps
- Expected overhead: 0.005-0.010s
- **New estimate:** 0.207-0.212s (still 2.3x faster than target)

**Mitigation Strategies:**

**Strategy 1: Benchmark testing**
```bash
# Before implementation
python benchmark.py > baseline.txt

# After implementation
python benchmark.py > after_fix.txt

# Compare
diff baseline.txt after_fix.txt
```

**Strategy 2: Performance profiling**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
processor.process('testting.xlsx', 'output.xlsx')
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 functions
```

**Strategy 3: Optimization if needed**
- Cache distance calculations
- Vectorize distance calculation (pandas)
- Use numpy for faster math operations

**Rollback Plan:**
If performance degrades > 50% (exceeds 0.3s):
1. Profile to identify bottleneck
2. Optimize distance calculation
3. If still slow, revert to old logic
4. Investigate alternative approaches

---

### RISK 4: Test Regression 🟡 MEDIUM

**Description:**
Existing tests fail due to changed gap selection behavior

**Probability:** MEDIUM (50%)
- Gap selection logic fundamentally changed
- Many tests depend on old behavior

**Impact:** MEDIUM
- Need to update test expectations
- May mask real issues
- Time-consuming to fix

**Affected Tests:**
- `test_detect_breaks_multiple_swipes` (LIKELY)
- `test_edge_case_multiple_breaks` (LIKELY)
- `test_detect_breaks_cutoff_priority_*` (CERTAIN - opposite behavior)
- Scenario tests with multiple gaps (POSSIBLE)

**Mitigation Strategies:**

**Strategy 1: Baseline comparison**
```bash
# Before implementation
pytest tests/ -v > tests_before.txt

# After implementation
pytest tests/ -v > tests_after.txt

# Compare
diff tests_before.txt tests_after.txt
```

**Strategy 2: Update expectations systematically**
1. Run tests, capture failures
2. For each failure, analyze expected vs. actual
3. Verify actual is correct (manual check)
4. Update test expectation
5. Add comment explaining change
6. Re-run test to verify

**Strategy 3: Document test changes**
```python
# Before fix (cutoff priority):
# Expected Break Time Out from gap with Break In closest to cutoff
# assert break_out == "10:25:00"

# After fix (checkpoint priority):
# Expected Break Time Out from gap closest to checkpoint (10:00:00)
assert break_out == "09:50:00"  # Gap 1: 09:50→09:55 (600s from checkpoint)
```

**Rollback Plan:**
1. Restore old test_processor.py from git
2. Restore old test_scenarios.py from git
3. Run tests to verify baseline: `pytest tests/ -v`

---

### RISK 5: Documentation Outdated 🟢 LOW

**Description:**
README, codebase summary, or other docs describe old behavior

**Probability:** LOW (20%)
- Well-defined documentation update checklist
- Small surface area

**Impact:** LOW
- Confusion for users/developers
- Incorrect understanding of algorithm
- No functional impact

**Affected Documentation:**
- README.md (break detection section)
- docs/codebase-summary.md (algorithm description)
- Inline comments in processor.py
- Docstrings in _detect_breaks()

**Mitigation Strategies:**

**Strategy 1: Documentation review checklist**
- [ ] README.md updated (break detection algorithm)
- [ ] codebase-summary.md updated (gap selection logic)
- [ ] processor.py docstrings updated
- [ ] Inline comments reviewed
- [ ] Configuration examples updated

**Strategy 2: Peer review**
- Have another developer review docs
- Check for consistency
- Verify examples are correct

**Rollback Plan:**
1. Git diff to see doc changes
2. Revert specific doc files if needed
3. Minimal impact (docs only)

---

## Additional Risks

### RISK 6: Midnight Crossing Time Comparison 🟡 MEDIUM

**Description:**
Distance calculation fails for times crossing midnight (e.g., 23:59:00 vs 00:01:00)

**Probability:** LOW (5%)
- Only affects Shift C
- Checkpoint at 02:00:00 (not near midnight)
- Break window 01:50-02:50 (not crossing midnight)

**Impact:** MEDIUM
- Incorrect distance calculation
- Wrong gap selection for night shifts

**Symptoms:**
```python
# Checkpoint: 02:00:00
# Time 1: 23:55:00 (previous day?)
# Distance: Should be ~2h 5min, calculated as 22h 55min
```

**Mitigation:**
Current implementation converts to seconds from midnight:
```python
seconds1 = time1.hour * 3600 + time1.minute * 60 + time1.second
```

**This works correctly for same-day comparisons** (all Shift C break times on same calendar day)

**Rollback Plan:**
If issue discovered:
1. Add midnight crossing logic to `_calculate_time_distance()`
2. Re-test with night shift data

---

### RISK 7: Config Field Order Dependency 🟢 LOW

**Description:**
Code relies on specific field order in rule.yaml

**Probability:** LOW (5%)
- YAML parsing is order-independent
- Python dicts preserve order (3.7+)

**Impact:** LOW
- Parsing errors if field order changes
- Easy to fix

**Mitigation:**
Use `.get()` with defaults instead of direct access:
```python
'break_out_checkpoint': parse_time(
    break_params['break_out'].get('checkpoint', window_start)
)
```

---

## Rollback Decision Matrix

| Trigger | Severity | Action | Timeline |
|---------|----------|--------|----------|
| All tests fail | 🔴 CRITICAL | Immediate rollback | < 5 min |
| >20% tests fail | 🟠 HIGH | Investigate, rollback if unfixable in 30 min | < 30 min |
| Performance >2x slower | 🟠 HIGH | Profile, rollback if unfixable | < 1 hour |
| Single test fails | 🟡 MEDIUM | Fix test expectation | < 15 min |
| Documentation issue | 🟢 LOW | Fix documentation | < 30 min |

## Comprehensive Rollback Plan

### Quick Rollback (Git Revert)

**When to use:** Critical failures, need immediate restore

**Steps:**
```bash
# 1. Check current status
git status
git log --oneline -5

# 2. Identify commit to revert
# (Assuming fix is in commit abc123)
git revert abc123

# 3. Verify rollback
pytest tests/ -v
python main.py testting.xlsx output_verify.xlsx

# 4. If successful
git push origin main
```

**Time:** < 5 minutes

---

### Partial Rollback (File-Level)

**When to use:** Specific component issues (e.g., only processor.py problem)

**Steps:**
```bash
# 1. Rollback specific file
git checkout HEAD~1 processor.py

# 2. Test
pytest tests/test_processor.py -v

# 3. If successful, commit
git add processor.py
git commit -m "fix: rollback processor.py gap selection logic"

# 4. Keep other changes (config.py, rule.yaml, docs)
```

**Time:** < 15 minutes

---

### Manual Rollback

**When to use:** Need granular control, partial revert

**Steps:**

**1. Restore processor.py gap selection (lines 402-434)**
```python
# Restore old cutoff-based selection
cutoff_time = shift_cfg.break_in_on_time_cutoff

for gap_idx in qualifying_gaps.index:
    break_in_ts = break_swipes.loc[gap_idx + 1, 'burst_start']
    break_in_time = break_in_ts.time()

    if break_in_time <= cutoff_time:
        distance = (cutoff_time seconds) - (break_in_time seconds)
    else:
        distance = (break_in_time seconds) - (cutoff_time seconds)

    if distance < min_distance_to_cutoff:
        min_distance_to_cutoff = distance
        best_gap = gap_idx
```

**2. Restore config.py (remove break_out_checkpoint)**
```python
# Remove from ShiftConfig dataclass
# Remove from load_from_yaml() parsing
```

**3. Restore rule.yaml (remove checkpoint fields)**
```yaml
# Remove checkpoint: "XX:XX:XX" from all shifts
```

**4. Restore test expectations**
```python
# Revert to old expectations in test_processor.py
```

**5. Run tests**
```bash
pytest tests/ -v
```

**Time:** < 30 minutes

---

## Validation After Rollback

### 1. Test Suite Validation
```bash
pytest tests/ -v --cov=. --cov-report=term-missing

# Expected:
# - All tests pass (same as before fix)
# - Coverage ≥ 70%
```

### 2. Integration Test
```bash
python main.py testting.xlsx output_rollback_verify.xlsx

# Verify:
# - Processing completes without errors
# - Output matches pre-fix behavior
```

### 3. Performance Check
```bash
python benchmark.py

# Expected:
# - Processing time < 0.5s (same as before)
```

## Risk Monitoring

### During Implementation

**Monitor:**
1. Test pass rate after each change
2. Processing time benchmarks
3. Configuration loading errors
4. Gap selection behavior (manual spot-checks)

**Stop conditions:**
- Test pass rate drops below 70%
- Processing time exceeds 0.5s
- Configuration loading fails
- Gap selection produces obviously wrong results

### After Deployment

**Monitor (if deployed to production):**
1. User feedback on break detection accuracy
2. Processing time in production
3. Error logs for KeyError, AttributeError
4. Data quality checks on output

**Rollback triggers:**
- Multiple user reports of incorrect break times
- Processing time > 2x baseline
- Configuration errors in production
- Data quality issues

## Success Criteria

Risk mitigation successful when:

1. ✅ All critical risks have mitigation strategies
2. ✅ Rollback plan tested and verified
3. ✅ Baseline tests captured before implementation
4. ✅ Performance benchmarks established
5. ✅ Monitoring plan defined
6. ✅ Decision matrix clear
7. ✅ Team aware of risks and rollback procedures

## Unresolved Risk Questions

1. **Should we implement feature flag for gradual rollout?**
   - Allow toggle between old and new logic
   - Useful for A/B testing
   - Adds complexity

2. **Should we add data validation checks?**
   - Verify Break Time Out closer to checkpoint than alternatives
   - Alert if distance > threshold
   - May slow processing

3. **Should we create backup before deployment?**
   - Save pre-fix output for comparison
   - Allows side-by-side validation
   - Requires storage space
