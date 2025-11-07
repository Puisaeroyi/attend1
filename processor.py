"""Core attendance data processing pipeline"""

from typing import Tuple
import pandas as pd
from config import RuleConfig, ShiftConfig


class AttendanceProcessor:
    """Process raw biometric logs into cleaned attendance records"""

    def __init__(self, config: RuleConfig):
        self.config = config

    def process(self, input_path: str, output_path: str):
        """Main processing pipeline

        Args:
            input_path: Path to input Excel file
            output_path: Path to output Excel file
        """
        print(f"📖 Loading input: {input_path}")
        df = self._load_excel(input_path)
        print(f"   Loaded {len(df)} records")

        print(f"🔍 Filtering by status: {self.config.status_filter}")
        df = self._filter_valid_status(df)
        print(f"   {len(df)} records after status filter")

        print(f"👥 Filtering valid users")
        df = self._filter_valid_users(df)
        print(f"   {len(df)} records after user filter")

        if len(df) == 0:
            print("⚠ No valid records to process after filtering")
            return

        print(f"🔄 Detecting bursts (≤{self.config.burst_threshold_minutes}min)")
        df = self._detect_bursts(df)
        print(f"   {len(df)} events after burst consolidation")

        print(f"📅 Detecting shift instances (handles midnight crossing)")
        df = self._detect_shift_instances(df)
        print(f"   {len(df)} swipes assigned to shift instances")

        print(f"⏰ Extracting attendance events")
        df = self._extract_attendance_events(df)
        print(f"   {len(df)} attendance records generated")

        print(f"💾 Writing output: {output_path}")
        self._write_output(df, output_path)
        print(f"✅ Processing complete!")

    def _load_excel(self, path: str) -> pd.DataFrame:
        """Load input Excel, parse datetime, validate columns (optimized)"""
        # OPTIMIZATION: Try xlrd first (faster for .xls), fall back to openpyxl
        try:
            df = pd.read_excel(path, engine='xlrd')
        except:
            try:
                # For .xlsx: use openpyxl with data_only to skip formulas
                df = pd.read_excel(path, engine='openpyxl', data_only=True)
            except:
                # Final fallback to default engine
                df = pd.read_excel(path)

        # Validate required columns
        required_cols = ['ID', 'Name', 'Date', 'Time', 'Status']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        # OPTIMIZATION: Use fast datetime parsing with format hint
        from performance import parse_datetime_optimized
        df['timestamp'] = df.apply(
            lambda row: parse_datetime_optimized(str(row['Date']), str(row['Time'])),
            axis=1
        )

        # Remove rows with invalid timestamps
        invalid_count = df['timestamp'].isna().sum()
        if invalid_count > 0:
            print(f"   ⚠ Skipped {invalid_count} rows with invalid timestamps")
            df = df[df['timestamp'].notna()].copy()

        # OPTIMIZATION: Sort once with composite key
        df = df.sort_values(['Name', 'timestamp'], na_position='last').reset_index(drop=True)

        return df

    def _filter_valid_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only records with Success status"""
        before = len(df)
        df = df[df['Status'] == self.config.status_filter].copy()
        after = len(df)

        if before - after > 0:
            print(f"   ⚠ Filtered {before - after} non-{self.config.status_filter} records")

        return df

    def _filter_valid_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only valid users and map to output names"""
        valid_usernames = set(self.config.valid_users.keys())
        before = len(df)

        # Filter: keep only valid usernames
        df = df[df['Name'].isin(valid_usernames)].copy()
        after = len(df)

        if before - after > 0:
            print(f"   ⚠ Filtered {before - after} invalid user records")

        # Map username to output name and ID
        df['output_name'] = df['Name'].map(
            lambda x: self.config.valid_users[x]['output_name']
        )
        df['output_id'] = df['Name'].map(
            lambda x: self.config.valid_users[x]['output_id']
        )

        return df

    def _detect_bursts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group swipes ≤2min apart, keep earliest start + latest end

        Uses compare-diff-cumsum pattern for efficient burst detection (optimized).
        """
        threshold = pd.Timedelta(minutes=self.config.burst_threshold_minutes)

        # OPTIMIZATION: Use sort=False to avoid re-sorting (already sorted)
        df['time_diff'] = df.groupby('Name', sort=False)['timestamp'].diff()

        # Mark burst boundaries (diff > threshold OR first row)
        df['new_burst'] = (df['time_diff'] > threshold) | df['time_diff'].isna()

        # Create burst group IDs
        df['burst_id'] = df.groupby('Name', sort=False)['new_burst'].cumsum()

        # For each burst: keep earliest timestamp as start, latest as end
        burst_groups = df.groupby(['Name', 'burst_id'], sort=False).agg({
            'timestamp': ['min', 'max'],
            'output_name': 'first',
            'output_id': 'first'
        }).reset_index()

        # Flatten multi-index columns
        burst_groups.columns = ['Name', 'burst_id', 'burst_start', 'burst_end', 'output_name', 'output_id']

        # Keep both burst_start and burst_end for proper event extraction
        # Different events use different timestamps from bursts:
        # - First In / Break In: use burst_start (earliest)
        # - Break Out / Last Out: use burst_end (latest)

        return burst_groups

    def _detect_shift_instances(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect shift instances based on First In swipes (check-in range)

        CRITICAL: Implements shift-instance grouping per rule.yaml v9.0
        - One shift instance = one complete attendance record
        - Night shifts crossing midnight stay as single record
        - Date = shift START date, not individual swipe calendar dates

        Algorithm:
        1. Find all check-in swipes (potential shift starts)
        2. For each check-in, create shift instance with activity window
        3. Assign all subsequent swipes to that instance until next check-in
        4. Handle night shift midnight crossing
        """
        # Sort by user and time to ensure chronological processing
        df = df.sort_values(['Name', 'burst_start']).reset_index(drop=True)

        # Initialize shift instance tracking
        df['shift_code'] = None
        df['shift_date'] = None
        df['shift_instance_id'] = None

        instance_id = 0

        for username in df['Name'].unique():
            user_mask = df['Name'] == username
            user_df = df[user_mask].copy()

            i = 0
            while i < len(user_df):
                row_idx = user_df.index[i]
                swipe_time = user_df.loc[row_idx, 'burst_start']
                swipe_time_only = swipe_time.time()

                # Check if this is a valid check-in (shift start)
                shift_code = None
                for code, shift_cfg in self.config.shifts.items():
                    if shift_cfg.is_in_check_in_range(swipe_time_only):
                        shift_code = code
                        break

                if shift_code:
                    # Found a shift start - create new shift instance
                    shift_date = swipe_time.date()
                    shift_cfg = self.config.shifts[shift_code]

                    # Determine activity window for this shift
                    from datetime import datetime, timedelta
                    if shift_code == 'C':
                        # Night shift: activity window ends at 06:35 NEXT day
                        window_end = datetime.combine(shift_date + timedelta(days=1),
                                                      shift_cfg.check_out_end)
                    elif shift_code == 'B':
                        # Afternoon shift: activity window ends at 22:35 same day
                        window_end = datetime.combine(shift_date, shift_cfg.check_out_end)
                    else:  # 'A'
                        # Morning shift: activity window ends at 14:35 same day
                        window_end = datetime.combine(shift_date, shift_cfg.check_out_end)

                    # Assign this swipe and ALL swipes within activity window to instance
                    # CRITICAL FIX: Include check-in range swipes as part of same instance
                    # Priority: check-out range > check-in range for overlapping windows
                    j = i
                    while j < len(user_df):
                        curr_idx = user_df.index[j]
                        curr_swipe = user_df.loc[curr_idx, 'burst_start']

                        # Check if swipe is within activity window
                        if curr_swipe <= window_end:
                            curr_time = curr_swipe.time()

                            # Check if in current shift's check-out range (highest priority)
                            in_current_checkout = self._time_in_range(
                                pd.Series([curr_time]),
                                shift_cfg.check_out_start,
                                shift_cfg.check_out_end
                            ).iloc[0]

                            # Check if would start a DIFFERENT shift type
                            would_start_different_shift = False
                            if not in_current_checkout and j > i:
                                for code, cfg in self.config.shifts.items():
                                    if code != shift_code and cfg.is_in_check_in_range(curr_time):
                                        would_start_different_shift = True
                                        break

                            if would_start_different_shift:
                                # This swipe starts a different shift type and not in checkout, stop
                                break

                            # Assign to current instance
                            df.loc[curr_idx, 'shift_code'] = shift_code
                            df.loc[curr_idx, 'shift_date'] = shift_date
                            df.loc[curr_idx, 'shift_instance_id'] = instance_id
                            j += 1
                        else:
                            # Outside activity window, stop
                            break

                    instance_id += 1
                    i = j  # Move to next unprocessed swipe
                else:
                    # Not a check-in swipe, skip (orphan swipe)
                    i += 1

        # Filter out orphan swipes (no shift assignment)
        before = len(df)
        df = df[df['shift_code'].notna()].copy()
        after = len(df)
        if before - after > 0:
            print(f"   ⚠ Filtered {before - after} orphan swipes (no shift assignment)")

        return df

    def _extract_attendance_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        For each shift instance:
        - Check-in: earliest in check-in window (v10.0 terminology)
        - Check-in Status: 'On Time' or 'Late' based on grace period
        - Break Time Out: latest BEFORE/AT midpoint in break window
        - Break Time In: earliest AFTER midpoint in break window
        - Break Time In Status: 'On Time' or 'Late' based on grace period
        - Check Out Record: latest in check-out window

        NOTE: Groups by shift_instance_id, NOT calendar_date
        This ensures night shifts crossing midnight stay as single records
        """
        results = []

        for instance_id, group in df.groupby('shift_instance_id'):
            shift_code = group['shift_code'].iloc[0]
            shift_date = group['shift_date'].iloc[0]
            shift_cfg = self.config.shifts[shift_code]
            output_name = group['output_name'].iloc[0]
            output_id = group['output_id'].iloc[0]

            # Extract time components for filtering
            group = group.copy()
            group['time_start'] = group['burst_start'].dt.time
            group['time_end'] = group['burst_end'].dt.time

            # Extract events (returns time strings or None)
            check_in_str, check_in_time = self._find_check_in(group, shift_cfg)
            check_out_str = self._find_check_out(group, shift_cfg)
            break_out_str, break_in_str, break_in_time = self._detect_breaks(group, shift_cfg)

            # Determine statuses
            check_in_status = shift_cfg.determine_check_in_status(check_in_time) if check_in_time else ""
            break_in_status = shift_cfg.determine_break_in_status(break_in_time) if break_in_time else ""

            results.append({
                'Date': shift_date,  # Shift START date, not swipe calendar date
                'ID': output_id,
                'Name': output_name,
                'Shift': shift_cfg.display_name,
                'Check-in': check_in_str,
                'Check-in Status': check_in_status,
                'Break Time Out': break_out_str,
                'Break Time In': break_in_str,
                'Break Time In Status': break_in_status,
                'Check Out Record': check_out_str
            })

        return pd.DataFrame(results)

    def _find_check_in(self, group: pd.DataFrame, shift_cfg: ShiftConfig) -> tuple:
        """Find earliest timestamp in check-in window (use burst_start for bursts)

        Returns:
            tuple: (time_string, time_object) for status calculation
        """
        mask = self._time_in_range(
            group['time_start'],
            shift_cfg.check_in_start,
            shift_cfg.check_in_end
        )
        candidates = group[mask]

        if len(candidates) > 0:
            ts = candidates['burst_start'].min()
            return ts.strftime('%H:%M:%S'), ts.time()
        return "", None

    def _find_check_out(self, group: pd.DataFrame, shift_cfg: ShiftConfig) -> str:
        """Find latest timestamp in check-out window (use burst_end for bursts)"""
        mask = self._time_in_range(
            group['time_end'],
            shift_cfg.check_out_start,
            shift_cfg.check_out_end
        )
        candidates = group[mask]

        if len(candidates) > 0:
            ts = candidates['burst_end'].max()
            return ts.strftime('%H:%M:%S')
        return ""

    def _detect_breaks(self, group: pd.DataFrame, shift_cfg: ShiftConfig) -> Tuple[str, str, object]:
        """
        Detect break using two-tier algorithm per rule.yaml v10.0:

        PRIORITY 1 - Gap Detection:
        - Find gap >= minimum_break_gap_minutes between consecutive swipes/bursts
        - Break Time Out: burst/swipe immediately BEFORE gap (use burst_end)
        - Break Time In: burst/swipe immediately AFTER gap (use burst_start)

        PRIORITY 2 - Midpoint Logic (fallback):
        - If no qualifying gap found, use midpoint checkpoint
        - Break Time Out: latest BEFORE/AT midpoint (use burst_end)
        - Break Time In: earliest AFTER midpoint (use burst_start)
        - Handle edge cases (all before, all after, single swipe)

        Returns:
            tuple: (break_out_str, break_in_str, break_in_time) for status calculation
        """
        min_gap = shift_cfg.minimum_break_gap_minutes
        midpoint = shift_cfg.midpoint

        # Filter swipes/bursts in break search window
        mask = self._time_in_range(
            group['time_start'],
            shift_cfg.break_search_start,
            shift_cfg.break_search_end
        ) | self._time_in_range(
            group['time_end'],
            shift_cfg.break_search_start,
            shift_cfg.break_search_end
        )
        break_swipes = group[mask].copy().sort_values('burst_start').reset_index(drop=True)

        if len(break_swipes) == 0:
            return "", "", None

        # PRIORITY 1: Try gap-based detection first (highest priority per rule.yaml)
        if len(break_swipes) >= 2:
            # Calculate gaps between consecutive swipes
            # Gap = time from end of previous burst to start of next burst
            break_swipes['next_burst_start'] = break_swipes['burst_start'].shift(-1)
            break_swipes['gap_minutes'] = (
                break_swipes['next_burst_start'] - break_swipes['burst_end']
            ).dt.total_seconds() / 60

            # Find gaps that meet minimum threshold
            qualifying_gaps = break_swipes[break_swipes['gap_minutes'] >= min_gap]

            if len(qualifying_gaps) > 0:
                # Enhanced logic: Independent gap selection
                # Break Time Out: closest to checkpoint (window start)
                # Break Time In: closest to cutoff (grace period end)
                checkpoint = shift_cfg.break_out_checkpoint
                cutoff = shift_cfg.break_in_on_time_cutoff

                def time_to_seconds(t: object) -> int:
                    """Convert time to seconds for distance calculation"""
                    return t.hour * 3600 + t.minute * 60 + t.second

                # Find Break Time Out: gap with Break Time Out closest to checkpoint
                best_out_gap = None
                min_distance_to_checkpoint = float('inf')

                for gap_idx in qualifying_gaps.index:
                    break_out_ts = break_swipes.loc[gap_idx, 'burst_end']
                    break_out_time = break_out_ts.time()

                    # Calculate distance from checkpoint (in seconds)
                    checkpoint_sec = time_to_seconds(checkpoint)
                    break_out_sec = time_to_seconds(break_out_time)
                    distance = abs(break_out_sec - checkpoint_sec)

                    if distance < min_distance_to_checkpoint:
                        min_distance_to_checkpoint = distance
                        best_out_gap = gap_idx

                # Find Break Time In: gap with Break Time In closest to cutoff
                best_in_gap = None
                min_distance_to_cutoff = float('inf')

                for gap_idx in qualifying_gaps.index:
                    break_in_ts = break_swipes.loc[gap_idx + 1, 'burst_start']
                    break_in_time = break_in_ts.time()

                    # Calculate distance from cutoff (in seconds)
                    cutoff_sec = time_to_seconds(cutoff)
                    break_in_sec = time_to_seconds(break_in_time)
                    distance = abs(break_in_sec - cutoff_sec)

                    if distance < min_distance_to_cutoff:
                        min_distance_to_cutoff = distance
                        best_in_gap = gap_idx

                # Return independently selected Break Time Out and Break Time In
                if best_out_gap is not None and best_in_gap is not None:
                    break_out_ts = break_swipes.loc[best_out_gap, 'burst_end']
                    break_in_ts = break_swipes.loc[best_in_gap + 1, 'burst_start']

                    return (
                        break_out_ts.strftime('%H:%M:%S'),
                        break_in_ts.strftime('%H:%M:%S'),
                        break_in_ts.time()
                    )

        # PRIORITY 2: Fallback to midpoint logic when no qualifying gaps found
        before_midpoint = break_swipes[break_swipes['time_end'] <= midpoint]
        after_midpoint = break_swipes[break_swipes['time_start'] > midpoint]

        # Case 1: Swipes span midpoint - use midpoint logic
        if len(before_midpoint) > 0 and len(after_midpoint) > 0:
            break_out_ts = before_midpoint['burst_end'].max()
            break_in_ts = after_midpoint['burst_start'].min()
            return break_out_ts.strftime('%H:%M:%S'), break_in_ts.strftime('%H:%M:%S'), break_in_ts.time()

        # PRIORITY 3: Handle single-side cases with midpoint logic

        # Case 2: All swipes before midpoint
        if len(before_midpoint) > 0 and len(after_midpoint) == 0:
            # Check for gap within before_midpoint swipes
            if len(before_midpoint) >= 2:
                # Use gap detection within before_midpoint
                before_sorted = before_midpoint.sort_values('burst_start').reset_index(drop=True)
                before_sorted['next_start'] = before_sorted['burst_start'].shift(-1)
                before_sorted['gap_min'] = (
                    before_sorted['next_start'] - before_sorted['burst_end']
                ).dt.total_seconds() / 60
                gap_found = before_sorted[before_sorted['gap_min'] >= min_gap]

                if len(gap_found) > 0:
                    idx = gap_found.index[0]
                    break_in_ts = before_sorted.loc[idx + 1, 'burst_start']
                    return (
                        before_sorted.loc[idx, 'burst_end'].strftime('%H:%M:%S'),
                        break_in_ts.strftime('%H:%M:%S'),
                        break_in_ts.time()
                    )

            # No gap: Break Out = latest, Break In = blank
            break_out = before_midpoint['burst_end'].max().strftime('%H:%M:%S')
            return break_out, "", None

        # Case 3: All swipes after midpoint
        if len(before_midpoint) == 0 and len(after_midpoint) > 0:
            # Check for gap within after_midpoint swipes
            if len(after_midpoint) >= 2:
                after_sorted = after_midpoint.sort_values('burst_start').reset_index(drop=True)
                after_sorted['next_start'] = after_sorted['burst_start'].shift(-1)
                after_sorted['gap_min'] = (
                    after_sorted['next_start'] - after_sorted['burst_end']
                ).dt.total_seconds() / 60
                gap_found = after_sorted[after_sorted['gap_min'] >= min_gap]

                if len(gap_found) > 0:
                    idx = gap_found.index[0]
                    break_in_ts = after_sorted.loc[idx + 1, 'burst_start']
                    return (
                        after_sorted.loc[idx, 'burst_end'].strftime('%H:%M:%S'),
                        break_in_ts.strftime('%H:%M:%S'),
                        break_in_ts.time()
                    )

            # No gap: Break Out = blank, Break In = earliest
            break_in_ts = after_midpoint['burst_start'].min()
            return "", break_in_ts.strftime('%H:%M:%S'), break_in_ts.time()

        # Case 4: No swipes (shouldn't reach here due to early return)
        return "", "", None

    def _time_in_range(self, time_series: pd.Series, start: pd.Timestamp.time, end: pd.Timestamp.time) -> pd.Series:
        """Check if times fall within range, handling midnight-spanning ranges

        Args:
            time_series: Series of time objects
            start: Range start time
            end: Range end time

        Returns:
            Boolean series indicating if each time is in range
        """
        if start <= end:
            # Normal range (e.g., 09:50 to 10:35)
            return (time_series >= start) & (time_series <= end)
        else:
            # Midnight-spanning range (e.g., 21:30 to 06:35)
            return (time_series >= start) | (time_series <= end)

    def _write_output(self, df: pd.DataFrame, output_path: str):
        """Write to Excel with proper formatting"""
        # Ensure Date is proper date format for Excel
        df['Date'] = pd.to_datetime(df['Date'])

        # Write with xlsxwriter for performance and formatting
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Attendance', index=False)

            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Attendance']

            # Header format
            header_fmt = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'align': 'center',
                'valign': 'vcenter'
            })

            # Apply header format and set column widths
            for col_num, col_name in enumerate(df.columns):
                worksheet.write(0, col_num, col_name, header_fmt)
                # Set appropriate column widths
                if col_name == 'Date':
                    worksheet.set_column(col_num, col_num, 12)
                elif col_name == 'ID':
                    worksheet.set_column(col_num, col_num, 10)
                elif col_name == 'Name':
                    worksheet.set_column(col_num, col_num, 20)
                elif 'Status' in col_name:
                    worksheet.set_column(col_num, col_num, 14)
                else:
                    worksheet.set_column(col_num, col_num, 12)
