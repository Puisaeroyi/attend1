"""Tests for configuration parsing"""

import pytest
from datetime import time
from config import RuleConfig, parse_time


def test_parse_time_hh_mm():
    """Test parsing HH:MM format"""
    assert parse_time("06:00") == time(6, 0, 0)
    assert parse_time("14:30") == time(14, 30, 0)
    assert parse_time("22:15") == time(22, 15, 0)


def test_parse_time_hh_mm_ss():
    """Test parsing HH:MM:SS format"""
    assert parse_time("10:15:30") == time(10, 15, 30)
    assert parse_time("02:22:30") == time(2, 22, 30)


def test_parse_time_with_whitespace():
    """Test parsing with surrounding whitespace"""
    assert parse_time(" 06:00 ") == time(6, 0, 0)
    assert parse_time("  14:30  ") == time(14, 30, 0)


def test_load_rule_yaml():
    """Test loading rule.yaml configuration"""
    config = RuleConfig.load_from_yaml('rule.yaml')

    # Check burst threshold
    assert config.burst_threshold_minutes == 2

    # Check status filter
    assert config.status_filter == "Success"

    # Check valid users
    assert len(config.valid_users) == 4
    assert 'Silver_Bui' in config.valid_users
    assert config.valid_users['Silver_Bui']['output_name'] == "Bui Duc Toan"
    assert config.valid_users['Silver_Bui']['output_id'] == "TPL0001"

    # Check shifts
    assert len(config.shifts) == 3
    assert 'A' in config.shifts
    assert 'B' in config.shifts
    assert 'C' in config.shifts


def test_shift_config_check_in_range():
    """Test shift check-in range detection"""
    config = RuleConfig.load_from_yaml('rule.yaml')

    shift_a = config.shifts['A']

    # Within range
    assert shift_a.is_in_check_in_range(time(6, 0, 0)) == True
    assert shift_a.is_in_check_in_range(time(6, 30, 0)) == True

    # Outside range (before)
    assert shift_a.is_in_check_in_range(time(5, 0, 0)) == False

    # Outside range (after)
    assert shift_a.is_in_check_in_range(time(7, 0, 0)) == False


def test_shift_config_display_names():
    """Test shift display names are correct"""
    config = RuleConfig.load_from_yaml('rule.yaml')

    assert config.shifts['A'].display_name == "Morning"
    assert config.shifts['B'].display_name == "Afternoon"
    assert config.shifts['C'].display_name == "Night"
