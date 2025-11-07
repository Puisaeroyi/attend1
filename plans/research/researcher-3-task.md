# Researcher 3 Task: Burst Detection & Representation

## Objective
Research best practices for detecting and representing burst events (multiple rapid swipes) in biometric attendance systems.

## Key Questions
1. How to efficiently group swipes within <=2min threshold?
2. Should bursts be represented by start time, end time, or both?
3. How should bursts be used in subsequent logic (check-in, break detection, check-out)?
4. What are edge cases (single swipe, overlapping bursts, midnight-spanning bursts)?

## Requirements from rule.yaml
- Burst definition: swipes within <=2min grouped as single burst
- Must apply BEFORE all other logic
- Representation: both burst_start (earliest) AND burst_end (latest) needed
- Example: 09:55-10:01 burst → Break Out uses 10:01 (burst_end)
- Bursts treated as atomic units in gap detection

## Deliverable
Write a research report covering:
- Recommended burst detection algorithm
- Data structure for representing bursts
- How to use burst_start vs burst_end in different contexts
- Edge case handling strategies
- Pseudocode for burst grouping logic
