# Code Standards - Attendance Data Processor

**Project:** Attendance Data Processor
**Version:** 2.0.0
**Date:** 2025-11-04
**Language:** Python 3.9+

---

## Overview

This document defines coding standards, patterns, and best practices for attendance processor codebase. Follows YAGNI (You Aren't Gonna Need It), KISS (Keep It Simple), DRY (Don't Repeat Yourself) principles.

---

## Code Organization

### Module Structure

**5 Core Modules:**
1. `main.py` - CLI entry point, orchestration
2. `config.py` - Configuration parsing (rule.yaml)
3. `processor.py` - Core processing logic
4. `validators.py` - Input validation
5. `utils.py` - File utilities

**Principle:** Single Responsibility - each module has ONE purpose

---

### File Size Guidelines

| File Type | Max LOC | Current | Status |
|-----------|---------|---------|--------|
| Module | 500 | 498 (processor.py) | ✅ Acceptable |
| Total Project | 1000 | 837 | ✅ Good |
| Method | 50 | 113 (_detect_shift_instances) | ⚠️ Exception |
| Test File | 500 | 443 (test_scenarios.py) | ✅ Good |

**Exception:** `_detect_shift_instances` (113 lines) - complex shift detection logic, well-documented

---

### Directory Structure

```
project_clean/
├── config.py                # Config parsing
├── processor.py             # Core logic
├── main.py                  # CLI
├── validators.py            # Validation
├── utils.py                 # Utilities
├── rule.yaml                # Business rules
├── requirements.txt         # Dependencies
├── pytest.ini               # Test config
├── tests/
│   ├── test_config.py
│   ├── test_scenarios.py
│   ├── test_real_data.py
│   └── test_processor.py
├── docs/
│   ├── codebase-summary.md
│   ├── project-overview-pdr.md
│   ├── code-standards.md    # This file
│   ├── system-architecture.md
│   ├── tech-stack.md
│   └── user-guide.md
└── plans/
    ├── 251104-fix-code-per-ruleset.md
    └── reports/
        ├── 251104-tester-comprehensive-test-report.md
        └── 251104-code-reviewer-comprehensive-review.md
```

---

## Naming Conventions

### Variables

**General Rules:**
- `snake_case` for all variables, functions, methods
- Descriptive names (no abbreviations unless common)
- Single letter only for loop counters (i, j) or lambda parameters

**Examples:**
```python
# Good
burst_threshold_minutes = 2
check_in_start = time(5, 30)
df_filtered = df[df['Status'] == 'Success'].copy()

# Bad
brstThrshld = 2  # Too abbreviated
checkInStart = time(5, 30)  # camelCase (wrong style)
d = df[df['Status'] == 'Success'].copy()  # Too generic
```

---

### Functions and Methods

**Public Methods:** `verb_noun` format
```python
def load_excel(path: str) -> pd.DataFrame:
def filter_valid_users(df: pd.DataFrame) -> pd.DataFrame:
def detect_bursts(df: pd.DataFrame) -> pd.DataFrame:
```

**Private Methods:** `_verb_noun` format (single underscore prefix)
```python
def _time_in_range(self, time_series, start, end):
def _find_first_in(self, group, shift_cfg):
def _detect_breaks(self, group, shift_cfg):
```

**Helper Functions:** `parse_*`, `validate_*`, `auto_*`
```python
def parse_time(s: str) -> time:
def validate_input_file(path: str) -> Tuple[bool, str]:
def auto_rename_if_exists(path: str) -> str:
```

---

### Classes

**PascalCase:**
```python
class AttendanceProcessor:
class RuleConfig:
class ShiftConfig:
```

---

### Constants

**UPPER_SNAKE_CASE:**
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_BURST_THRESHOLD = 2  # minutes
```

**Note:** Currently no global constants (all config-driven from rule.yaml)

---

### Files

**Python Modules:** `lowercase_underscore.py`
```
config.py
processor.py
validators.py
```

**Test Files:** `test_<module_name>.py`
```
test_config.py
test_processor.py
test_scenarios.py
```

**Documentation:** `kebab-case.md` or `PascalCase.md`
```
code-standards.md
user-guide.md
README.md
```

---

## Data Structures & Types

### Dataclasses (Preferred for Config)

**Use `@dataclass` for configuration objects:**
```python
from dataclasses import dataclass

@dataclass
class ShiftConfig:
    """Configuration for a single shift"""
    name: str
    display_name: str
    check_in_start: time
    check_in_end: time
    # ... other fields

    def is_in_check_in_range(self, t: time) -> bool:
        """Check if time falls in check-in range"""
        # Implementation
```

**Benefits:**
- Immutable by default (add `frozen=True` if needed)
- Auto-generated `__init__`, `__repr__`
- Type hints built-in
- Clean, readable

---

### DataFrames

**Column Naming:**
- Use descriptive names: `timestamp`, `burst_start`, `burst_end`
- Avoid ambiguous names: `time_only` → `time_start`, `time_end`

**Key Columns (Standard):**
```python
# Input columns
df = pd.DataFrame({
    'ID': [...],
    'Name': [...],
    'Date': [...],
    'Time': [...],
    'Status': [...]
})

# After burst detection
df = pd.DataFrame({
    'Name': [...],
    'burst_id': [...],
    'burst_start': [...],  # Earliest timestamp in burst
    'burst_end': [...],    # Latest timestamp in burst
    'output_name': [...],
    'output_id': [...]
})

# After shift instance detection
df['shift_code'] = ...      # A/B/C
df['shift_date'] = ...       # Shift START date
df['shift_instance_id'] = ...  # Unique ID per shift instance
```

**DataFrame Operations:**
```python
# Always use copy() after filtering to avoid SettingWithCopyWarning
df = df[df['Status'] == 'Success'].copy()

# Use vectorized operations (NOT loops)
df['time_diff'] = df.groupby('Name')['timestamp'].diff()

# Use errors='coerce' for timestamp parsing (permissive)
df['timestamp'] = pd.to_datetime(..., errors='coerce')
```

---

## Design Patterns

### 1. Pipeline Pattern

**Usage:** Sequential data transformation stages

**Implementation (processor.py):**
```python
def process(self, input_path: str, output_path: str):
    df = self._load_excel(input_path)
    df = self._filter_valid_status(df)
    df = self._filter_valid_users(df)
    df = self._detect_bursts(df)
    df = self._detect_shift_instances(df)
    df = self._extract_attendance_events(df)
    self._write_output(df, output_path)
```

**Benefits:**
- Clear data flow
- Each stage testable independently
- Easy to add/remove stages
- Readable

---

### 2. Strategy Pattern (Config-Driven)

**Usage:** Behavior controlled by rule.yaml (no hardcoded values)

**Implementation (config.py):**
```python
@dataclass
class RuleConfig:
    burst_threshold_minutes: int
    valid_users: Dict[str, Dict[str, str]]
    shifts: Dict[str, ShiftConfig]

    @classmethod
    def load_from_yaml(cls, path: str) -> 'RuleConfig':
        # Parse YAML, return config object
```

**Benefits:**
- Business rules externalized
- No code changes for config updates
- Testable with different configs
- Maintainable

---

### 3. Diff-Cumsum Pattern (Vectorized)

**Usage:** Burst detection - fast, elegant

**Implementation (processor.py:114-145):**
```python
# Calculate time difference between consecutive swipes
df['time_diff'] = df.groupby('Name')['timestamp'].diff()

# Mark burst boundaries
df['new_burst'] = (df['time_diff'] > threshold) | df['time_diff'].isna()

# Create burst IDs (cumulative sum of boundaries)
df['burst_id'] = df.groupby('Name')['new_burst'].cumsum()

# Aggregate bursts
burst_groups = df.groupby(['Name', 'burst_id']).agg({
    'timestamp': ['min', 'max']  # burst_start, burst_end
})
```

**Benefits:**
- O(n) complexity (fast)
- Vectorized (pandas optimized)
- No loops
- Elegant

---

### 4. Two-Tier Fallback Pattern

**Usage:** Break detection - try primary method, fall back to secondary

**Implementation (processor.py:332-445):**
```python
def _detect_breaks(self, group, shift_cfg):
    # PRIORITY 1: Try gap-based detection
    if len(break_swipes) >= 2:
        qualifying_gaps = break_swipes[break_swipes['gap_minutes'] >= min_gap]
        if len(qualifying_gaps) > 0:
            return (break_out, break_in)  # Success!

    # PRIORITY 2: Fall back to midpoint logic
    return self._midpoint_fallback(break_swipes, midpoint, min_gap)
```

**Benefits:**
- Robust (handles edge cases)
- Clear priority (gap → midpoint)
- Maintainable

---

## Error Handling

### Philosophy: Permissive with Warnings

**Principle:** Skip invalid data, warn user, continue processing

**Example (processor.py:70-74):**
```python
invalid_count = df['timestamp'].isna().sum()
if invalid_count > 0:
    print(f"   ⚠ Skipped {invalid_count} rows with invalid timestamps")
    df = df[df['timestamp'].notna()].copy()
```

---

### Error Handling Hierarchy

**Level 1: Input Validation (validators.py)**
- Return `(bool, error_msg)` tuples
- Don't raise exceptions
- Let caller decide how to handle

```python
def validate_input_file(path: str) -> Tuple[bool, str]:
    p = Path(path)
    if not p.exists():
        return False, f"File not found: {path}"
    if p.suffix.lower() not in ['.xlsx', '.xls']:
        return False, f"Invalid file type..."
    return True, ""
```

**Level 2: Processing (processor.py)**
- Use `errors='coerce'` for pandas operations
- Filter invalid data with warnings
- Raise `ValueError` for critical errors (missing columns)

```python
# Permissive
df['timestamp'] = pd.to_datetime(..., errors='coerce')

# Strict (critical requirement)
if missing:
    raise ValueError(f"Missing required columns: {', '.join(missing)}")
```

**Level 3: CLI (main.py)**
- Catch specific exceptions first, generic last
- Print user-friendly messages
- Return exit codes (0=success, 1=error)

```python
try:
    processor.process(input_path, output_path)
except FileNotFoundError as e:
    print(f"❌ Error: File not found - {e}")
    return 1
except ValueError as e:
    print(f"❌ Error: Invalid data - {e}")
    return 1
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    traceback.print_exc()
    return 1
```

---

## Documentation Standards

### Docstrings

**Module Docstring (top of file):**
```python
"""Core attendance data processing pipeline"""
```

**Class Docstring:**
```python
class AttendanceProcessor:
    """Process raw biometric logs into cleaned attendance records"""
```

**Method Docstring (Google Style):**
```python
def _time_in_range(self, time_series: pd.Series,
                   start: pd.Timestamp.time,
                   end: pd.Timestamp.time) -> pd.Series:
    """Check if times fall within range, handling midnight-spanning ranges

    Args:
        time_series: Series of time objects
        start: Range start time
        end: Range end time

    Returns:
        Boolean series indicating if each time is in range

    Example:
        >>> times = pd.Series([time(9, 30), time(10, 15)])
        >>> _time_in_range(times, time(9, 0), time(10, 0))
        0     True
        1    False
        dtype: bool
    """
```

**Complex Algorithm Docstring:**
```python
def _detect_shift_instances(self, df: pd.DataFrame) -> pd.DataFrame:
    """Detect shift instances based on First In swipes (check-in range)

    CRITICAL: Implements shift-instance grouping per rule.yaml v9.0
    - One shift instance = one complete attendance record
    - Night shifts crossing midnight stay as single record
    - Date = shift START date, not individual swipe calendar dates

    Algorithm:
    1. Find all check-in swipes (potential shift starts)
    2. For each check-in, create shift instance with activity window
    3. Assign all subsequent swipes to instance until next check-in
    4. Handle night shift midnight crossing

    Args:
        df: DataFrame with burst_start, burst_end, Name, output_name, output_id

    Returns:
        DataFrame with added columns: shift_code, shift_date, shift_instance_id

    Raises:
        None - orphan swipes filtered out with warning
    """
```

---

### Inline Comments

**When to Use:**
- Complex logic (algorithms)
- Non-obvious behavior
- Workarounds / hacks
- Important context

**When NOT to Use:**
- Obvious code (`i += 1  # increment i`)
- Self-documenting code

**Good Examples:**
```python
# PRIORITY 1: Try gap-based detection first
if len(break_swipes) >= 2:
    ...

# Night shift: activity window ends at 06:35 NEXT day
window_end = datetime.combine(shift_date + timedelta(days=1),
                               shift_cfg.check_out_end)

# Gap = time from end of previous burst to start of next burst
gap = next_swipe['burst_start'] - current['burst_end']
```

---

## Testing Standards

### Test Structure

**Naming:**
- Test functions: `test_<function_name>_<scenario>`
- Test files: `test_<module_name>.py`

```python
def test_burst_detection_simple():
def test_burst_detection_midnight_spanning():
def test_scenario_4_night_shift_crossing_midnight():
```

---

### Test Coverage Requirements

| Component | Min Coverage | Current |
|-----------|--------------|---------|
| Critical paths | 100% | 100% ✅ |
| Core logic | 80% | ~85% ✅ |
| Edge cases | 70% | ~75% ✅ |
| Overall | 70% | 72% ⚠️ |

**Focus:** Test scenarios (rule.yaml requirements) > unit tests

---

### Fixtures

**Use pytest fixtures for reusable test data:**
```python
@pytest.fixture
def config():
    """Load rule.yaml config for tests"""
    return RuleConfig.load_from_yaml('rule.yaml')

@pytest.fixture
def scenario_4_input():
    """Night shift crossing midnight - scenario_4 from rule.yaml"""
    return pd.DataFrame([
        {'Name': 'Capone', 'timestamp': datetime(2025, 11, 3, 21, 55, 28)},
        {'Name': 'Capone', 'timestamp': datetime(2025, 11, 4, 2, 0, 35)},
        # ...
    ])
```

---

### Assertions

**Use descriptive assertions:**
```python
# Good
assert len(result['shift_instance_id'].unique()) == 1, \
    "Night shift should be single instance"

# Bad
assert len(result['shift_instance_id'].unique()) == 1
```

---

## Code Quality Tools

### Required Checks

**Before Commit:**
1. ✅ All tests pass: `pytest tests/ -v`
2. ✅ No syntax errors: `python -m py_compile *.py`
3. ✅ Imports resolve: `python -c "import config, processor, validators"`

**Recommended (Future):**
1. Code formatting: `black *.py`
2. Linting: `flake8 *.py`
3. Type checking: `mypy *.py`
4. Coverage: `pytest --cov=. --cov-report=html`

---

## Performance Guidelines

### Optimization Principles

1. **Use Vectorized Operations** (NOT loops)
   ```python
   # Good
   df['time_diff'] = df.groupby('Name')['timestamp'].diff()

   # Bad
   for i in range(len(df)):
       df.loc[i, 'time_diff'] = ...
   ```

2. **Minimize DataFrame Copies**
   ```python
   # Good (single copy)
   mask = (df['Status'] == 'Success') & (df['Name'].isin(valid_users))
   df = df[mask].copy()

   # Bad (multiple copies)
   df = df[df['Status'] == 'Success'].copy()
   df = df[df['Name'].isin(valid_users)].copy()
   ```

3. **Use Efficient Aggregations**
   ```python
   # Good (single pass)
   burst_groups = df.groupby(['Name', 'burst_id']).agg({
       'timestamp': ['min', 'max']
   })

   # Bad (two passes)
   burst_start = df.groupby(['Name', 'burst_id'])['timestamp'].min()
   burst_end = df.groupby(['Name', 'burst_id'])['timestamp'].max()
   ```

---

### Performance Targets

| Dataset Size | Target Time | Current |
|--------------|-------------|---------|
| 90-200 rows | <0.5s | 0.202s ✅ |
| 1,000 rows | <2s | ~1s ✅ |
| 10,000 rows | <10s | ~10s ✅ |

---

## Version Control Standards

### Commit Messages

**Format:** `<type>: <short summary>`

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructure (no behavior change)
- `docs`: Documentation only
- `test`: Test additions/updates
- `perf`: Performance improvement

**Examples:**
```
feat: add gap-based break detection (Priority 1)
fix: preserve burst_end for Break Out extraction
refactor: replace _classify_shifts with _detect_shift_instances
docs: update README with gap-based break detection
test: add scenario 3 test (late break with gap)
perf: optimize shift instance detection with early break
```

---

### Branch Naming

**Format:** `<type>/<short-description>`

**Examples:**
```
feat/gap-based-break-detection
fix/burst-representation
refactor/shift-instance-grouping
docs/update-architecture
```

---

## Security Standards

### Input Validation

**Always Validate:**
1. File existence, type, readability
2. Required columns presence
3. Data types (timestamps, IDs)
4. User whitelist membership

**Never Trust:**
1. User input (file paths, names)
2. Excel cell contents (potential formulas)
3. File sizes (potential memory issues)

---

### Known Gaps (TODO)

1. **Excel Formula Injection**
   - Risk: Name/ID contains `=cmd|'/c calc'!A1`
   - Mitigation: Sanitize cell values starting with `=`, `+`, `-`, `@`
   - Priority: MEDIUM

2. **File Size Limit**
   - Risk: 100MB Excel file causes memory error
   - Mitigation: Check file size before loading (max 10MB)
   - Priority: LOW

---

## Code Review Checklist

**Before Approving PR:**

**Functionality:**
- ✅ All tests pass
- ✅ Code implements requirements correctly
- ✅ Edge cases handled

**Code Quality:**
- ✅ Follows naming conventions
- ✅ Methods <50 lines (exceptions documented)
- ✅ No hardcoded values (config-driven)
- ✅ No code duplication (DRY)

**Documentation:**
- ✅ Docstrings on public methods
- ✅ Complex logic has comments
- ✅ README updated if needed

**Testing:**
- ✅ New features have tests
- ✅ Bug fixes have regression tests
- ✅ Coverage >70%

**Performance:**
- ✅ No obvious bottlenecks
- ✅ Vectorized operations used
- ✅ DataFrame copies minimized

---

## Architectural Principles

### 1. YAGNI (You Aren't Gonna Need It)
**Implementation:**
- No speculative features
- Implement ONLY rule.yaml requirements
- No premature abstractions

**Examples:**
- ✅ No "multiple breaks per shift" (rule.yaml says NOT implemented)
- ✅ No database integration (not required)
- ✅ No web UI (CLI sufficient)

---

### 2. KISS (Keep It Simple, Stupid)
**Implementation:**
- Simple algorithms (diff-cumsum, not complex state machines)
- Flat structure (5 modules, not 20 classes)
- Readable code > clever code

**Examples:**
- ✅ Diff-cumsum for burst detection (simple, fast)
- ✅ Nested loop for shift detection (clear, maintainable)
- ✅ Dataclasses for config (simple, effective)

---

### 3. DRY (Don't Repeat Yourself)
**Implementation:**
- Config-driven logic (rule.yaml, not hardcoded)
- Reusable helper methods (`_time_in_range`)
- No code duplication

**Examples:**
- ✅ `_time_in_range` used for check-in, check-out, break windows
- ✅ `parse_time` reused for all time parsing
- ✅ Shift configs in loop (not duplicated A/B/C)

---

## Dependencies Management

### Adding Dependencies

**Criteria:**
1. Mature, well-maintained (>1000 stars, active commits)
2. Widely used (>10M downloads/month)
3. Minimal transitive dependencies
4. Compatible with Python 3.9+

**Process:**
1. Add to `requirements.txt` with version constraint
2. Test installation in fresh venv
3. Update docs if needed

**Current Dependencies:** All meet criteria ✅

---

### Version Pinning

**Strategy:** Minimum version constraints (allow patch updates)

```
# requirements.txt
pandas>=2.0.0
openpyxl>=3.1.0
pyyaml>=6.0.0
xlsxwriter>=3.0.0
pytest>=7.4.0
```

**Benefits:**
- Security patches auto-applied
- Bug fixes auto-applied
- Breaking changes prevented (major version locked)

---

## Deprecation Policy

**When Removing Features:**
1. Add deprecation warning (1 version before removal)
2. Update documentation
3. Provide migration guide
4. Remove in next major version

**Example:**
```python
import warnings

def old_method():
    warnings.warn(
        "old_method is deprecated, use new_method instead",
        DeprecationWarning,
        stacklevel=2
    )
    return new_method()
```

---

## Conclusion

These standards ensure codebase remains clean, maintainable, performant. Follow principles: YAGNI, KISS, DRY. Write tests first. Document complex logic. Optimize for readability, not cleverness. When in doubt, prefer simplicity.

**Current Compliance:** ~95% (excellent)
**Exceptions:** 1 method >100 lines (documented), 9 legacy unit tests (technical debt)
