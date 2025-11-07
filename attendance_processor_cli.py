#!/usr/bin/env python3
"""
Attendance Data Processor - CLI Entry Point

Transforms raw biometric log data into cleaned attendance records
following rules defined in rule.yaml.

Usage:
    python main.py input.xlsx output.xlsx
"""

import argparse
import sys
from pathlib import Path

from config import RuleConfig
from processor import AttendanceProcessor
from validators import validate_input_file, validate_yaml_config
from utils import auto_rename_output


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Transform biometric logs into cleaned attendance records',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py output1.xlsx processed.xlsx
    python main.py /path/to/input.xlsx /path/to/output.xlsx

The program will:
  1. Load and validate input Excel file
  2. Filter by status (Success only) and valid users
  3. Detect and consolidate burst swipes (≤2min apart)
  4. Classify shifts (A/B/C) based on first check-in
  5. Extract First In, Break Out, Break In, Last Out times
  6. Write formatted output Excel file

Output file will be auto-renamed if it already exists.
        """
    )

    parser.add_argument(
        'input_file',
        help='Input Excel file path (raw biometric logs)'
    )
    parser.add_argument(
        'output_file',
        help='Output Excel file path (cleaned attendance records)'
    )
    parser.add_argument(
        '--config',
        default='rule.yaml',
        help='Path to rule.yaml configuration file (default: rule.yaml)'
    )

    args = parser.parse_args()

    try:
        # Validate configuration file
        print(f"🔧 Loading configuration: {args.config}")
        is_valid, error = validate_yaml_config(args.config)
        if not is_valid:
            print(f"❌ Error: {error}")
            return 1

        # Load configuration
        config = RuleConfig.load_from_yaml(args.config)
        print(f"   ✓ Loaded config: {len(config.shifts)} shifts, {len(config.valid_users)} valid users")

        # Validate input file
        print(f"📋 Validating input file: {args.input_file}")
        is_valid, error = validate_input_file(args.input_file)
        if not is_valid:
            print(f"❌ Error: {error}")
            return 1
        print(f"   ✓ Input file validated")

        # Auto-rename output if exists
        output_path = auto_rename_output(args.output_file)

        # Process
        print(f"\n{'='*60}")
        print(f"🚀 Starting processing pipeline")
        print(f"{'='*60}\n")

        processor = AttendanceProcessor(config)
        processor.process(args.input_file, output_path)

        print(f"\n{'='*60}")
        print(f"✅ Success! Output written to: {output_path}")
        print(f"{'='*60}")

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        return 1
    except ValueError as e:
        print(f"❌ Error: Invalid data - {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
