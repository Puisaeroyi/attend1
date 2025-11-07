# Attendance Data Processor - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding Your Data](#understanding-your-data)
3. [Running the Processor](#running-the-processor)
4. [Customizing Rules](#customizing-rules)
5. [Interpreting Results](#interpreting-results)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

---

## Getting Started

### Prerequisites

- Python 3.9 or higher installed
- Raw biometric log data in Excel format (.xlsx)
- Basic command line knowledge

### Installation Steps

1. **Navigate to project directory**:
   ```bash
   cd /path/to/project1
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   ```

3. **Activate virtual environment**:
   - **Linux/Mac**: `source venv/bin/activate`
   - **Windows**: `venv\Scripts\activate`

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify installation**:
   ```bash
   python main.py --help
   ```

   You should see the help message with usage instructions.

---

## Understanding Your Data

### Input Data Requirements

Your Excel file must have these columns (case-sensitive):

| Column | Required | Description | Example Values |
|--------|----------|-------------|----------------|
| **ID** | Yes | Numeric user ID | 38, 7072503 |
| **Name** | Yes | Username (must match rule.yaml) | Silver_Bui, Capone |
| **Date** | Yes | Swipe date | 2025.11.02, 2025-11-02 |
| **Time** | Yes | Swipe time | 06:30:15, 14:00:00 |
| **Status** | Yes | Swipe status | Success, Failure |
| **Type** | No | Swipe type (optional) | F1, Card |

### Valid Users

Only users defined in `rule.yaml` will be processed. Users not in the mapping will be filtered out with a warning.

**Example** from `rule.yaml`:
```yaml
operators:
  user_mapping:
    Silver_Bui:
      output_name: "Bui Duc Toan"
      output_id: "TPL0001"
    Capone:
      output_name: "Pham Tan Phat"
      output_id: "TPL0002"
```

### Common Data Issues

❌ **ID = 0 or blank**: Filtered out automatically
❌ **Status ≠ "Success"**: Filtered out automatically
❌ **Unknown username**: Filtered out with warning
❌ **Invalid date/time**: Skipped with warning

---

## Running the Processor

### Basic Usage

```bash
python main.py input.xlsx output.xlsx
```

**Example**:
```bash
python main.py /home/silver/output1.xlsx processed_attendance.xlsx
```

### With Custom Configuration

```bash
python main.py input.xlsx output.xlsx --config custom_rules.yaml
```

### Understanding the Output

When you run the processor, you'll see:

```
🔧 Loading configuration: rule.yaml
   ✓ Loaded config: 3 shifts, 4 valid users
📋 Validating input file: /home/silver/output1.xlsx
   ✓ Input file validated

============================================================
🚀 Starting processing pipeline
============================================================

📖 Loading input: /home/silver/output1.xlsx
   Loaded 90 records
🔍 Filtering by status: Success
   90 records after status filter
👥 Filtering valid users
   ⚠ Filtered 60 invalid user records
   30 records after user filter
🔄 Detecting bursts (≤2min)
   28 events after burst consolidation
📅 Classifying shifts
⏰ Extracting attendance events
   6 attendance records generated
💾 Writing output: processed_attendance.xlsx
✅ Processing complete!

============================================================
✅ Success! Output written to: processed_attendance.xlsx
============================================================
```

**What each step means**:

1. **Loading input**: Reads Excel file, combines date+time
2. **Filtering by status**: Keeps only "Success" swipes
3. **Filtering valid users**: Keeps only employees in rule.yaml
4. **Detecting bursts**: Consolidates swipes ≤2min apart
5. **Classifying shifts**: Determines shift (A/B/C) per user/day
6. **Extracting events**: Finds First In, Break Out, Break In, Last Out
7. **Writing output**: Creates formatted Excel file

---

## Customizing Rules

### Editing rule.yaml

The `rule.yaml` file controls all processing logic.

#### 1. Adding a New Employee

```yaml
operators:
  user_mapping:
    NewUsername:
      output_name: "Full Legal Name"
      output_id: "TPL0005"  # Unique ID
```

#### 2. Changing Burst Threshold

Default is 2 minutes:
```yaml
burst_logic:
  definition: "Swipes within <= 3 minutes are grouped"  # Changed to 3
```

#### 3. Adjusting Shift Times

Example: Change morning shift check-in window:
```yaml
shift_structure:
  shifts:
    A:
      check_in_search_range: "06:00-07:00"  # Changed from 05:30-06:35
```

#### 4. Modifying Break Detection

Example: Change afternoon shift break midpoint:
```yaml
break_detection:
  shifts:
    B:
      midpoint_checkpoint: "18:30"  # Changed from 18:15
```

### Important Notes

⚠️ **After editing rule.yaml**:
- Maintain proper YAML indentation (2 spaces, no tabs)
- Test with a small dataset first
- Validate times are in "HH:MM" or "HH:MM:SS" format

---

## Interpreting Results

### Output File Format

The processor creates an Excel file with these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Date** | Calendar date | 2025-11-02 |
| **ID** | Employee ID from mapping | TPL0001 |
| **Name** | Full name from mapping | Bui Duc Toan |
| **Shift** | Shift type | Morning, Afternoon, Night |
| **First In** | Check-in time (HH:MM:SS) | 06:00:15 |
| **Break Out** | Break start time | 10:00:30 |
| **Break In** | Break return time | 10:30:45 |
| **Last Out** | Check-out time | 14:00:00 |

### Understanding Empty Fields

Empty fields are **normal** and indicate:

- **Empty First In**: No swipe in check-in window
- **Empty Break Out**: No swipe before break midpoint
- **Empty Break In**: No swipe after break midpoint
- **Empty Last Out**: No swipe in check-out window

### Example Output

```
Date       | ID      | Name            | Shift     | First In | Break Out | Break In | Last Out
2025-11-02 | TPL0001 | Bui Duc Toan    | Morning   | 06:00:15 |           |          |
2025-11-02 | TPL0002 | Pham Tan Phat   | Afternoon | 14:00:30 | 18:05:00  | 18:35:20 | 21:59:50
2025-11-02 | TPL0003 | Mac Le Duc Minh | Morning   | 05:58:14 |           |          | 13:53:32
```

**Interpretation**:
- **Bui Duc Toan**: Checked in but no other swipes recorded
- **Pham Tan Phat**: Complete attendance with break
- **Mac Le Duc Minh**: Worked full shift without break swipes

---

## Troubleshooting

### Problem: "Configuration file not found"

**Cause**: `rule.yaml` not in current directory

**Solutions**:
1. Run from project directory: `cd /path/to/project1`
2. Specify full path: `--config /full/path/to/rule.yaml`
3. Copy rule.yaml to current directory

### Problem: "Missing required columns"

**Cause**: Input Excel missing ID, Name, Date, Time, or Status

**Solution**: Verify input file has all required columns with correct names (case-sensitive)

### Problem: "No valid records to process"

**Cause**: All rows filtered out (wrong usernames or all non-Success)

**Solutions**:
1. Check usernames match `rule.yaml`
2. Verify Status column has "Success" values
3. Review filtering warnings in output

### Problem: "Invalid time format"

**Cause**: Times in rule.yaml not in HH:MM or HH:MM:SS format

**Solution**: Fix rule.yaml times:
```yaml
# Wrong
check_in_search_range: "6:00-6:35"

# Correct
check_in_search_range: "06:00-06:35"
```

### Problem: Output file already exists

**Not a problem!** The processor auto-renames:
- `output.xlsx` → `output_20251104_093015.xlsx`

### Problem: "YAML parser error"

**Cause**: Invalid YAML syntax (usually indentation)

**Solution**:
1. Use 2 spaces for indentation (no tabs)
2. Ensure colons followed by space: `key: value`
3. Quote strings with special chars: `"06:00-14:00"`

---

## Advanced Usage

### Processing Multiple Files

```bash
# Process all Excel files in a directory
for file in /path/to/inputs/*.xlsx; do
  python main.py "$file" "processed_$(basename $file)"
done
```

### Batch Processing Script

Create `batch_process.sh`:
```bash
#!/bin/bash
for month in Jan Feb Mar; do
  python main.py "attendance_${month}.xlsx" "processed_${month}.xlsx"
done
```

### Testing with Sample Data

Before processing production data:

```bash
# Use first 20 rows only (manual creation)
# Or use provided test fixtures
pytest tests/test_integration.py -v
```

### Performance Tips

- **Small datasets (<1000 rows)**: Standard mode (current setup)
- **Large datasets (>10000 rows)**: Consider chunking or streaming

### Viewing Processing Details

Add verbose logging (future enhancement):
```bash
python main.py input.xlsx output.xlsx --verbose
```

---

## FAQ

**Q: Can I process multiple shifts for the same person on the same day?**
A: Yes! Each shift creates a separate output row.

**Q: What happens if someone checks in for Shift A but works into Shift B?**
A: They're assigned to Shift A (based on first check-in). All swipes processed for that shift.

**Q: Can I change the output column names?**
A: Currently fixed. Future enhancement could add customizable output format.

**Q: How do I handle daylight saving time?**
A: The processor uses naive datetimes (no timezone). Ensure input data is in local time.

**Q: Can I export to CSV instead of Excel?**
A: Not currently. Use Excel to save as CSV, or contact dev team for CSV export feature.

**Q: What if I have more than 4 employees?**
A: Add them to `rule.yaml` user_mapping with unique IDs.

---

## Getting Help

1. **Check documentation**: `README.md`, this guide, `docs/tech-stack.md`
2. **Run tests**: `pytest tests/ -v` to verify setup
3. **Check logs**: Review terminal output for warnings
4. **Contact support**: Reach out to development team with:
   - Input file sample (5-10 rows)
   - Error message screenshot
   - rule.yaml configuration

---

## Best Practices

✅ **Do**:
- Test with sample data first
- Keep rule.yaml backed up
- Review warnings in output
- Verify output spot-checks manually

❌ **Don't**:
- Edit rule.yaml without testing
- Ignore filtering warnings
- Process without validating input format
- Skip virtual environment activation

---

## Quick Reference

### Common Commands

```bash
# Standard processing
python main.py input.xlsx output.xlsx

# Custom config
python main.py input.xlsx output.xlsx --config rules.yaml

# Run tests
pytest tests/ -v

# Activate venv (Linux/Mac)
source venv/bin/activate

# Activate venv (Windows)
venv\Scripts\activate
```

### Key Files

- `main.py` - CLI entry point
- `processor.py` - Processing logic
- `rule.yaml` - Business rules
- `README.md` - Project overview
- `docs/user-guide.md` - This guide

### Support Files

- `requirements.txt` - Dependencies
- `tests/` - Test suite
- `.gitignore` - Version control ignore patterns

---

**Version**: 1.0.0
**Last Updated**: 2025-11-04
**Author**: Development Team
