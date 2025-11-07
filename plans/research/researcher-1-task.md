# Researcher 1 Task: Shift-Instance Grouping & Night Shift Handling

## Objective
Research best practices for shift-instance grouping in attendance systems, specifically handling night shifts that cross midnight boundaries.

## Key Questions
1. How should night shifts crossing midnight be represented in attendance records?
2. What's the industry standard for "shift date" attribution when shifts span calendar days?
3. How to efficiently group all swipes belonging to one shift instance (including next-day swipes)?
4. What are edge cases in shift window boundaries (e.g., swipe at exactly 06:35)?

## Requirements from rule.yaml
- Night shift starts 21:30-22:35 on Day N
- Includes ALL swipes until 06:35 on Day N+1
- Output must show Date = Day N (shift START date)
- One shift = one complete record (no fragmentation)

## Deliverable
Write a research report covering:
- Recommended algorithm for shift-instance grouping
- Data structure for tracking shift windows across midnight
- Edge case handling strategies
- Pseudocode for grouping logic
