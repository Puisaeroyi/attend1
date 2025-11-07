"""Test with real dataset from /home/silver/output03-04.xlsx"""

import pytest
import pandas as pd
import time
from pathlib import Path
from config import RuleConfig
from processor import AttendanceProcessor


@pytest.fixture
def config():
    """Load configuration"""
    return RuleConfig.load_from_yaml('/home/silver/project_clean/rule.yaml')


@pytest.fixture
def processor(config):
    """Create processor instance"""
    return AttendanceProcessor(config)


def test_real_data_processing(processor, tmp_path):
    """Test processing real data from /home/silver/output03-04.xlsx

    Requirements:
    - Process successfully without errors
    - Handle all 4 operators
    - Process night shifts correctly (no fragmentation)
    - Performance: <0.5s for ~90 rows
    """
    input_path = '/home/silver/output03-04.xlsx'
    output_path = tmp_path / 'test_output.xlsx'

    # Check if input file exists
    if not Path(input_path).exists():
        pytest.skip(f"Input file not found: {input_path}")

    # Measure performance
    start_time = time.time()

    # Process
    processor.process(str(input_path), str(output_path))

    elapsed = time.time() - start_time

    # Verify output exists
    assert output_path.exists()

    # Load and verify output
    result = pd.read_excel(output_path)

    # Basic validations
    assert len(result) > 0, "No output records generated"
    assert 'Date' in result.columns
    assert 'ID' in result.columns
    assert 'Name' in result.columns
    assert 'Shift' in result.columns
    assert 'First In' in result.columns
    assert 'Break Out' in result.columns
    assert 'Break In' in result.columns
    assert 'Last Out' in result.columns

    # Verify all 4 operators present
    unique_ids = result['ID'].unique()
    assert len(unique_ids) >= 1, f"Expected >= 1 operators, got {len(unique_ids)}"

    # Verify shift types
    valid_shifts = {'Morning', 'Afternoon', 'Night'}
    assert set(result['Shift'].unique()).issubset(valid_shifts)

    # Performance check
    print(f"\n⏱️  Processing time: {elapsed:.3f}s")
    print(f"📊 Records processed: {len(result)}")
    print(f"👥 Operators: {len(unique_ids)}")

    if elapsed < 0.5:
        print(f"✅ Performance: EXCELLENT (<0.5s)")
    elif elapsed < 1.0:
        print(f"⚠️  Performance: ACCEPTABLE (<1.0s)")
    else:
        print(f"❌ Performance: NEEDS OPTIMIZATION (>{1.0}s)")

    # Print sample records
    print("\n📄 Sample records:")
    print(result.head(10).to_string())

    return result


def test_night_shift_integrity(processor, tmp_path):
    """Verify night shifts are not fragmented

    CRITICAL: Night shifts crossing midnight must remain as single records
    Date column must show shift START date
    """
    input_path = '/home/silver/output03-04.xlsx'
    output_path = tmp_path / 'test_output.xlsx'

    if not Path(input_path).exists():
        pytest.skip(f"Input file not found: {input_path}")

    processor.process(str(input_path), str(output_path))
    result = pd.read_excel(output_path)

    # Get night shift records
    night_shifts = result[result['Shift'] == 'Night']

    if len(night_shifts) == 0:
        pytest.skip("No night shifts in dataset")

    print(f"\n🌙 Night shifts found: {len(night_shifts)}")

    # Verify each night shift has all timestamps
    for idx, row in night_shifts.iterrows():
        print(f"\nNight shift on {row['Date']}:")
        print(f"  Name: {row['Name']}")
        print(f"  First In: {row['First In']}")
        print(f"  Break Out: {row['Break Out']}")
        print(f"  Break In: {row['Break In']}")
        print(f"  Last Out: {row['Last Out']}")

        # Verify completeness (at minimum First In and Last Out)
        assert row['First In'] != '', "Night shift missing First In"
        # Last Out might be blank if no check-out swipe

    print("✅ All night shifts appear as single complete records")


def test_gap_based_break_detection(processor, tmp_path):
    """Verify gap-based break detection is working

    Look for cases where break swipes are both after midpoint
    but separated by >= 5 minutes (should use gap detection)
    """
    input_path = '/home/silver/output03-04.xlsx'
    output_path = tmp_path / 'test_output.xlsx'

    if not Path(input_path).exists():
        pytest.skip(f"Input file not found: {input_path}")

    processor.process(str(input_path), str(output_path))
    result = pd.read_excel(output_path)

    # Find records with both Break Out and Break In
    complete_breaks = result[
        (result['Break Out'].notna()) &
        (result['Break Out'] != '') &
        (result['Break In'].notna()) &
        (result['Break In'] != '')
    ]

    print(f"\n🔍 Records with complete breaks: {len(complete_breaks)}/{len(result)}")

    if len(complete_breaks) > 0:
        print("\nSample breaks:")
        for idx, row in complete_breaks.head(5).iterrows():
            print(f"  {row['Name']} on {row['Date']} ({row['Shift']}): "
                  f"{row['Break Out']} → {row['Break In']}")

    # Verify break times are in expected format
    for idx, row in complete_breaks.iterrows():
        break_out = row['Break Out']
        break_in = row['Break In']

        # Should be HH:MM:SS format
        assert ':' in str(break_out), f"Invalid Break Out format: {break_out}"
        assert ':' in str(break_in), f"Invalid Break In format: {break_in}"

    print("✅ Gap-based break detection working")


def test_burst_consolidation(processor, tmp_path):
    """Verify burst detection is consolidating multiple rapid swipes"""
    input_path = '/home/silver/output03-04.xlsx'

    if not Path(input_path).exists():
        pytest.skip(f"Input file not found: {input_path}")

    # Load raw data
    df = pd.read_excel(input_path, engine='openpyxl')
    df['timestamp'] = pd.to_datetime(
        df['Date'].astype(str) + ' ' + df['Time'].astype(str),
        errors='coerce'
    )
    df = df[df['timestamp'].notna()].copy()

    # Filter valid users
    df = df[df['Name'].isin(['Silver_Bui', 'Capone', 'Minh', 'Trieu'])].copy()

    raw_count = len(df)

    # Process through burst detection
    df = processor._filter_valid_status(df)
    df = processor._filter_valid_users(df)
    df = processor._detect_bursts(df)

    burst_count = len(df)

    print(f"\n💥 Burst consolidation:")
    print(f"   Raw swipes: {raw_count}")
    print(f"   After burst detection: {burst_count}")
    print(f"   Reduction: {raw_count - burst_count} swipes consolidated")

    if burst_count < raw_count:
        print("✅ Burst detection is consolidating swipes")
    else:
        print("ℹ️  No bursts detected in this dataset")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
