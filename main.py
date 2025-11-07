#!/usr/bin/env python3
"""Unified Attendance & CSV Converter Tool

A menu-driven application that provides:
1. CSV to XLSX conversion (with column extraction)
2. Attendance data processing (biometric log cleaning)
0. Exit

Author: Development Team
Version: 2.1.0
"""

import sys
from pathlib import Path

# Import CSV converter functions
import csv_converter
import pandas as pd

# Import attendance processor
from config import RuleConfig
from processor import AttendanceProcessor
from validators import validate_input_file


def clear_screen():
    """Clear terminal screen."""
    print("\033[H\033[J", end="")


def print_header():
    """Print application header."""
    print("=" * 70)
    print("  ATTENDANCE & CSV CONVERTER TOOL v2.1.0")
    print("=" * 70)
    print()


def print_menu():
    """Display main menu."""
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│                        MAIN MENU                            │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│  1. CSV to XLSX Converter                                  │")
    print("│     → Extract columns from CSV and convert to Excel        │")
    print("│                                                             │")
    print("│  2. Attendance Data Processor                              │")
    print("│     → Process biometric logs into attendance records       │")
    print("│                                                             │")
    print("│  0. Exit                                                    │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()


def get_user_choice() -> str:
    """Get menu choice from user.

    Returns:
        User's choice as string
    """
    while True:
        choice = input("Enter your choice (0-2): ").strip()
        if choice in ['0', '1', '2']:
            return choice
        print("❌ Invalid choice. Please enter 0, 1, or 2.")


def get_file_path(prompt: str, must_exist: bool = True) -> str:
    """Get file path from user with validation.

    Args:
        prompt: Prompt message to display
        must_exist: Whether file must exist

    Returns:
        Validated file path
    """
    while True:
        path = input(f"{prompt}: ").strip()

        if not path:
            print("❌ Path cannot be empty. Try again.")
            continue

        path_obj = Path(path)

        if must_exist and not path_obj.exists():
            print(f"❌ File not found: {path}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return ""
            continue

        return path


def csv_to_xlsx_workflow():
    """Execute CSV to XLSX conversion workflow."""
    clear_screen()
    print_header()
    print("╔═════════════════════════════════════════════════════════════╗")
    print("║              CSV TO XLSX CONVERTER                          ║")
    print("╚═════════════════════════════════════════════════════════════╝")
    print()
    print("This tool extracts columns [0,1,2,3,4,6] from CSV")
    print("Output columns: ID, Name, Date, Time, Type, Status")
    print()

    # Get input file
    input_path = get_file_path("📂 Enter CSV input file path")
    if not input_path:
        return

    # Get output file
    output_path = get_file_path("💾 Enter XLSX output file path", must_exist=False)
    if not output_path:
        return

    print()
    print("🔄 Processing...")

    try:
        # Validate inputs
        csv_converter.validate_input_file(input_path)
        csv_converter.validate_output_path(output_path)

        # Convert
        row_count = csv_converter.convert_csv_to_xlsx(input_path, output_path)

        # Success
        print()
        print("✅ Conversion successful!")
        print(f"   Input:   {input_path}")
        print(f"   Output:  {output_path}")
        print(f"   Rows:    {row_count}")
        print(f"   Columns: {len(csv_converter.COLUMN_NAMES)} ({', '.join(csv_converter.COLUMN_NAMES)})")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except pd.errors.EmptyDataError:
        print("\n❌ Error: CSV file is empty")
    except pd.errors.ParserError as e:
        print(f"\n❌ Error: Malformed CSV - {e}")
    except PermissionError as e:
        print(f"\n❌ Error: Permission denied - {e}")
    except Exception as e:
        print(f"\n❌ Error: Unexpected error - {e}")

    print()
    input("Press Enter to continue...")


def attendance_processor_workflow():
    """Execute attendance data processing workflow."""
    clear_screen()
    print_header()
    print("╔═════════════════════════════════════════════════════════════╗")
    print("║          ATTENDANCE DATA PROCESSOR                          ║")
    print("╚═════════════════════════════════════════════════════════════╝")
    print()
    print("Process biometric swipe logs into cleaned attendance records")
    print("Features: Burst detection, Shift grouping, Break detection")
    print()

    # Get input file
    input_path = get_file_path("📂 Enter input Excel file path (.xlsx)")
    if not input_path:
        return

    # Get output file
    output_path = get_file_path("💾 Enter output Excel file path (.xlsx)", must_exist=False)
    if not output_path:
        return

    # Get config file (optional)
    print()
    config_path = input("⚙️  Enter config file path (press Enter for default 'rule.yaml'): ").strip()
    if not config_path:
        config_path = "rule.yaml"

    print()
    print("=" * 70)
    print("🚀 Starting processing pipeline")
    print("=" * 70)
    print()

    try:
        # Load configuration
        print(f"🔧 Loading configuration: {config_path}")
        config = RuleConfig.load_from_yaml(config_path)
        print(f"   ✓ Loaded config: {len(config.shifts)} shifts, {len(config.valid_users)} valid users")

        # Validate input
        print(f"📋 Validating input file: {input_path}")
        is_valid, message = validate_input_file(input_path)
        if not is_valid:
            print(f"   ❌ {message}")
            print()
            input("Press Enter to continue...")
            return
        print("   ✓ Input file validated")

        print()
        print("=" * 70)
        print("🚀 Starting processing pipeline")
        print("=" * 70)
        print()

        # Process
        processor = AttendanceProcessor(config)
        processor.process(input_path, output_path)

        print()
        print("=" * 70)
        print(f"✅ Success! Output written to: {output_path}")
        print("=" * 70)

    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
    except ValueError as e:
        print(f"❌ Error: Invalid data - {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    input("Press Enter to continue...")


def main():
    """Main entry point."""
    try:
        while True:
            clear_screen()
            print_header()
            print_menu()

            choice = get_user_choice()

            if choice == '0':
                clear_screen()
                print()
                print("👋 Thank you for using Attendance & CSV Converter Tool!")
                print("   Goodbye!")
                print()
                return 0

            elif choice == '1':
                csv_to_xlsx_workflow()

            elif choice == '2':
                attendance_processor_workflow()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
        return 1

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
