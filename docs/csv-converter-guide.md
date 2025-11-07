# CSV to XLSX Converter Guide

## Overview

The CSV to XLSX Converter extracts specific columns from CSV files and converts them to Excel format with renamed columns.

## Features

- **Column Extraction**: Selects columns at indices [0, 1, 2, 3, 4, 6] from CSV
- **Column Renaming**: Output columns named: ID, Name, Date, Time, Type, Status
- **Validation**: Comprehensive input/output validation
- **Error Handling**: Clear error messages for all failure modes
- **Performance**: Fast processing even for large files

## Usage

### Through Menu Interface

1. Run `python main.py`
2. Select option `1` for CSV to XLSX Converter
3. Enter input CSV file path
4. Enter output XLSX file path
5. Tool will validate and convert

### Programmatic Usage

```python
import csv_converter

# Convert CSV to XLSX
row_count = csv_converter.convert_csv_to_xlsx(
    input_path='/path/to/input.csv',
    output_path='/path/to/output.xlsx'
)

print(f"Converted {row_count} rows")
```

## Input Requirements

- **File Format**: CSV with comma-separated values
- **Minimum Columns**: 7 columns (indices 0-6 must exist)
- **Encoding**: UTF-8
- **Column Mapping**:
  - Index 0 → ID
  - Index 1 → Name
  - Index 2 → Date
  - Index 3 → Time
  - Index 4 → Type
  - Index 6 → Status (note: skips index 5)

## Example

**Input CSV** (`input.csv`):
```
38,Silver_Bui,2025.11.05,09:00:15,F1,unused,Success
42,John_Doe,2025.11.05,10:30:22,F2,unused,Success
```

**Output XLSX** (`output.xlsx`):
| ID | Name | Date | Time | Type | Status |
|----|------|------|------|------|--------|
| 38 | Silver_Bui | 2025.11.05 | 09:00:15 | F1 | Success |
| 42 | John_Doe | 2025.11.05 | 10:30:22 | F2 | Success |

## Error Handling

### File Not Found
```
❌ Error: Input file not found: /path/to/file.csv
```

### Invalid Extension
```
❌ Error: Input file must be CSV format, got: .txt
❌ Error: Output file must be XLSX format, got: .xls
```

### Insufficient Columns
```
❌ Error: CSV has only 5 columns, but column index 6 (7th column) is required.
         Need at least 7 columns.
```

### Empty CSV
```
❌ Error: CSV file is empty
```

### Permission Denied
```
❌ Error: Permission denied - Cannot write to /protected/output.xlsx
```

## Performance

Expected processing times:
- Small files (<1K rows): <1 second
- Medium files (1K-10K rows): 1-5 seconds
- Large files (10K-100K rows): 5-30 seconds

## API Reference

### `convert_csv_to_xlsx(input_path, output_path)`

Convert CSV to XLSX with column extraction.

**Parameters:**
- `input_path` (str): Path to input CSV file
- `output_path` (str): Path to output XLSX file

**Returns:**
- `int`: Number of rows processed

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `ValueError`: If column indices exceed CSV columns
- `pd.errors.EmptyDataError`: If CSV is empty
- `pd.errors.ParserError`: If CSV is malformed
- `PermissionError`: If cannot write output file

**Example:**
```python
row_count = csv_converter.convert_csv_to_xlsx(
    '/home/user/data.csv',
    '/home/user/output.xlsx'
)
```

### `validate_input_file(file_path)`

Validate input CSV file exists and has correct extension.

**Parameters:**
- `file_path` (str): Path to input CSV file

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file extension is not .csv

### `validate_output_path(file_path)`

Validate output XLSX path and parent directory.

**Parameters:**
- `file_path` (str): Path to output XLSX file

**Raises:**
- `ValueError`: If file extension is not .xlsx
- `FileNotFoundError`: If parent directory doesn't exist

### `validate_column_count(input_path)`

Validate CSV has enough columns for extraction.

**Parameters:**
- `input_path` (str): Path to input CSV file

**Raises:**
- `ValueError`: If CSV doesn't have enough columns

## Integration with Main Application

The CSV converter is integrated into the main menu application (`main.py`).

When user selects option 1, the workflow:
1. Prompts for input CSV file path
2. Validates input file exists and is CSV format
3. Prompts for output XLSX file path
4. Validates output path and parent directory
5. Performs conversion
6. Displays success message with row count

## Troubleshooting

### Large Files Are Slow

For very large files (>100K rows), consider:
- Processing in chunks
- Using more efficient CSV readers
- Increasing system memory

### Encoding Issues

If you encounter encoding errors:
```python
# Specify encoding explicitly
df = pd.read_csv(input_path, usecols=COLUMN_INDICES, encoding='utf-8')
```

### Memory Issues

For extremely large files (>1GB):
- Process in chunks using `pd.read_csv(chunksize=10000)`
- Consider using dask for out-of-core processing
- Increase system swap/virtual memory

## Best Practices

1. **Always validate inputs** before processing
2. **Handle errors gracefully** with clear user messages
3. **Use absolute paths** to avoid path resolution issues
4. **Check disk space** before writing large outputs
5. **Test with sample data** before processing production files

## Version History

**v2.1.0** (2025-11-05)
- Integrated into unified menu application
- Added interactive workflow
- Improved error messages

**v1.0.0** (Initial)
- Basic CSV to XLSX conversion
- Column extraction and renaming
- Validation and error handling
