# Tech Stack - Attendance Data Processor

## Core Language
- **Python 3.9+** (requires datetime.fromisoformat, pandas 2.0 compatibility)

## Primary Dependencies

### Excel Processing
- **openpyxl 3.1+** - Excel file read/write operations
  - Native .xlsx format support
  - Preserves formatting and formulas
  - Optimized read/write modes for performance

### Data Processing
- **pandas 2.0+** - Data manipulation and transformation
  - Efficient datetime operations
  - Vectorized operations for burst detection
  - GroupBy operations for per-employee processing
  - Excel integration via openpyxl engine

### Configuration
- **PyYAML 6.0+** - Parse rule.yaml configuration
  - Safe loading for security
  - Native Python data structure mapping

### CLI Interface
- **argparse** (stdlib) - Command-line argument parsing
  - No external dependency
  - Built-in help generation

### Date/Time Processing
- **datetime** (stdlib) - Time parsing and manipulation
  - Timezone-naive operations (as per data)
  - Time arithmetic and comparisons

### File Operations
- **pathlib** (stdlib) - Modern path handling
  - Cross-platform compatibility
  - Auto-rename logic for output files

## Development Dependencies

### Testing
- **pytest 7.4+** - Test framework
- **pytest-cov** - Code coverage reporting

### Code Quality
- **black** - Code formatting
- **flake8** - Linting
- **mypy** - Type checking (optional, for maintainability)

## Project Structure

```
project1/
├── attendance_processor.py    # Main processing logic
├── main.py                    # CLI entry point
├── rule.yaml                  # Configuration rules
├── requirements.txt           # Python dependencies
├── tests/
│   ├── test_processor.py      # Unit tests
│   └── test_integration.py    # Integration tests with real data
├── docs/
│   ├── tech-stack.md          # This file
│   └── ...                    # Other documentation
└── plans/
    └── research/              # Research reports
```

## Installation Command

```bash
pip install openpyxl>=3.1.0 pandas>=2.0.0 pyyaml>=6.0 pytest>=7.4.0 pytest-cov
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

## Rationale

### Why openpyxl?
- Native .xlsx support without Excel installation
- Can preserve existing formatting if needed
- Well-maintained, stable API
- Better than xlrd (deprecated for .xlsx)

### Why pandas?
- Vectorized operations = 100x faster than row iteration
- Built-in datetime handling with parse_dates
- GroupBy perfectly suits "per employee per day" logic
- Industry standard for data processing

### Why PyYAML?
- rule.yaml is already in YAML format
- More readable than JSON for configuration
- Native Python type mapping

### Why stdlib argparse?
- No external dependency
- Sufficient for simple CLI (input, output paths)
- Auto-generates --help documentation

## Performance Expectations

For 90-row dataset (as in output1.xlsx):
- **Load time**: <0.1s
- **Processing time**: <0.2s
- **Write time**: <0.1s
- **Total**: <0.5s

For 10,000-row dataset:
- **Processing time**: 1-2s (with optimizations)

## Python Version Requirement

Minimum: **Python 3.9**

Reasons:
- `datetime.fromisoformat()` improvements
- `dict` merge operator `|` (code clarity)
- pandas 2.0 requires Python 3.9+
- Type hint improvements (optional but recommended)

## Operating System Support

✓ Linux (primary, as per WSL2 environment)
✓ macOS
✓ Windows (native or WSL2)

Cross-platform via pathlib and pandas.
