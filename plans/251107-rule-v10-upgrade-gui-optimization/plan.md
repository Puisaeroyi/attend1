# Implementation Plan: Rule v10.0 Upgrade & GUI Optimization

**Date:** 2025-11-07
**Project:** Attendance Data Processor
**Version:** Target v3.1.0
**Priority:** HIGH

---

## Overview

Two-phase upgrade addressing rule logic enhancement + performance optimization.

**Phase 1:** Rule v9.0 → v10.0 upgrade (terminology, late marking, output columns)
**Phase 2:** GUI performance optimization (threading, responsiveness, UX)

---

## Phases Summary

| Phase | Description | Status | Progress |
|-------|-------------|--------|----------|
| 01 | Research & Analysis | ⏸ Pending | 0% |
| 02 | Rule v10.0 Config Upgrade | ⏸ Pending | 0% |
| 03 | Rule v10.0 Processing Logic | ⏸ Pending | 0% |
| 04 | Rule v10.0 Output Columns | ⏸ Pending | 0% |
| 05 | Rule v10.0 Testing | ⏸ Pending | 0% |
| 06 | GUI Performance Analysis | ⏸ Pending | 0% |
| 07 | GUI Threading Optimization | ⏸ Pending | 0% |
| 08 | GUI Responsiveness Enhancement | ⏸ Pending | 0% |
| 09 | Integration Testing | ⏸ Pending | 0% |
| 10 | Documentation Update | ⏸ Pending | 0% |

---

## Phase Details

Each phase documented in separate file:

- [`phase-01-research-analysis.md`](./phase-01-research-analysis.md) - Research rule differences, GUI bottlenecks
- [`phase-02-rule-config-upgrade.md`](./phase-02-rule-config-upgrade.md) - Update rule.yaml, config.py
- [`phase-03-rule-processing-logic.md`](./phase-03-rule-processing-logic.md) - Implement late marking, grace period logic
- [`phase-04-rule-output-columns.md`](./phase-04-rule-output-columns.md) - Add status columns to output
- [`phase-05-rule-testing.md`](./phase-05-rule-testing.md) - Test scenarios, validate logic
- [`phase-06-gui-performance-analysis.md`](./phase-06-gui-performance-analysis.md) - Identify bottlenecks, profiling
- [`phase-07-gui-threading-optimization.md`](./phase-07-gui-threading-optimization.md) - Optimize thread management
- [`phase-08-gui-responsiveness.md`](./phase-08-gui-responsiveness.md) - Progress bars, async updates
- [`phase-09-integration-testing.md`](./phase-09-integration-testing.md) - End-to-end validation
- [`phase-10-documentation.md`](./phase-10-documentation.md) - Update docs, changelog

---

## Key Changes Summary

### Task 1: Rule v10.0 Upgrade

**Terminology Changes:**
- "First In" → "Check-in"
- "Break Out" → "Break Time Out"
- "Break In" → "Break Time In"
- "Last Out" → "Check Out Record"

**Late Marking System (NEW):**
- Grace period = hard cutoff (not advisory)
- Check-in status: On Time (≤ shift_start + 04:59), Late (≥ shift_start + 05:00)
- Break Time In status: On Time (≤ break_end + 04:59), Late (≥ break_end + 05:00)

**Output Columns (NEW):**
- Added "Check-in Status" column
- Added "Break Time In Status" column

**Break Search Range (C Shift):**
- Changed from "01:50-02:45" → "01:50-02:50"

### Task 2: GUI Performance Optimization

**Issues Addressed:**
- GUI freezing during processing
- Slow response during file operations
- Thread safety concerns
- Delayed progress feedback

**Solutions:**
- Async file I/O with queue-based updates
- Progress indicators (real-time row processing)
- Thread pool for parallel operations
- UI debouncing for log updates

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 01 | 2 hours | None |
| Phase 02 | 3 hours | Phase 01 |
| Phase 03 | 6 hours | Phase 02 |
| Phase 04 | 4 hours | Phase 03 |
| Phase 05 | 8 hours | Phase 04 |
| Phase 06 | 3 hours | None (parallel) |
| Phase 07 | 6 hours | Phase 06 |
| Phase 08 | 5 hours | Phase 07 |
| Phase 09 | 6 hours | Phase 05, 08 |
| Phase 10 | 3 hours | Phase 09 |

**Total:** ~46 hours (~6 working days)

---

## Success Criteria

### Rule v10.0
- ✅ All terminology updated (code, config, output)
- ✅ Late marking logic implemented correctly
- ✅ Grace period cutoffs accurate (04:59 vs 05:00)
- ✅ Status columns output correctly
- ✅ C shift break range extended (01:50-02:50)
- ✅ All existing tests pass
- ✅ New tests validate late marking logic

### GUI Optimization
- ✅ No GUI freezing during processing
- ✅ Responsive UI (<100ms for user actions)
- ✅ Progress feedback updates smoothly
- ✅ Thread-safe operations (no race conditions)
- ✅ Large files (10k+ rows) process without lag
- ✅ CPU usage optimized (<50% single core)

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing logic | HIGH | MEDIUM | Comprehensive test suite, regression tests |
| Grace period off-by-one errors | HIGH | MEDIUM | Boundary testing (04:59, 05:00, 05:01) |
| Thread deadlocks | MEDIUM | LOW | Thorough code review, lock analysis |
| Performance regression | MEDIUM | LOW | Benchmarking before/after |
| UI responsiveness unchanged | MEDIUM | MEDIUM | Profiling, incremental testing |

---

## Rollback Strategy

**If Critical Issues Found:**
1. Revert to rule.yaml v9.0 (keep backup)
2. Disable new status columns (backward compatible)
3. Restore original GUI threading
4. Document issues for future iteration

**Version Control:**
- Branch: `feat/rule-v10-gui-optimization`
- Tag before merge: `v3.0.0-stable`
- Tag after merge: `v3.1.0`

---

## Next Steps

1. Review plan with stakeholders
2. Begin Phase 01 (Research & Analysis)
3. Create feature branch
4. Implement phases sequentially
5. Continuous testing throughout

---

## Notes

- **Sacrifice grammar for concision** (per project standards)
- **YAGNI, KISS, DRY principles** apply
- **No speculative features** beyond requirements
- **Comprehensive testing** before merge
- **Documentation updates** mandatory

---

## Unresolved Questions

1. **Rule v10.0 source:** Where is rule1.yaml (v10.0)? Using requirements from user.
2. **Late marking edge cases:** What if check-in at exactly 06:05:00? (Assuming "Late" based on ≥ 05:00)
3. **Break Time In status:** Apply to all shifts or only A/B/C? (Assuming all shifts)
4. **Backward compatibility:** Should old outputs still work? (Assuming yes, add columns)
5. **Performance targets:** What's acceptable processing time for 10k rows? (Assuming <30s)

---

**Plan Status:** DRAFT - Awaiting approval
**Created:** 2025-11-07
**Author:** Planner Agent
