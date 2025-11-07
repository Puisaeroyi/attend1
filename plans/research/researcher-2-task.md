# Researcher 2 Task: Gap-Based Break Detection Algorithms

## Objective
Research best practices for detecting breaks in attendance data using time gaps between swipes, with midpoint logic as fallback.

## Key Questions
1. How to efficiently detect time gaps >= threshold between consecutive swipes?
2. What's the priority order: gap detection vs midpoint logic?
3. How to handle edge cases (all swipes before midpoint, all after, spanning midpoint)?
4. What about bursts - should gaps be calculated between bursts or individual swipes?

## Requirements from rule.yaml
- Priority 1: Gap detection (gap >= minimum_break_gap between swipes/bursts)
- Priority 2: Midpoint fallback logic (complex branching based on swipe distribution)
- Burst handling: gaps calculated between bursts as atomic units
- Single swipe logic: use midpoint checkpoint to determine Break Out vs Break In

## Deliverable
Write a research report covering:
- Recommended two-tier algorithm (gap detection + midpoint fallback)
- Efficient implementation approach for gap calculation
- Decision tree for all edge cases
- Pseudocode for break detection logic
