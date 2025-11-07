"""Tests for core processing logic"""

import pytest
import pandas as pd
from datetime import datetime, time
from config import RuleConfig, ShiftConfig
from processor import AttendanceProcessor


@pytest.fixture
def config():
    """Load configuration from rule.yaml"""
    return RuleConfig.load_from_yaml('rule.yaml')


@pytest.fixture
def processor(config):
    """Create processor instance"""
    return AttendanceProcessor(config)


def test_filter_valid_status(processor):
    """Test filtering by status"""
    df = pd.DataFrame({
        'Status': ['Success', 'Success', 'Failure', 'Success'],
        'Name': ['Silver_Bui', 'Capone', 'Minh', 'Trieu'],
        'Date': ['2025-11-02'] * 4,
        'Time': ['06:00:00', '07:00:00', '08:00:00', '09:00:00'],
        'timestamp': pd.date_range('2025-11-02 06:00', periods=4, freq='1h')
    })

    result = processor._filter_valid_status(df)

    assert len(result) == 3
    assert all(result['Status'] == 'Success')


def test_filter_valid_users(processor):
    """Test filtering by valid users"""
    df = pd.DataFrame({
        'Name': ['Silver_Bui', 'Unknown', 'Capone', 'Invalid'],
        'Date': ['2025-11-02'] * 4,
        'Time': ['06:00:00', '07:00:00', '08:00:00', '09:00:00'],
        'timestamp': pd.date_range('2025-11-02 06:00', periods=4, freq='1h')
    })

    result = processor._filter_valid_users(df)

    assert len(result) == 2
    assert 'Silver_Bui' in result['Name'].values
    assert 'Capone' in result['Name'].values
    assert 'Unknown' not in result['Name'].values


def test_burst_detection(processor):
    """Test burst detection consolidates swipes ≤2min apart"""
    # Create swipes: 3 within 2min (burst), 1 separate
    df = pd.DataFrame({
        'Name': ['Silver_Bui', 'Silver_Bui', 'Silver_Bui', 'Silver_Bui'],
        'Date': ['2025-11-02'] * 4,
        'Time': ['06:00:00', '06:00:30', '06:01:45', '06:10:00'],
        'Status': ['Success'] * 4
    })
    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    # Add output mappings by filtering through _filter_valid_users first
    df = processor._filter_valid_users(df)

    result = processor._detect_bursts(df)

    # Should have 2 events: 1 burst + 1 separate
    assert len(result) == 2

    # First event should be the burst start (earliest)
    assert result.iloc[0]['burst_start'] == datetime(2025, 11, 2, 6, 0, 0)

    # Second event should be the separate swipe
    assert result.iloc[1]['burst_start'] == datetime(2025, 11, 2, 6, 10, 0)


def test_shift_classification(processor):
    """Test shift classification based on first timestamp"""
    df = pd.DataFrame({
        'Name': ['Silver_Bui', 'Silver_Bui', 'Capone', 'Minh'],
        'Date': ['2025-11-02'] * 4,
        'Time': ['06:00:00', '10:00:00', '14:00:00', '22:00:00'],
        'Status': ['Success'] * 4
    })
    df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    # Add output mappings
    df = processor._filter_valid_users(df)

    # Process bursts first
    df = processor._detect_bursts(df)

    result = processor._detect_shift_instances(df)

    # All rows for Silver_Bui on same day should have same shift (A)
    silver_rows = result[result['Name'] == 'Silver_Bui']
    assert all(silver_rows['shift_code'] == 'A')

    # Capone should be shift B
    capone_rows = result[result['Name'] == 'Capone']
    assert all(capone_rows['shift_code'] == 'B')

    # Minh should be shift C
    minh_rows = result[result['Name'] == 'Minh']
    assert all(minh_rows['shift_code'] == 'C')


def test_find_first_in(processor, config):
    """Test finding first check-in within window"""
    shift_a = config.shifts['A']

    # Swipes: before window, in window, in window, after window
    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 2, 5, 0, 0),   # Too early
            datetime(2025, 11, 2, 6, 0, 0),   # First in window
            datetime(2025, 11, 2, 6, 30, 0),  # Also in window
            datetime(2025, 11, 2, 7, 0, 0)    # Too late
        ]
    })
    df['time_start'] = df['burst_start'].dt.time

    result, _ = processor._find_check_in(df, shift_a)

    # Should return earliest in window (06:00:00)
    assert result == "06:00:00"


def test_find_first_in_no_match(processor, config):
    """Test finding first check-in when none in window"""
    shift_a = config.shifts['A']

    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 2, 5, 0, 0),   # Too early
            datetime(2025, 11, 2, 7, 0, 0)    # Too late
        ]
    })
    df['time_start'] = df['burst_start'].dt.time

    result, _ = processor._find_check_in(df, shift_a)

    # Should return empty string
    assert result == ""


def test_detect_breaks_normal(processor, config):
    """Test break detection with 2 swipes (before/after midpoint)"""
    shift_a = config.shifts['A']  # Midpoint: 10:15

    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 2, 9, 55, 0),   # Before midpoint
            datetime(2025, 11, 2, 10, 30, 0)   # After midpoint
        ],
        'burst_end': [
            datetime(2025, 11, 2, 9, 55, 0),   # Before midpoint
            datetime(2025, 11, 2, 10, 30, 0)   # After midpoint
        ]
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    break_out, break_in, _ = processor._detect_breaks(df, shift_a)

    assert break_out == "09:55:00"
    assert break_in == "10:30:00"


def test_detect_breaks_single_before_midpoint(processor, config):
    """Test break detection with single swipe before midpoint"""
    shift_a = config.shifts['A']  # Midpoint: 10:15

    df = pd.DataFrame({
        'burst_start': [datetime(2025, 11, 2, 10, 8, 0)],  # Before midpoint
        'burst_end': [datetime(2025, 11, 2, 10, 8, 0)]     # Before midpoint
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    break_out, break_in, _ = processor._detect_breaks(df, shift_a)

    assert break_out == "10:08:00"
    assert break_in == ""  # Empty


def test_detect_breaks_single_after_midpoint(processor, config):
    """Test break detection with single swipe after midpoint"""
    shift_a = config.shifts['A']  # Midpoint: 10:15

    df = pd.DataFrame({
        'burst_start': [datetime(2025, 11, 2, 10, 20, 0)],  # After midpoint
        'burst_end': [datetime(2025, 11, 2, 10, 20, 0)]     # After midpoint
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    break_out, break_in, _ = processor._detect_breaks(df, shift_a)

    assert break_out == ""  # Empty
    assert break_in == "10:20:00"


def test_detect_breaks_no_swipes(processor, config):
    """Test break detection with no swipes in window"""
    shift_a = config.shifts['A']

    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 2, 6, 0, 0),    # Too early for break window
            datetime(2025, 11, 2, 14, 0, 0)    # Too late for break window
        ],
        'burst_end': [
            datetime(2025, 11, 2, 6, 0, 0),    # Too early for break window
            datetime(2025, 11, 2, 14, 0, 0)    # Too late for break window
        ]
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    break_out, break_in, _ = processor._detect_breaks(df, shift_a)

    assert break_out == ""
    assert break_in == ""


def test_detect_breaks_multiple_swipes(processor, config):
    """Test break detection with multiple swipes each side of midpoint"""
    shift_a = config.shifts['A']  # Midpoint: 10:15, cutoff: 10:34:59

    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 2, 9, 50, 0),   # Before
            datetime(2025, 11, 2, 9, 55, 0),   # Before (latest before midpoint)
            datetime(2025, 11, 2, 10, 25, 0),  # After (earliest after midpoint)
            datetime(2025, 11, 2, 10, 30, 0)   # After
        ],
        'burst_end': [
            datetime(2025, 11, 2, 9, 50, 0),   # Before
            datetime(2025, 11, 2, 9, 55, 0),   # Before (latest before midpoint)
            datetime(2025, 11, 2, 10, 25, 0),  # After (earliest after midpoint)
            datetime(2025, 11, 2, 10, 30, 0)   # After
        ]
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    break_out, break_in, _ = processor._detect_breaks(df, shift_a)

    # With independent selection (v10.0):
    # Three qualifying gaps: 09:50-09:55 (5min), 09:55-10:25 (30min), 10:25-10:30 (5min)
    # Break Time Out: 09:55 is closest to checkpoint 10:00:00 (300 sec vs 1500 sec)
    # Break Time In: 10:30 is closest to cutoff 10:34:59 (299 sec vs 599 sec)
    assert break_out == "09:55:00", f"Expected Break Time Out: 09:55:00, Got: {break_out}"
    assert break_in == "10:30:00", f"Expected Break Time In: 10:30:00, Got: {break_in}"


def test_time_in_range_normal(processor):
    """Test time range checking for normal ranges"""
    times = pd.Series([
        time(9, 0, 0),
        time(9, 50, 0),
        time(10, 0, 0),
        time(10, 30, 0),
        time(11, 0, 0)
    ])

    # Range: 09:50 to 10:35
    result = processor._time_in_range(times, time(9, 50, 0), time(10, 35, 0))

    expected = [False, True, True, True, False]
    assert list(result) == expected


def test_time_in_range_midnight_spanning(processor):
    """Test time range checking for midnight-spanning ranges"""
    times = pd.Series([
        time(20, 0, 0),
        time(22, 0, 0),
        time(23, 30, 0),
        time(1, 0, 0),
        time(6, 0, 0),
        time(8, 0, 0)
    ])

    # Range: 21:30 to 06:35 (night shift)
    result = processor._time_in_range(times, time(21, 30, 0), time(6, 35, 0))

    expected = [False, True, True, True, True, False]
    assert list(result) == expected


def test_detect_breaks_cutoff_priority_selection(processor, config):
    """
    Test break detection with cutoff priority selection.

    This test reproduces the specific scenario from rows 421-424 where:
    - Shift C has break_end_time: 02:45:00 and break_in_on_time_cutoff: 02:49:59
    - Input timestamps: 02:13:01, 02:39:29, 02:39:33, 04:59:54
    - Two gaps available:
        1. Gap between 02:13:01 and 02:39:29 (26 min 28 sec) - QUALIFIES (>= 5 min)
        2. Gap between 02:39:29 and 02:39:33 (4 sec) - TOO SMALL (< 5 min)
    - The algorithm should choose gap #1 because gap #2 doesn't meet minimum requirements
    - Expected: Break Time Out = 02:13:01, Break Time In = 02:39:29
    """
    shift_c = config.shifts['C']  # Night shift with cutoff 02:49:59

    # Create test data matching the scenario
    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 4, 2, 13, 1),   # First swipe
            datetime(2025, 11, 4, 2, 39, 29),  # Second swipe
            datetime(2025, 11, 4, 2, 39, 33),  # Third swipe
            datetime(2025, 11, 4, 4, 59, 54)   # Fourth swipe
        ],
        'burst_end': [
            datetime(2025, 11, 4, 2, 13, 1),   # First swipe
            datetime(2025, 11, 4, 2, 39, 29),  # Second swipe
            datetime(2025, 11, 4, 2, 39, 33),  # Third swipe
            datetime(2025, 11, 4, 4, 59, 54)   # Fourth swipe
        ]
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    # Test the break detection
    break_out, break_in, break_in_time = processor._detect_breaks(df, shift_c)

    # Verify the algorithm chose the correct gap according to current rules
    # Gap between 02:39:29 and 02:39:33 is only 4 seconds, which is < 5 minute minimum
    # So the algorithm should choose the only qualifying gap: 02:13:01 to 02:39:29
    assert break_out == "02:13:01", f"Expected Break Time Out: 02:13:01, Got: {break_out}"
    assert break_in == "02:39:29", f"Expected Break Time In: 02:39:29, Got: {break_in}"

    # Additional verification: ensure the break_in_time is correct
    assert break_in_time == time(2, 39, 29), f"Expected break_in_time: 02:39:29, Got: {break_in_time}"

    print(f"✅ Test passed: Break Time Out = {break_out}, Break Time In = {break_in}")
    print(f"✅ Correctly selected qualifying gap (4-second gap doesn't meet 5-min requirement)")


def test_detect_breaks_cutoff_priority_with_valid_small_gaps(processor, config):
    """
    Test break detection with scenario where small gaps should be considered.

    This test shows what would happen if we had gaps that are closer to the cutoff
    AND still meet minimum requirements.
    """
    shift_c = config.shifts['C']  # Night shift with cutoff 02:49:59

    # Create test data with valid gaps where closer one should be preferred
    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 4, 1, 30, 0),   # Early swipe
            datetime(2025, 11, 4, 2, 10, 0),   # Creates 40-min gap
            datetime(2025, 11, 4, 2, 49, 0),   # Close to cutoff - creates 39-min gap
            datetime(2025, 11, 4, 4, 0, 0)     # Final swipe
        ],
        'burst_end': [
            datetime(2025, 11, 4, 1, 30, 0),
            datetime(2025, 11, 4, 2, 10, 0),
            datetime(2025, 11, 4, 2, 49, 0),
            datetime(2025, 11, 4, 4, 0, 0)
        ]
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    # Test the break detection
    break_out, break_in, break_in_time = processor._detect_breaks(df, shift_c)

    # Both gaps qualify (> 5 min), but second gap should be chosen because
    # Break Time In (02:49:00) is closer to cutoff (02:49:59)
    assert break_out == "02:10:00", f"Expected Break Time Out: 02:10:00, Got: {break_out}"
    assert break_in == "02:49:00", f"Expected Break Time In: 02:49:00, Got: {break_in}"

    print(f"✅ Valid gaps test passed: Break Time Out = {break_out}, Break Time In = {break_in}")
    print(f"✅ Correctly selected gap with Break Time In closest to cutoff (02:49:00 vs 02:49:59)")


def test_detect_breaks_cutoff_priority_selection_multiple_gaps(processor, config):
    """
    Test break detection with multiple gaps where algorithm should prioritize cutoff proximity.

    This test verifies the enhanced logic works with more complex scenarios.
    """
    shift_c = config.shifts['C']  # Night shift with cutoff 02:49:59

    # Create test data with multiple qualifying gaps
    df = pd.DataFrame({
        'burst_start': [
            datetime(2025, 11, 4, 1, 30, 0),   # Early swipe
            datetime(2025, 11, 4, 2, 10, 0),   # Before cutoff gap
            datetime(2025, 11, 4, 2, 35, 0),   # Closer to cutoff
            datetime(2025, 11, 4, 2, 49, 0),   # Very close to cutoff (9 sec away)
            datetime(2025, 11, 4, 4, 0, 0)     # After cutoff
        ],
        'burst_end': [
            datetime(2025, 11, 4, 1, 30, 0),
            datetime(2025, 11, 4, 2, 10, 0),
            datetime(2025, 11, 4, 2, 35, 0),
            datetime(2025, 11, 4, 2, 49, 0),
            datetime(2025, 11, 4, 4, 0, 0)
        ]
    })
    df['time_start'] = df['burst_start'].dt.time
    df['time_end'] = df['burst_end'].dt.time

    # Test the break detection
    break_out, break_in, break_in_time = processor._detect_breaks(df, shift_c)

    # Verify independent selection (v10.0):
    # Break Time Out: 02:10 closest to checkpoint 02:00:00 (600 sec vs 1800/2100/2940 sec)
    # Break Time In: 02:49 closest to cutoff 02:49:59 (59 sec vs 899/2399/4201 sec)
    assert break_out == "02:10:00", f"Expected Break Time Out: 02:10:00, Got: {break_out}"
    assert break_in == "02:49:00", f"Expected Break Time In: 02:49:00, Got: {break_in}"

    print(f"✅ Multiple gaps test passed: Break Time Out = {break_out}, Break Time In = {break_in}")
    print(f"✅ Correctly selected independent Break Out (closest to checkpoint) and Break In (closest to cutoff)")
