"""Comprehensive scenario tests from rule.yaml lines 236-319"""

import pytest
import pandas as pd
from datetime import datetime
from config import RuleConfig
from processor import AttendanceProcessor


@pytest.fixture
def config():
    """Load configuration from rule.yaml"""
    return RuleConfig.load_from_yaml('rule.yaml')


@pytest.fixture
def processor(config):
    """Create processor instance"""
    return AttendanceProcessor(config)


def test_scenario_1_normal_day_shift(processor):
    """Scenario 1: Normal day shift with proper break

    Input: 05:55, 09:55, 10:25, 14:05
    Expected:
    - Shift: A (Morning)
    - First In: 05:55
    - Break Out: 09:55
    - Break In: 10:25
    - Last Out: 14:05
    """
    df = pd.DataFrame({
        'ID': ['1'] * 4,
        'Name': ['Silver_Bui'] * 4,
        'Date': ['2025-11-04'] * 4,
        'Time': ['05:55:00', '09:55:00', '10:25:00', '14:05:00'],
        'Status': ['Success'] * 4
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)
    df = processor._detect_shift_instances(df)
    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    assert row['Shift'] == 'Morning'
    assert row['Check-in'] == '05:55:00'
    assert row['Break Time Out'] == '09:55:00'
    assert row['Break Time In'] == '10:25:00'
    assert row['Check Out Record'] == '14:05:00'
    print("✅ Scenario 1 PASSED: Normal day shift")


def test_scenario_2_burst_with_breaks(processor):
    """Scenario 2: Burst with breaks

    Input: 05:55, [09:55-10:01 burst], 10:25, 14:05
    Expected:
    - Break Out: 10:01 (end of burst)
    - Break In: 10:25
    """
    df = pd.DataFrame({
        'ID': ['1'] * 9,
        'Name': ['Silver_Bui'] * 9,
        'Date': ['2025-11-04'] * 9,
        'Time': [
            '05:55:00',
            '09:55:00', '09:56:00', '09:57:00', '09:58:00', '09:59:00', '10:01:00',  # Burst
            '10:25:00',
            '14:05:00'
        ],
        'Status': ['Success'] * 9
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)

    # Verify burst consolidation (6 burst swipes + 3 regular = 4 events)
    assert len(df) == 4

    df = processor._detect_shift_instances(df)
    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    assert row['Shift'] == 'Morning'
    assert row['Check-in'] == '05:55:00'
    assert row['Break Time Out'] == '10:01:00'  # End of burst
    assert row['Break Time In'] == '10:25:00'
    assert row['Check Out Record'] == '14:05:00'
    print("✅ Scenario 2 PASSED: Burst with breaks")


def test_scenario_3_late_break_after_midpoint(processor):
    """Scenario 3: Late break after midpoint (gap-based detection)

    Input: 06:00, 10:20, 10:29, 14:00
    Expected: 9-minute gap detected
    - Break Out: 10:20 (gap-based)
    - Break In: 10:29 (gap-based)
    """
    df = pd.DataFrame({
        'ID': ['1'] * 4,
        'Name': ['Silver_Bui'] * 4,
        'Date': ['2025-11-04'] * 4,
        'Time': ['06:00:00', '10:20:00', '10:29:00', '14:00:00'],
        'Status': ['Success'] * 4
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)
    df = processor._detect_shift_instances(df)
    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    assert row['Shift'] == 'Morning'
    assert row['Check-in'] == '06:00:00'
    assert row['Break Time Out'] == '10:20:00'  # Gap-based detection
    assert row['Break Time In'] == '10:29:00'   # Gap-based detection
    assert row['Check Out Record'] == '14:00:00'
    print("✅ Scenario 3 PASSED: Late break after midpoint (gap-based)")


def test_scenario_4_night_shift_crossing_midnight(processor):
    """Scenario 4: Night shift crossing midnight

    Input:
    - 2025-11-03 21:55:28
    - 2025-11-04 02:00:35 (next day)
    - 2025-11-04 02:44:51 (next day)
    - 2025-11-04 06:03:14 (next day)

    Expected:
    - Date: 2025-11-03 (shift START date)
    - All timestamps from next calendar day included
    - Single complete record (no fragmentation)
    """
    df = pd.DataFrame({
        'ID': ['1'] * 4,
        'Name': ['Capone'] * 4,
        'Date': ['2025-11-03', '2025-11-04', '2025-11-04', '2025-11-04'],
        'Time': ['21:55:28', '02:00:35', '02:44:51', '06:03:14'],
        'Status': ['Success'] * 4
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)
    df = processor._detect_shift_instances(df)

    # CRITICAL: Verify all swipes assigned to same shift instance
    unique_instances = df['shift_instance_id'].nunique()
    assert unique_instances == 1, f"Night shift fragmented into {unique_instances} instances!"

    # Verify all assigned to shift C
    assert all(df['shift_code'] == 'C')

    # Verify shift date is Nov 3 (not Nov 4)
    assert all(df['shift_date'] == pd.Timestamp('2025-11-03').date())

    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    # Date should be shift START date (Nov 3), not swipe calendar date
    assert str(row['Date'])[:10] == '2025-11-03'
    assert row['Shift'] == 'Night'
    assert row['ID'] == 'TPL0002'  # Capone
    assert row['Name'] == 'Pham Tan Phat'
    assert row['Check-in'] == '21:55:28'
    assert row['Break Time Out'] == '02:00:35'  # Next calendar day
    assert row['Break Time In'] == '02:44:51'   # Next calendar day
    assert row['Check Out Record'] == '06:03:14'   # Next calendar day
    print("✅ Scenario 4 PASSED: Night shift crossing midnight (single record)")


def test_scenario_5_single_swipe_before_midpoint(processor):
    """Scenario 5: Single swipe before midpoint

    Input: 06:00, 10:08, 14:00
    Expected:
    - Break Out: 10:08 (before 10:15)
    - Break In: blank
    """
    df = pd.DataFrame({
        'ID': ['1'] * 3,
        'Name': ['Silver_Bui'] * 3,
        'Date': ['2025-11-04'] * 3,
        'Time': ['06:00:00', '10:08:00', '14:00:00'],
        'Status': ['Success'] * 3
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)
    df = processor._detect_shift_instances(df)
    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    assert row['Shift'] == 'Morning'
    assert row['Check-in'] == '06:00:00'
    assert row['Break Time Out'] == '10:08:00'
    assert row['Break Time In'] == ''  # Blank
    assert row['Check Out Record'] == '14:00:00'
    print("✅ Scenario 5 PASSED: Single swipe before midpoint")


def test_scenario_6_no_break_taken(processor):
    """Scenario 6: No break taken

    Input: 06:00, 14:00 (no swipes in break window)
    Expected:
    - Break Out: blank
    - Break In: blank
    """
    df = pd.DataFrame({
        'ID': ['1'] * 2,
        'Name': ['Silver_Bui'] * 2,
        'Date': ['2025-11-04'] * 2,
        'Time': ['06:00:00', '14:00:00'],
        'Status': ['Success'] * 2
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)
    df = processor._detect_shift_instances(df)
    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    assert row['Shift'] == 'Morning'
    assert row['Check-in'] == '06:00:00'
    assert row['Break Time Out'] == ''  # Blank
    assert row['Break Time In'] == ''   # Blank
    assert row['Check Out Record'] == '14:00:00'
    print("✅ Scenario 6 PASSED: No break taken")


def test_edge_case_overlapping_windows(processor):
    """Edge case: Overlapping check-in/check-out windows

    B shift check-out: 21:30-22:35
    C shift check-in: 21:30-22:35

    Verify B shift check-out has priority over C shift check-in
    """
    # B shift with swipe at 22:00 (overlaps with C check-in window)
    df = pd.DataFrame({
        'ID': ['1'] * 2,
        'Name': ['Silver_Bui'] * 2,
        'Date': ['2025-11-04'] * 2,
        'Time': ['14:00:00', '22:00:00'],  # B shift
        'Status': ['Success'] * 2
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)
    df = processor._detect_shift_instances(df)

    # Verify only ONE shift instance (B shift)
    assert df['shift_instance_id'].nunique() == 1
    assert all(df['shift_code'] == 'B')

    result = processor._extract_attendance_events(df)
    assert len(result) == 1
    assert result.iloc[0]['Shift'] == 'Afternoon'
    assert result.iloc[0]['Check Out Record'] == '22:00:00'
    print("✅ Edge case PASSED: Overlapping windows handled correctly")


def test_edge_case_multiple_breaks(processor):
    """Edge case: Multiple gaps (should use gap closest to cutoff)

    Input: 06:00, 09:55, 10:05, 10:15, 10:25, 14:00
    Gaps:
    - 09:55 to 10:05 = 10 minutes (first qualifying gap) - Break In 10:05 is 1794 sec from cutoff 10:34:59
    - 10:15 to 10:25 = 10 minutes (second gap) - Break In 10:25 is 599 sec from cutoff 10:34:59

    Expected: Use second gap (10:15 -> 10:25) because Break Time In is closer to cutoff
    """
    df = pd.DataFrame({
        'ID': ['1'] * 6,
        'Name': ['Silver_Bui'] * 6,
        'Date': ['2025-11-04'] * 6,
        'Time': ['06:00:00', '09:55:00', '10:05:00', '10:15:00', '10:25:00', '14:00:00'],
        'Status': ['Success'] * 6
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)
    df = processor._detect_shift_instances(df)
    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    # With independent selection (v10.0):
    # Break Time Out: 09:55 closest to checkpoint 10:00:00 (300 sec, same as 10:05 but first)
    # Break Time In: 10:25 closest to cutoff 10:34:59 (599 sec)
    assert row['Break Time Out'] == '09:55:00'
    assert row['Break Time In'] == '10:25:00'
    print("✅ Edge case PASSED: Multiple breaks (independent selection used)")


def test_edge_case_burst_spanning_break(processor):
    """Edge case: Burst spanning break period

    Input: 06:00, [10:00-10:14 burst], 14:00
    Burst within break window, all before midpoint (10:15)

    Expected: Use burst_end for Break Out, blank for Break In
    """
    df = pd.DataFrame({
        'ID': ['1'] * 17,
        'Name': ['Silver_Bui'] * 17,
        'Date': ['2025-11-04'] * 17,
        'Time': ['06:00:00'] + [f'10:{i:02d}:00' for i in range(0, 15)] + ['14:00:00'],
        'Status': ['Success'] * 17
    })

    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.sort_values(['Name', 'timestamp']).reset_index(drop=True)

    # Process
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)

    # Verify burst consolidation
    assert len(df) == 3  # First In + Burst + Last Out

    df = processor._detect_shift_instances(df)
    result = processor._extract_attendance_events(df)

    assert len(result) == 1
    row = result.iloc[0]

    # Break Out should be burst_end (10:14), Break In blank (all before midpoint 10:15)
    assert row['Break Time Out'] == '10:14:00'
    assert row['Break Time In'] == ''
    print("✅ Edge case PASSED: Burst spanning break period")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
