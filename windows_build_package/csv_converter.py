"""CSV to XLSX converter module.

Extracts specific columns from CSV files and converts them to XLSX format
with custom column names.
"""

import csv
from pathlib import Path
import pandas as pd


# Column indices to extract from CSV (0-indexed)
COLUMN_INDICES = [0, 1, 2, 3, 4, 6]

# Column names for output XLSX
COLUMN_NAMES = ['ID', 'Name', 'Date', 'Time', 'Type', 'Status']


def validate_input_file(file_path: str) -> None:
    """Validate input CSV file exists and has correct extension.

    Args:
        file_path: Path to input CSV file

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file extension is not .csv
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if path.suffix.lower() != '.csv':
        raise ValueError(f"Input file must be CSV format, got: {path.suffix}")


def validate_output_path(file_path: str) -> None:
    """Validate output XLSX path and parent directory.

    Args:
        file_path: Path to output XLSX file

    Raises:
        ValueError: If file extension is not .xlsx
        FileNotFoundError: If parent directory doesn't exist
    """
    path = Path(file_path)

    if path.suffix.lower() != '.xlsx':
        raise ValueError(f"Output file must be XLSX format, got: {path.suffix}")

    if not path.parent.exists():
        raise FileNotFoundError(f"Output directory doesn't exist: {path.parent}")


def validate_column_count(input_path: str) -> None:
    """Validate CSV has enough columns for extraction.

    Args:
        input_path: Path to input CSV file

    Raises:
        ValueError: If CSV doesn't have enough columns
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            first_row = next(reader)
        except StopIteration:
            raise pd.errors.EmptyDataError("CSV file is empty")

        max_col_idx = max(COLUMN_INDICES)
        if len(first_row) <= max_col_idx:
            raise ValueError(
                f"CSV has only {len(first_row)} columns, "
                f"but column index {max_col_idx} (7th column) is required. "
                f"Need at least {max_col_idx + 1} columns."
            )


def convert_csv_to_xlsx(input_path: str, output_path: str) -> int:
    """Convert CSV to XLSX with column extraction.

    Args:
        input_path: Path to input CSV file
        output_path: Path to output XLSX file

    Returns:
        Number of rows processed

    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If column indices exceed CSV columns
        pd.errors.EmptyDataError: If CSV is empty
        pd.errors.ParserError: If CSV is malformed
        PermissionError: If cannot write output file
    """
    # Validate column count before processing
    validate_column_count(input_path)

    # Read CSV with specific columns
    df = pd.read_csv(input_path, usecols=COLUMN_INDICES)

    # Rename columns
    df.columns = COLUMN_NAMES

    # Write to XLSX
    df.to_excel(output_path, index=False, engine='openpyxl')

    return len(df)
