# User Guide - Attendance & CSV Converter Tool (GUI)

## Overview

The Attendance & CSV Converter Tool v3.0.0 is a user-friendly Windows application that combines two powerful tools:
- **CSV to XLSX Converter** - Extract specific columns from CSV files and convert to Excel format
- **Attendance Data Processor** - Transform biometric attendance logs into structured attendance records

## Installation

### System Requirements
- Windows 10 or Windows 11 (64-bit)
- No Python installation required
- 50MB free disk space

### Installation Steps
1. Download `AttendanceProcessor.exe` from the provided location
2. Save the file to your desired location (Desktop, Documents, etc.)
3. Double-click the file to launch the application

**No installation required!** The application is completely self-contained.

## Getting Started

When you launch the application, you'll see the main window with two tabs:

```
┌─────────────────────────────────────────────────────────────┐
│              Attendance & CSV Converter Tool                │
│                    Version 3.0.0 - GUI Edition             │
├─────────────────────────────────────────────────────────────┤
│  [CSV Converter]  [Attendance Processor]                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Tab Content Area                         │
│                                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Ready]                                                     │
└─────────────────────────────────────────────────────────────┘
```

## CSV Converter

### Purpose
Convert CSV files to Excel format while extracting specific columns (ID, Name, Date, Time, Type, Status).

### Step-by-Step Instructions

1. **Launch the application** and select the **"CSV Converter"** tab

2. **Select Input CSV File:**
   - Click the **"Browse..."** button next to "Input CSV File"
   - Navigate to your CSV file and select it
   - The file path will appear in the input field

3. **Choose Output Location:**
   - Click the **"Browse..."** button next to "Output XLSX File"
   - Navigate to where you want to save the Excel file
   - Enter a filename and click **"Save"**

4. **Convert the File:**
   - Click the **"Convert"** button
   - Watch the status area for progress updates
   - When complete, you'll see a success message with the number of rows converted

5. **Check the Results:**
   - Open the output Excel file to verify the conversion
   - The file should contain columns: ID, Name, Date, Time, Type, Status

### What It Does
- Extracts columns 0, 1, 2, 3, 4, and 6 from the CSV file
- Renames them to: ID, Name, Date, Time, Type, Status
- Saves as an Excel (.xlsx) file
- Provides detailed progress feedback

## Attendance Data Processor

### Purpose
Process raw biometric attendance data into clean, structured attendance records with shift detection and break time analysis.

### Step-by-Step Instructions

1. **Launch the application** and select the **"Attendance Processor"** tab

2. **Select Input Excel File:**
   - Click the **"Browse..."** button next to "Input Excel File"
   - Select your biometric data file (.xlsx or .xls format)
   - The file should contain columns: ID, Name, Date, Time, Type, Status

3. **Choose Output Location:**
   - Click the **"Browse..."** button next to "Output Excel File"
   - Select where to save the processed attendance report
   - Enter a filename and click **"Save"**

4. **Configure Processing Settings:**
   - The config file field defaults to "rule.yaml" (bundled with the application)
   - For advanced users: Click **"Browse..."** to use a custom configuration file
   - Click **"Default"** to reset to the built-in configuration

5. **Process the Data:**
   - Click the **"Process"** button
   - Watch the processing log for real-time updates:
     ```
     🔧 Loading configuration: rule.yaml
        ✓ Loaded config: 3 shifts, 4 valid users
     📖 Loading input: data.xlsx
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
     💾 Writing output: processed.xlsx
     ✅ Success! Output written to: processed.xlsx
     ```

6. **Review the Results:**
   - Open the output Excel file
   - The processed file contains structured attendance records with columns:
     - Date, ID, Name, Shift, Check In Record, Break Time Out, Break Time In, Check Out Record

### Advanced Features
- **Burst Detection:** Groups multiple swipes within 2 minutes
- **Shift Detection:** Handles night shifts crossing midnight
- **Break Detection:** Automatically finds break times using gap analysis
- **User Filtering:** Processes only configured valid users
- **Error Handling:** Skips invalid data with warnings

## Menu Bar Functions

### File Menu
- **Exit:** Close the application

### Tools Menu
- **Clear All Logs:** Clear all log text areas in both tabs

### Help Menu
- **Help:** Show this quick start guide
- **About:** View application information and version

## Keyboard Shortcuts
- **Ctrl+Q:** Exit the application
- **F1:** Show help dialog
- **Alt+F4:** Exit the application (Windows standard)

## Status Bar
The status bar at the bottom of the window shows:
- Current application status
- Timestamped status updates
- Tab switching notifications

## Troubleshooting

### Common Issues

#### "File not found" Error
**Cause:** The input file doesn't exist or has been moved
**Solution:**
- Check that the input file path is correct
- Ensure the file is not currently open in Excel
- Use the "Browse..." button to reselect the file

#### "Permission denied" Error
**Cause:** Cannot write to the output location
**Solution:**
- Close the output file if it's open in Excel
- Choose a different output location
- Ensure you have write permissions to the folder

#### "Invalid file format" Error
**Cause:** Wrong file type selected
**Solution:**
- CSV Converter: Select .csv files only
- Attendance Processor: Select .xlsx or .xls files only
- Check file extensions are correct

#### Processing takes too long
**Cause:** Large datasets or complex data
**Solution:**
- Large files (10,000+ rows) may take 10-20 seconds
- Watch the processing log for progress
- The application remains responsive during processing

#### Application won't open
**Cause:** System compatibility issues
**Solution:**
- Ensure you're using Windows 10 or 11
- Try right-clicking and selecting "Run as administrator"
- Contact IT support if the issue persists

### Error Messages

#### Validation Errors
- **"Please select input/output files"**: Use the Browse buttons to select files
- **"Input and output files cannot be the same"**: Choose different locations
- **"Output directory not found"**: Select a valid output folder

#### Processing Errors
- **"Config file not found"**: Ensure rule.yaml is in the same folder as the .exe
- **"No valid records to process"**: Check that your data contains valid users and success status
- **"Configuration error"**: The rule.yaml file may be corrupted

## File Formats

### CSV Converter Input Format
The CSV file should have at least 7 columns with data in columns:
- Column 0: User ID
- Column 1: User Name
- Column 2: Date
- Column 3: Time
- Column 4: Type (optional)
- Column 5: (ignored)
- Column 6: Status

### Attendance Processor Input Format
The Excel file should contain these columns:
| Column | Description | Example |
|--------|-------------|---------|
| ID | User ID (numeric) | 38 |
| Name | Username | Silver_Bui |
| Date | Date of swipe | 2025.11.02 |
| Time | Time of swipe | 06:30:15 |
| Type | Swipe type (optional) | F1 |
| Status | Swipe status | Success |

### Output Format
Both tools output Excel files (.xlsx) with processed data in organized formats suitable for reporting and analysis.

## Tips and Best Practices

### Before Processing
1. **Backup your data** - Always keep original files unchanged
2. **Check file formats** - Ensure correct file extensions (.csv, .xlsx)
3. **Close Excel files** - Don't have input/output files open in Excel
4. **Free disk space** - Ensure adequate space for output files

### During Processing
1. **Watch the progress log** - Monitor for any warnings or errors
2. **Be patient** - Large files may take several minutes
3. **Don't close the application** - Wait for processing to complete

### After Processing
1. **Verify results** - Open output files to check the data
2. **Check for warnings** - Review any warning messages in the log
3. **Save configurations** - Note any custom settings used

## Support

For technical assistance:
1. Check this user guide for common solutions
2. Review the processing log for error details
3. Contact IT support with:
   - Error messages
   - Input file samples (if possible)
   - Steps to reproduce the issue

---

**Version:** 3.0.0 (GUI Edition)
**Last Updated:** 2025-11-06
**Platform:** Windows 10/11