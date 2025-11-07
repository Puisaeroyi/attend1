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
        'timestamp': pd.date_range('2025-11-02 06:00', periods=4, freq='1H')
    })

    result = processor._filter_valid_status(df)

    assert len(result) == 3
    assert all(result['Status'] == 'Success')


def test_filter_valid_users(processor):
    """Test filtering by valid users"""
    df = pd.DataFrame({
        'Name': ['Silver_Bui', 'Unknown', 'Capone', 'Invalid'],
        'timestamp': pd.date_range('2025-11-02 06:00', periods=4, freq='1H')
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
        'timestamp': [
            datetime(2025, 11, 2, 6, 0, 0),
            datetime(2025, 11, 2, 6, 0, 30),  # 30s later
            datetime(2025, 11, 2, 6, 1, 45),  # 1:45 later
            datetime(2025, 11, 2, 6, 10, 0)   # 8:15 later (separate)
        ],
        'output_name': ['Bui Duc Toan'] * 4,
        'output_id': ['TPL0001'] * 4
    })

    result = processor._detect_bursts(df)

    # Should have 2 events: 1 burst + 1 separate
    assert len(result) == 2

    # First event should be the burst start (earliest)
    assert result.iloc[0]['timestamp'] == datetime(2025, 11, 2, 6, 0, 0)

    # Second event should be the separate swipe
    assert result.iloc[1]['timestamp'] == datetime(2025, 11, 2, 6, 10, 0)


def test_shift_classification(processor):
    """Test shift classification based on first timestamp"""
    df = pd.DataFrame({
        'Name': ['Silver_Bui', 'Silver_Bui', 'Capone', 'Minh'],
        'timestamp': [
            datetime(2025, 11, 2, 6, 0, 0),    # Morning shift A (in check-in range 05:30-06:35)
            datetime(2025, 11, 2, 10, 0, 0),   # Same day, same user
            datetime(2025, 11, 2, 14, 0, 0),   # Afternoon shift B (in check-in range 13:30-14:35)
            datetime(2025, 11, 2, 22, 0, 0)    # Night shift C (in check-in range 21:30-22:35)
        ],
        'output_name': ['Bui Duc Toan', 'Bui Duc Toan', 'Pham Tan Phat', 'Mac Le Duc Minh'],
        'output_id': ['TPL0001', 'TPL0001', 'TPL0002', 'TPL0003']
    })

    result = processor._classify_shifts(df)

    # All rows for Silver_Bui on same day should have same shift (A)
    silver_rows = result[result['Name'] == 'Silver_Bui']
    assert all(silver_rows['shift'] == 'A')

    # Capone should be shift B
    capone_rows = result[result['Name'] == 'Capone']
    assert all(capone_rows['shift'] == 'B')

    # Minh should be shift C
    minh_rows = result[result['Name'] == 'Minh']
    assert all(minh_rows['shift'] == 'C')


def test_find_first_in(processor, config):
    """Test finding first check-in within window"""
    shift_a = config.shifts['A']

    # Swipes: before window, in window, in window, after window
    df = pd.DataFrame({
        'timestamp': [
            datetime(2025, 11, 2, 5, 0, 0),   # Too early
            datetime(2025, 11, 2, 6, 0, 0),   # First in window
            datetime(2025, 11, 2, 6, 30, 0),  # Also in window
            datetime(2025, 11, 2, 7, 0, 0)    # Too late
        ]
    })
    df['time_only'] = df['timestamp'].dt.time

    result = processor._find_first_in(df, shift_a)

    # Should return earliest in window (06:00:00)
    assert result == "06:00:00"


def test_find_first_in_no_match(processor, config):
    """Test finding first check-in when none in window"""
    shift_a = config.shifts['A']

    df = pd.DataFrame({
        'timestamp': [
            datetime(2025, 11, 2, 5, 0, 0),   # Too early
            datetime(2025, 11, 2, 7, 0, 0)    # Too late
        ]
    })
    df['time_only'] = df['timestamp'].dt.time

    result = processor._find_first_in(df, shift_a)

    # Should return empty string
    assert result == ""


def test_detect_breaks_normal(processor, config):
    """Test break detection with 2 swipes (before/after midpoint)"""
    shift_a = config.shifts['A']  # Midpoint: 10:15

    df = pd.DataFrame({
        'timestamp': [
            datetime(2025, 11, 2, 9, 55, 0),   # Before midpoint
            datetime(2025, 11, 2, 10, 30, 0)   # After midpoint
        ]
    })
    df['time_only'] = df['timestamp'].dt.time

    break_out, break_in = processor._detect_breaks(df, shift_a)

    assert break_out == "09:55:00"
    assert break_in == "10:30:00"


def test_detect_breaks_single_before_midpoint(processor, config):
    """Test break detection with single swipe before midpoint"""
    shift_a = config.shifts['A']  # Midpoint: 10:15

    df = pd.DataFrame({
        'timestamp': [datetime(2025, 11, 2, 10, 8, 0)]  # Before midpoint
    })
    df['time_only'] = df['timestamp'].dt.time

    break_out, break_in = processor._detect_breaks(df, shift_a)

    assert break_out == "10:08:00"
    assert break_in == ""  # Empty


def test_detect_breaks_single_after_midpoint(processor, config):
    """Test break detection with single swipe after midpoint"""
    shift_a = config.shifts['A']  # Midpoint: 10:15

    df = pd.DataFrame({
        'timestamp': [datetime(2025, 11, 2, 10, 20, 0)]  # After midpoint
    })
    df['time_only'] = df['timestamp'].dt.time

    break_out, break_in = processor._detect_breaks(df, shift_a)

    assert break_out == ""  # Empty
    assert break_in == "10:20:00"


def test_detect_breaks_no_swipes(processor, config):
    """Test break detection with no swipes in window"""
    shift_a = config.shifts['A']

    df = pd.DataFrame({
        'timestamp': [
            datetime(2025, 11, 2, 6, 0, 0),    # Too early for break window
            datetime(2025, 11, 2, 14, 0, 0)    # Too late for break window
        ]
    })
    df['time_only'] = df['timestamp'].dt.time

    break_out, break_in = processor._detect_breaks(df, shift_a)

    assert break_out == ""
    assert break_in == ""


def test_detect_breaks_multiple_swipes(processor, config):
    """Test break detection with multiple swipes each side of midpoint"""
    shift_a = config.shifts['A']  # Midpoint: 10:15

    df = pd.DataFrame({
        'timestamp': [
            datetime(2025, 11, 2, 9, 50, 0),   # Before
            datetime(2025, 11, 2, 9, 55, 0),   # Before (latest before midpoint)
            datetime(2025, 11, 2, 10, 25, 0),  # After (earliest after midpoint)
            datetime(2025, 11, 2, 10, 30, 0)   # After
        ]
    })
    df['time_only'] = df['timestamp'].dt.time

    break_out, break_in = processor._detect_breaks(df, shift_a)

    # Break Out should be latest before/at midpoint
    assert break_out == "09:55:00"

    # Break In should be earliest after midpoint
    assert break_in == "10:25:00"


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
