# Planner Report: Code Compliance Analysis for rule.yaml v9.0

**Date**: 2025-11-04
**Planner Agent**: Analysis Complete
**Status**: Implementation Plan Ready

---

## Executive Summary

Analyzed current Python codebase against rule.yaml v9.0 requirements. Found **5 CRITICAL violations** and **2 MEDIUM priority issues** preventing code from complying with ruleset.

**Most severe**: Shift-instance grouping not implemented - code groups by calendar_date, causing night shifts crossing midnight to fragment into multiple records instead of single unified record.

**Implementation plan created**: `/home/silver/project_clean/plans/251104-fix-code-per-ruleset.md`

**Estimated effort**: 15 hours over 2-3 days

---

## Key Rule Updates in v9.0

### 1. Shift-Instance Grouping (lines 51-72)
- One shift instance = one complete record, even crossing midnight
- Night shift: 21:30 Day_N → 06:35 Day_N+1 stays ONE record
- Date column shows shift START date, not individual swipe dates

### 2. Gap-Based Break Detection (lines 135-167)
- Priority 1: Detect gaps >= minimum_break_gap_minutes between swipes/bursts
- Priority 2: Fall back to midpoint logic only if no qualifying gap found
- Complex branching for edge cases (all before/after midpoint, single swipe)

### 3. Burst Representation (lines 74-85)
- Must preserve both burst_start (earliest) AND burst_end (latest)
- Different contexts use different timestamps (check-in uses start, break-out uses end)
- Example: Burst 09:55-10:01 → Break Out uses 10:01 (burst_end), NOT 09:55

### 4. Minimum Break Gap Parameter (lines 121, 125, 133)
- New parameter: minimum_break_gap_minutes = 5 for all shifts
- Required for gap detection algorithm

### 5. Strict Window Enforcement (line 113)
- Swipes outside defined search ranges must be excluded
- Orphan swipes without shift start → ignored

---

## Gap Analysis: CRITICAL Issues

### Issue 1: Shift-Instance Grouping NOT Implemented ❌
**Location**: `processor.py:144-161` (_classify_shifts)
**Current**: Groups by `calendar_date`
**Required**: Group by shift instance (handle midnight crossing)
**Impact**: BREAKING - Night shifts fragmented, violates core requirement
**Example Failure**:
```
Input: Night shift 2025-11-03 21:55 + swipes on 2025-11-04
Current Output: TWO records (one for 11-03, one for 11-04)
Expected Output: ONE record with Date=2025-11-03
```

### Issue 2: Gap-Based Break Detection Missing ❌
**Location**: `processor.py:228-264` (_detect_breaks)
**Current**: Only midpoint logic implemented
**Required**: Gap detection as Priority 1, midpoint as Priority 2
**Impact**: CRITICAL - Inaccurate break times when clear gaps exist
**Example Failure** (scenario_3):
```
Input: 06:00, 10:20, 10:29, 14:00 (9-min gap between 10:20-10:29)
Current Output: Break Out="", Break In=10:20 (midpoint fallback wrong)
Expected Output: Break Out=10:20, Break In=10:29 (gap-based correct)
```

### Issue 3: Burst Representation Loses burst_end ❌
**Location**: `processor.py:140`
**Current**: `burst_groups['timestamp'] = burst_groups['burst_start']` (discards burst_end)
**Required**: Preserve both burst_start AND burst_end for contextual use
**Impact**: CRITICAL - Break Out times wrong when bursts involved
**Example Failure** (scenario_2):
```
Burst: 09:55-10:01
Current Output: Break Out=09:55 (uses burst_start for everything)
Expected Output: Break Out=10:01 (should use burst_end)
```

### Issue 4: minimum_break_gap_minutes Parameter Missing ❌
**Location**: `config.py:10-97`
**Current**: Parameter not parsed from rule.yaml
**Required**: Parse minimum_break_gap_minutes for each shift
**Impact**: BLOCKING - Cannot implement gap detection without threshold

### Issue 5: Night Shift Date Attribution Wrong ❌
**Location**: `processor.py:146`
**Current**: Uses swipe calendar_date
**Required**: Use shift START date (Day_N for night shift starting Day_N)
**Impact**: CRITICAL - Date column incorrect for night shifts

---

## Gap Analysis: MEDIUM Priority Issues

### Issue 6: Midpoint Fallback Logic Incomplete ⚠
**Location**: `processor.py:228-264`
**Current**: Only handles "swipes spanning midpoint" case
**Required**: Handle 4 cases (spanning, all before with/without gap, all after with/without gap, single swipe)
**Impact**: MEDIUM - Edge cases produce incorrect results

### Issue 7: Boundary Precision Unclear ⚠
**Location**: `processor.py:266-282` (_time_in_range)
**Current**: Uses >= and <= (inclusive both ends)
**Required**: Clarify if 06:35:00 exactly belongs to night shift or excluded
**Impact**: LOW - Minor edge case, needs user confirmation

---

## Research Findings Summary

Spawned 3 researcher agents in parallel to investigate best practices:

### Researcher 1: Shift-Instance Grouping
**Key Finding**: Industry best practice = group by shift START timestamp, track activity windows across calendar days.

**Algorithm**:
1. Detect shift starts (First In swipes in check_in_search_ranges)
2. Define activity windows (handle midnight crossing for C_shift)
3. Assign all swipes within window to shift instance
4. Output with shift_date = date of First In

**Report**: `/home/silver/project_clean/plans/research/researcher-1-findings.md`

### Researcher 2: Gap-Based Break Detection
**Key Finding**: Two-tier algorithm optimal - gap detection (objective) as Priority 1, midpoint logic (heuristic) as Priority 2.

**Algorithm**:
1. Try gap detection first (linear scan for gap >= minimum)
2. If no qualifying gap, fall back to complex midpoint branching
3. Handle bursts as atomic units (gap from burst_end to next burst_start)

**Report**: `/home/silver/project_clean/plans/research/researcher-2-findings.md`

### Researcher 3: Burst Detection & Representation
**Key Finding**: Must preserve both burst_start AND burst_end - different contexts require different timestamps.

**Usage**:
- Check-in: burst_start (earliest)
- Check-out: burst_end (latest)
- Break Out: burst_end (latest before gap)
- Break In: burst_start (earliest after gap)
- Gap calculation: current.burst_end to next.burst_start

**Report**: `/home/silver/project_clean/plans/research/researcher-3-findings.md`

---

## Implementation Plan Overview

### Phase 1: Config Updates (2h)
- Add minimum_break_gap_minutes to ShiftConfig dataclass
- Parse parameter from rule.yaml

### Phase 2: Burst Detection Fix (2h)
- Preserve burst_end column (don't discard)
- Verify burst_start, burst_end, timestamp all present

### Phase 3: Shift-Instance Grouping (4h) - CRITICAL
- Complete rewrite of _classify_shifts → _detect_shift_instances
- Implement _get_activity_window (handle midnight crossing)
- Implement _collect_shift_swipes (assign swipes to instances)
- Update _extract_attendance_events grouping

### Phase 4: Gap-Based Break Detection (3h) - CRITICAL
- Implement _detect_break_by_gap (Priority 1)
- Implement _detect_break_by_midpoint (Priority 2 fallback)
- Rewrite _detect_breaks to use two-tier algorithm

### Phase 5: First In / Last Out Fixes (1h)
- Update _find_first_in to use burst_start explicitly
- Update _find_last_out to use burst_end explicitly

### Phase 6: Extract Events Update (1h)
- Update grouping from (Name, calendar_date, shift) to shift_instance_id
- Handle time_only column correctly for bursts

### Phase 7: Testing & Validation (2h)
- Create test_processor_v9.py with all 6 rule.yaml scenarios
- Integration test with real data
- Performance benchmark

**Total**: 15 hours, 2-3 days calendar time

---

## Files Affected

### Modified (2 files)
1. **config.py** - Add minimum_break_gap_minutes parameter
2. **processor.py** - Major rewrite of shift classification and break detection

### Created (1 file)
1. **tests/test_processor_v9.py** - Comprehensive scenario tests

### No deletions required

---

## Test Strategy

### Unit Tests (6 scenarios from rule.yaml)
1. Scenario 1: Normal day shift with standard breaks
2. Scenario 2: Burst with breaks (tests burst_end usage)
3. Scenario 3: Late break after midpoint (tests gap detection)
4. Scenario 4: Night shift crossing midnight (tests shift-instance grouping)
5. Scenario 5: Single swipe before midpoint
6. Scenario 6: No break taken

### Integration Tests
- Full pipeline with /home/silver/output1.xlsx
- Validate night shift Date column = shift START date
- Verify Break Out/In times match gap detection logic

### Performance Tests
- Benchmark 90-row dataset (target: <0.5s)
- Benchmark 1,000-row dataset (target: <2s)
- Ensure no significant regression

---

## Risk Assessment

### HIGH RISK
- **Shift instance detection complexity** - Midnight crossing logic error-prone
  - Mitigation: Comprehensive unit tests, manual validation with scenario_4

- **Breaking existing functionality** - Complete rewrite may cause regressions
  - Mitigation: Keep existing tests passing, extensive manual testing

### MEDIUM RISK
- **Performance degradation** - Shift instance detection may slow processing
  - Mitigation: Optimize grouping logic, benchmark with large datasets

### LOW RISK
- **Edge cases in real data** - Unforeseen scenarios beyond test coverage
  - Mitigation: Permissive error handling, extensive logging, user warnings

---

## Acceptance Criteria

### Must Pass ✓
1. All 6 rule.yaml scenarios produce expected output
2. Night shift (scenario_4) outputs Date = shift START date (2025-11-03, not 2025-11-04)
3. Burst + break (scenario_2) uses burst_end (10:01) for Break Out
4. Gap detection (scenario_3) detects 9-min gap correctly
5. All unit tests pass (target: 100%)
6. Integration test with /home/silver/output1.xlsx succeeds

### Should Pass ✓
1. Performance remains <0.5s for 90-row dataset
2. No regressions in existing test coverage
3. Code follows existing patterns and style conventions

---

## Unresolved Questions

1. **Boundary precision**: Swipe at exactly 06:35:00 - inclusive or exclusive for night shift?
   - Recommendation: Inclusive (<=) based on validation_rules line 230
   - Needs user confirmation

2. **Multiple breaks per shift**: rule.yaml says "NOT implemented", but what if data shows multiple gaps?
   - Recommendation: Use first qualifying gap only, ignore subsequent
   - Document limitation

3. **Orphan swipes**: Swipes outside ALL check-in ranges - completely ignored or logged?
   - Recommendation: Silently ignore (don't create shift instances)
   - Could add logging for transparency

4. **Burst spanning midnight**: Burst from 23:59 to 00:01 - how to represent?
   - Recommendation: Single burst with burst_start (Day_N), burst_end (Day_N+1)
   - Assign to shift based on burst_start time

5. **Gap calculation at midnight**: Gap from 23:58 to 00:03 - correct handling?
   - Recommendation: Use datetime objects, gaps naturally positive
   - No special case needed

---

## Recommendations

### Immediate Actions (Priority: CRITICAL)
1. Review implementation plan at `/home/silver/project_clean/plans/251104-fix-code-per-ruleset.md`
2. Clarify unresolved questions with user if needed
3. Begin Phase 1 (Config Updates) - quick win, enables later phases
4. Implement sequentially following dependencies in plan

### Before Starting Implementation
1. Backup current working code
2. Create feature branch for v9.0 compliance
3. Set up test fixtures for all 6 scenarios
4. Review research findings to understand algorithms

### During Implementation
1. Test each phase before proceeding to next
2. Keep existing tests passing (no regressions)
3. Add logging for debugging shift instance detection
4. Document complex logic with comments

### Post-Implementation
1. Run full test suite (unit + integration)
2. Manual validation with /home/silver/output1.xlsx
3. Performance benchmark and comparison
4. Update documentation (README, tech docs)
5. Code review before deployment

---

## Conclusion

Current codebase violates 5 critical requirements from rule.yaml v9.0:
1. ❌ Shift-instance grouping not implemented (groups by calendar_date)
2. ❌ Gap-based break detection missing (only midpoint logic)
3. ❌ Burst representation loses burst_end timestamps
4. ❌ minimum_break_gap_minutes parameter not parsed
5. ❌ Night shift date attribution incorrect

**Severity**: CRITICAL - Code produces incorrect output for night shifts and break detection.

**Solution**: Complete rewrite of shift classification and break detection logic, plus config and burst handling updates. Well-defined requirements in rule.yaml with comprehensive test scenarios provide high confidence in implementation feasibility.

**Estimated effort**: 15 hours over 2-3 days. Recommended approach: sequential implementation following phase dependencies, test each phase before proceeding.

**Next steps**: Review plan, clarify unresolved questions, begin Phase 1 (Config Updates).

---

## Appendix: File Paths

### Implementation Plan
`/home/silver/project_clean/plans/251104-fix-code-per-ruleset.md`

### Research Reports
- `/home/silver/project_clean/plans/research/researcher-1-findings.md` (Shift-instance grouping)
- `/home/silver/project_clean/plans/research/researcher-2-findings.md` (Gap-based break detection)
- `/home/silver/project_clean/plans/research/researcher-3-findings.md` (Burst detection)

### Code Files to Modify
- `/home/silver/project_clean/config.py`
- `/home/silver/project_clean/processor.py`

### Test Files to Create
- `/home/silver/project_clean/tests/test_processor_v9.py`

### Rule Reference
- `/home/silver/rule.yaml` (v9.0)
