# Phase 4: Test Strategy - Break Time Out Checkpoint Fix

## Test Pyramid

```
         /\
        /  \  Integration Tests (2)
       /----\
      /      \  Unit Tests (5)
     /--------\
    / Scenario \ Scenario Tests (3)
   /____________\
```

## Test Categories

### 1. Scenario Tests (High Priority)
**Purpose:** Validate against real-world use cases from rule.yaml
**Files:** test_scenarios.py
**Count:** 3 scenarios affected

### 2. Unit Tests (Medium Priority)
**Purpose:** Test individual method behavior
**Files:** test_processor.py
**Count:** 5 new/updated tests

### 3. Integration Tests (Low Priority)
**Purpose:** End-to-end validation with real data
**Files:** Manual verification
**Count:** 2 manual tests

## Scenario Test Cases

### Scenario 1: Multiple Gaps - Checkpoint Priority (NEW)

**Test Name:** `test_scenario_multiple_gaps_checkpoint_priority`

**Input Data:**
```python
Silver_Bui on 2025-11-06 (Shift C - Night):
- 02:01:45 (Row 418)
- 02:13:00 (Row 420)
- 02:13:01 (Row 421)
- 02:39:33 (Row 423)
```

**Configuration:**
- Shift C checkpoint: 02:00:00
- Shift C cutoff: 02:49:59
- Minimum gap: 5 minutes

**Gap Analysis:**
- Gap 1: 02:01:45 → 02:13:00 (11.25 min ✅)
  - Break Out distance from checkpoint: 105 sec
  - Break In distance from cutoff: 2219 sec
- Gap 2: 02:13:01 → 02:39:33 (26.53 min ✅)
  - Break Out distance from checkpoint: 781 sec
  - Break In distance from cutoff: 626 sec

**Expected Result:**
```python
assert break_out == "02:01:45"  # Gap 1 (closer to checkpoint)
assert break_in == "02:13:00"   # From same gap
```

**Test Implementation:**
```python
def test_scenario_multiple_gaps_checkpoint_priority():
    """Test checkpoint priority with multiple qualifying gaps (Shift C)"""
    config = RuleConfig.load_from_yaml('rule.yaml')
    processor = AttendanceProcessor(config)

    group = pd.DataFrame([
        {
            'burst_start': datetime(2025, 11, 6, 2, 1, 45),
            'burst_end': datetime(2025, 11, 6, 2, 1, 45),
            'time_start': time(2, 1, 45),
            'time_end': time(2, 1, 45),
        },
        # ... other timestamps ...
    ])

    shift_cfg = config.shifts['C']
    break_out, break_in, _ = processor._detect_breaks(group, shift_cfg)

    assert break_out == "02:01:45", \
        f"Expected Break Out from gap closest to checkpoint (02:00:00), got {break_out}"
    assert break_in == "02:13:00", \
        f"Expected Break Time In from same gap, got {break_in}"
```

### Scenario 2: Single Gap - Should Still Work

**Test Name:** `test_scenario_single_gap_checkpoint`

**Input Data:**
```python
Shift A timestamps:
- 09:55:00
- 10:05:00 (10 min gap - qualifies)
```

**Expected Result:**
```python
assert break_out == "09:55:00"  # Only gap
assert break_in == "10:05:00"   # Only gap
```

**Purpose:** Verify single gap selection unchanged

### Scenario 3: No Qualifying Gaps - Midpoint Fallback

**Test Name:** `test_scenario_no_gaps_midpoint_fallback`

**Input Data:**
```python
Shift A timestamps:
- 10:08:00
- 10:10:00 (2 min gap - too small)
- 10:12:00 (2 min gap - too small)
```

**Configuration:**
- Midpoint: 10:15:00

**Expected Result:**
```python
# Falls back to midpoint logic (Priority 2)
assert break_out == "10:12:00"  # Latest before midpoint
assert break_in == ""            # None after midpoint
```

**Purpose:** Verify fallback logic unchanged

## Unit Test Cases

### Unit Test 1: Helper Method - Time Distance Calculation

**Test Name:** `test_calculate_time_distance`

**Test Cases:**
```python
def test_calculate_time_distance():
    config = RuleConfig.load_from_yaml('rule.yaml')
    processor = AttendanceProcessor(config)

    # Test 1: Same times
    assert processor._calculate_time_distance(time(10, 0, 0), time(10, 0, 0)) == 0

    # Test 2: 1 minute difference
    assert processor._calculate_time_distance(time(10, 0, 0), time(10, 1, 0)) == 60

    # Test 3: 1 hour 45 seconds
    assert processor._calculate_time_distance(time(10, 0, 0), time(11, 0, 45)) == 3645

    # Test 4: Time 1 > Time 2 (absolute distance)
    assert processor._calculate_time_distance(time(10, 5, 0), time(10, 0, 0)) == 300

    # Test 5: Across hours
    assert processor._calculate_time_distance(time(9, 58, 0), time(10, 2, 0)) == 240
```

### Unit Test 2: Gap Selection - Checkpoint Priority (Shift A)

**Test Name:** `test_gap_selection_checkpoint_priority_shift_a`

**Input:**
```python
Shift A timestamps:
- 09:50:00 (checkpoint distance: 10 min = 600 sec)
- 09:55:00 (5 min gap)
- 10:25:00 (checkpoint distance: 25 min = 1500 sec)
- 10:30:00 (5 min gap)
```

**Configuration:**
- Shift A checkpoint: 10:00:00
- Shift A cutoff: 10:34:59

**Expected:**
```python
# Gap 1: 09:50 → 09:55 (Break Out 600 sec from checkpoint)
# Gap 2: 10:25 → 10:30 (Break Out 1500 sec from checkpoint)
# Expected: Gap 1 selected (closer to checkpoint)

assert break_out == "09:50:00"
assert break_in == "09:55:00"
```

### Unit Test 3: Gap Selection - Checkpoint Priority (Shift B)

**Test Name:** `test_gap_selection_checkpoint_priority_shift_b`

**Purpose:** Verify checkpoint priority works for Shift B

**Configuration:**
- Shift B checkpoint: 18:00:00
- Shift B cutoff: 18:34:59

### Unit Test 4: Edge Case - All Gaps Same Distance

**Test Name:** `test_edge_case_equal_checkpoint_distances`

**Input:**
```python
Shift A timestamps with symmetric gaps:
- 09:55:00 (5 min from checkpoint)
- 10:05:00
- 10:05:01 (5 min from checkpoint)
- 10:15:00
```

**Expected:**
```python
# Should select first gap (deterministic tie-breaking)
assert break_out == "09:55:00"
assert break_in == "10:05:00"
```

### Unit Test 5: Configuration Loading - Checkpoint Field

**Test Name:** `test_config_loads_checkpoint`

**Purpose:** Verify checkpoint loaded from rule.yaml

```python
def test_config_loads_checkpoint():
    config = RuleConfig.load_from_yaml('rule.yaml')

    # Shift A
    assert config.shifts['A'].break_out_checkpoint == time(10, 0, 0)

    # Shift B
    assert config.shifts['B'].break_out_checkpoint == time(18, 0, 0)

    # Shift C
    assert config.shifts['C'].break_out_checkpoint == time(2, 0, 0)
```

## Integration Test Cases

### Integration Test 1: Real Data - Silver_Bui 2025-11-06

**Test Type:** Manual verification

**Data Source:** testting.xlsx rows 418-423

**Procedure:**
1. Run processor: `python main.py testting.xlsx output_test.xlsx`
2. Open output_test.xlsx
3. Find row for Silver_Bui on 2025-11-06
4. Verify values

**Expected Output:**
```
Date: 2025-11-06
Name: Bui Duc Toan (Silver_Bui)
Shift: Night
Check In: (TBD based on data)
Break Time Out: 02:01:45 ✅
Break Time In: 02:13:00 or 02:39:33 (depends on paired vs independent)
Check Out: (TBD based on data)
```

**Pass Criteria:**
- Break Time Out = 02:01:45 (NOT 02:13:01)

### Integration Test 2: Full Test Suite with Real Data

**Test Type:** Automated

**Data Source:** All available test files

**Procedure:**
```bash
# Run all scenario tests
pytest tests/test_scenarios.py -v

# Expected: All scenarios pass
```

## Test Execution Plan

### Phase 1: Pre-Implementation Validation
```bash
# Run existing tests to establish baseline
pytest tests/ -v > baseline_tests.txt

# Expected: Some tests may fail (using old logic)
```

### Phase 2: Configuration Update Testing
```bash
# Test config loading after rule.yaml update
python -c "from config import RuleConfig; cfg = RuleConfig.load_from_yaml('rule.yaml'); print(cfg.shifts['A'].break_out_checkpoint)"

# Expected output: 10:00:00
```

### Phase 3: Unit Test Development
```bash
# Add and run new unit tests incrementally
pytest tests/test_processor.py::test_calculate_time_distance -v
pytest tests/test_processor.py::test_config_loads_checkpoint -v
pytest tests/test_processor.py::test_gap_selection_checkpoint_priority_shift_a -v

# Expected: All new tests pass
```

### Phase 4: Implementation Testing
```bash
# After implementing gap selection fix
pytest tests/test_processor.py::test_scenario_multiple_gaps_checkpoint_priority -v

# Expected: Test passes with correct Break Time Out
```

### Phase 5: Regression Testing
```bash
# Update existing test expectations
pytest tests/test_processor.py -v

# Fix any failing tests by updating expectations
```

### Phase 6: Full Suite Validation
```bash
# Run all tests
pytest tests/ -v --cov=. --cov-report=term-missing

# Expected:
# - All tests pass
# - Coverage ≥ 70%
# - No regressions
```

### Phase 7: Integration Testing
```bash
# Process real data
python main.py testting.xlsx output_integration_test.xlsx

# Manual verification of results
```

## Test Data Requirements

### Required Test Files
1. **rule.yaml** - with updated checkpoint configuration
2. **testting.xlsx** - real attendance data (if available)
3. **Mock data** - for scenario tests

### Test Data Coverage

**Shift Coverage:**
- ✅ Shift A (Morning) - at least 2 tests
- ✅ Shift B (Afternoon) - at least 1 test
- ✅ Shift C (Night) - at least 2 tests

**Gap Coverage:**
- ✅ No qualifying gaps (midpoint fallback)
- ✅ Single qualifying gap
- ✅ Multiple qualifying gaps (checkpoint priority)
- ✅ Equal distances (tie-breaking)

**Edge Cases:**
- ✅ Timestamps exactly at checkpoint
- ✅ Timestamps exactly at cutoff
- ✅ Timestamps outside search range
- ✅ Single swipe in break window

## Expected Test Results

### Before Fix
```
Total Tests: 32
Passed: 23
Failed: 9 (incorrect Break Time Out selection)
```

### After Fix
```
Total Tests: 37 (5 new tests added)
Passed: 37
Failed: 0
Coverage: ≥ 72%
```

## Performance Testing

### Benchmark Test

**Test Name:** `test_performance_break_detection`

```python
def test_performance_break_detection():
    """Verify break detection performance after checkpoint fix"""
    import time
    from processor import AttendanceProcessor
    from config import RuleConfig

    config = RuleConfig.load_from_yaml('rule.yaml')
    processor = AttendanceProcessor(config)

    # Create large test dataset
    large_group = pd.DataFrame([
        # 100 timestamps with multiple gaps
    ])

    shift_cfg = config.shifts['A']

    start = time.time()
    for _ in range(100):
        processor._detect_breaks(large_group, shift_cfg)
    elapsed = time.time() - start

    # Expected: < 0.1s for 100 iterations
    assert elapsed < 0.1, f"Performance degraded: {elapsed:.3f}s"
```

## Test Coverage Goals

### Method Coverage
- `_detect_breaks()`: 100% (all branches)
- `_calculate_time_distance()`: 100%
- Configuration loading: 100%

### Scenario Coverage
- All 3 shifts: 100%
- Priority 1 (gap detection): 100%
- Priority 2 (midpoint fallback): 100%
- Edge cases: ≥ 80%

### Overall Coverage
**Target:** ≥ 72% (maintain current level)
**Stretch Goal:** ≥ 75%

## Test Maintenance

### After Implementation

**Update test expectations:**
1. Review all tests using gap-based detection
2. Update expected Break Time Out values
3. Add comments explaining checkpoint priority
4. Document test data scenarios

**Test documentation:**
1. Add docstrings to all new tests
2. Explain why specific values expected
3. Reference rule.yaml configuration

## Automated Test Execution

### CI/CD Integration (Future)

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Failure Handling

### If Tests Fail

**Scenario 1: Configuration loading fails**
```
Error: KeyError: 'checkpoint'
Solution: Verify rule.yaml syntax, check config.py parsing logic
```

**Scenario 2: Break Time Out incorrect**
```
AssertionError: Expected 02:01:45, got 02:13:01
Solution: Check gap selection logic, verify checkpoint distance calculation
```

**Scenario 3: Break Time In incorrect**
```
AssertionError: Expected 02:13:00, got 02:39:33
Solution: Verify paired gap selection (both from same gap)
```

## Success Criteria

Testing phase complete when:

1. ✅ All new unit tests pass (5 tests)
2. ✅ All scenario tests pass (3 scenarios)
3. ✅ Integration test validates real data
4. ✅ Performance benchmark passes (< 0.5s)
5. ✅ Test coverage ≥ 72%
6. ✅ No regressions in existing functionality
7. ✅ Test documentation complete

## Unresolved Testing Questions

1. **Should we add tests for invalid configurations?**
   - Missing checkpoint field
   - Checkpoint > cutoff
   - Checkpoint outside search range

2. **Should we test paired vs. independent gap selection?**
   - Only if implementing independent selection
   - May need separate test suite

3. **Should we add visual test output?**
   - Show gap selection decisions
   - Useful for debugging
   - May clutter test output
