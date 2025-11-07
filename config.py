"""Configuration parser for rule.yaml"""

from dataclasses import dataclass
from datetime import time
from typing import Dict
import yaml


@dataclass
class ShiftConfig:
    """Configuration for a single shift"""
    name: str  # "A", "B", "C"
    display_name: str  # For output column
    check_in_start: time
    check_in_end: time
    check_out_start: time
    check_out_end: time
    break_search_start: time
    break_search_end: time
    break_out_checkpoint: time  # Target time for Break Time Out (window start)
    midpoint: time
    minimum_break_gap_minutes: int  # Minimum gap for break detection
    # v10.0 additions - late marking
    shift_start: time  # Official shift start time
    check_in_on_time_cutoff: time  # Last second to be on-time for check-in
    check_in_late_threshold: time  # This and after = Late for check-in
    break_end_time: time  # Official break end time
    break_in_on_time_cutoff: time  # Last second to be on-time for break return
    break_in_late_threshold: time  # This and after = Late for break return

    def is_in_check_in_range(self, t: time) -> bool:
        """Check if time falls in check-in search range"""
        if self.check_in_start <= self.check_in_end:
            return self.check_in_start <= t <= self.check_in_end
        else:
            # Handle midnight spanning (e.g., 21:30-06:35 for night shift)
            return t >= self.check_in_start or t <= self.check_in_end

    def determine_check_in_status(self, check_in_time: time) -> str:
        """Determine check-in status: 'On Time' or 'Late'

        Args:
            check_in_time: Employee check-in time

        Returns:
            'On Time' if <= on_time_cutoff, 'Late' if >= late_threshold, '' if blank
        """
        if check_in_time is None:
            return ""

        if check_in_time <= self.check_in_on_time_cutoff:
            return "On Time"
        elif check_in_time >= self.check_in_late_threshold:
            return "Late"
        return ""  # Edge case (shouldn't happen with proper cutoffs)

    def determine_break_in_status(self, break_in_time: time) -> str:
        """Determine break-in status: 'On Time' or 'Late'

        Args:
            break_in_time: Employee break return time

        Returns:
            'On Time' if <= on_time_cutoff, 'Late' if >= late_threshold, '' if blank
        """
        if break_in_time is None:
            return ""

        if break_in_time <= self.break_in_on_time_cutoff:
            return "On Time"
        elif break_in_time >= self.break_in_late_threshold:
            return "Late"
        return ""  # Edge case


@dataclass
class RuleConfig:
    """Complete configuration from rule.yaml"""
    burst_threshold_minutes: int
    valid_users: Dict[str, Dict[str, str]]  # username -> {output_name, output_id}
    shifts: Dict[str, ShiftConfig]
    status_filter: str

    @classmethod
    def load_from_yaml(cls, path: str, use_cache: bool = True) -> 'RuleConfig':
        """Parse rule.yaml into config objects with optional caching

        Args:
            path: Path to rule.yaml file
            use_cache: If True, return cached config if available (default: True)

        Returns:
            RuleConfig object
        """
        # Check cache first
        if use_cache:
            from performance import get_cached_config
            cached = get_cached_config(path)
            if cached:
                return cached

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        # Parse burst threshold
        burst_minutes = int(data['burst_detection']['definition'].split('<=')[1].split('minutes')[0].strip())

        # Parse valid users with mapping
        user_mapping = data['operators']['user_mapping']
        valid_users = {}
        for username, mapping in user_mapping.items():
            valid_users[username] = {
                'output_name': mapping['output_name'],
                'output_id': mapping['output_id']
            }

        # Parse shifts
        shifts = {}
        shift_data = data['shift_structure']['shifts']
        break_data = data['break_detection']['parameters']

        for shift_code in ['A', 'B', 'C']:
            shift_info = shift_data[shift_code]
            break_info = break_data[f'{shift_code}_shift']

            # Parse check-in configuration (v10.0)
            check_in_config = shift_info.get('check_in', {})
            if check_in_config:
                # v10.0 format with nested check_in structure
                check_in_range = check_in_config['search_range'].split('-')
                shift_start = parse_time(check_in_config['shift_start'])
                check_in_on_time_cutoff = parse_time(check_in_config['on_time_cutoff'])
                check_in_late_threshold = parse_time(check_in_config['late_threshold'])
            else:
                # v9.0 format - backwards compatibility
                check_in_range = shift_info['check_in_search_range'].split('-')
                # Default: 5-minute grace period
                shift_start_str = shift_info['window'].split('-')[0]
                shift_start = parse_time(shift_start_str)
                check_in_on_time_cutoff = time(shift_start.hour, shift_start.minute + 4, 59)
                check_in_late_threshold = time(shift_start.hour, shift_start.minute + 5, 0)

            check_in_start = parse_time(check_in_range[0])
            check_in_end = parse_time(check_in_range[1])

            # Parse check-out configuration
            check_out_config = shift_info.get('check_out', {})
            if check_out_config:
                # v10.0 format
                check_out_range = check_out_config['search_range'].split('-')
            else:
                # v9.0 format
                check_out_range = shift_info['check_out_search_range'].split('-')

            check_out_start = parse_time(check_out_range[0])
            check_out_end = parse_time(check_out_range[1])

            # Parse break configuration (v10.0)
            break_out_config = break_info.get('break_out', {})
            break_in_config = break_info.get('break_in', {})

            if break_out_config and break_in_config:
                # v10.0 format with separate break_out/break_in
                break_out_range = break_out_config['search_range'].split('-')
                break_in_range = break_in_config['search_range'].split('-')
                # Use broader range (should be same or break_in wider)
                break_search_start = parse_time(break_out_range[0])
                break_search_end = parse_time(break_in_range[1])

                # Parse break_out_checkpoint (new in fix)
                if 'checkpoint' in break_out_config:
                    break_out_checkpoint = parse_time(break_out_config['checkpoint'])
                else:
                    # Fallback: use window start time
                    window_start = break_info['window'].split('-')[0]
                    break_out_checkpoint = parse_time(window_start)

                break_end_time = parse_time(break_in_config['break_end_time'])
                break_in_on_time_cutoff = parse_time(break_in_config['on_time_cutoff'])
                break_in_late_threshold = parse_time(break_in_config['late_threshold'])
            else:
                # v9.0 format - backwards compatibility
                break_range = break_info['search_range'].split('-')
                break_search_start = parse_time(break_range[0])
                break_search_end = parse_time(break_range[1])

                # Default break_out_checkpoint: use window start time
                window_start = break_info['window'].split('-')[0]
                break_out_checkpoint = parse_time(window_start)

                # Default: break window end time + 5-minute grace period
                break_window_end_str = break_info['window'].split('-')[1]
                break_end_time = parse_time(break_window_end_str)
                break_in_on_time_cutoff = time(break_end_time.hour, break_end_time.minute + 4, 59)
                break_in_late_threshold = time(break_end_time.hour, break_end_time.minute + 5, 0)

            # Parse midpoint
            midpoint = parse_time(break_info['midpoint_checkpoint'])

            # Parse minimum break gap
            minimum_break_gap = break_info['minimum_break_gap_minutes']

            # Determine display name
            display_names = {'A': 'Morning', 'B': 'Afternoon', 'C': 'Night'}

            shifts[shift_code] = ShiftConfig(
                name=shift_code,
                display_name=display_names[shift_code],
                check_in_start=check_in_start,
                check_in_end=check_in_end,
                check_out_start=check_out_start,
                check_out_end=check_out_end,
                break_search_start=break_search_start,
                break_search_end=break_search_end,
                break_out_checkpoint=break_out_checkpoint,
                midpoint=midpoint,
                minimum_break_gap_minutes=minimum_break_gap,
                shift_start=shift_start,
                check_in_on_time_cutoff=check_in_on_time_cutoff,
                check_in_late_threshold=check_in_late_threshold,
                break_end_time=break_end_time,
                break_in_on_time_cutoff=break_in_on_time_cutoff,
                break_in_late_threshold=break_in_late_threshold
            )

        # Status filter
        status_filter = data['dataset_requirements']['input_logs']['status_filter'].split(' ')[0]

        config = cls(
            burst_threshold_minutes=burst_minutes,
            valid_users=valid_users,
            shifts=shifts,
            status_filter=status_filter
        )

        # Cache for future use
        if use_cache:
            from performance import cache_config
            cache_config(path, config)

        return config


def parse_time(s: str) -> time:
    """Convert time string to time object

    Handles formats:
    - "HH:MM" -> time(HH, MM, 0)
    - "HH:MM:SS" -> time(HH, MM, SS)
    """
    s = s.strip()
    parts = s.split(':')

    if len(parts) == 2:
        return time(int(parts[0]), int(parts[1]), 0)
    elif len(parts) == 3:
        return time(int(parts[0]), int(parts[1]), int(parts[2]))
    else:
        raise ValueError(f"Invalid time format: {s}")
