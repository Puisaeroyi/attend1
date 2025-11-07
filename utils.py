"""Utility helper functions"""

from datetime import datetime
from pathlib import Path


def auto_rename_output(path: str) -> str:
    """
    If path exists, rename with timestamp or number suffix

    Examples:
        output.xlsx -> output_20251104_093015.xlsx
        output.xlsx -> output_2.xlsx (if timestamp version exists)

    Args:
        path: Desired output file path

    Returns:
        Available file path (original or renamed)
    """
    p = Path(path)
    if not p.exists():
        return path

    # Try timestamp suffix
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_path = p.parent / f"{p.stem}_{timestamp}{p.suffix}"

    if not new_path.exists():
        print(f"ℹ Output file exists, renamed to: {new_path.name}")
        return str(new_path)

    # Try numeric suffix
    counter = 1
    while True:
        new_path = p.parent / f"{p.stem}_{counter}{p.suffix}"
        if not new_path.exists():
            print(f"ℹ Output file exists, renamed to: {new_path.name}")
            return str(new_path)
        counter += 1
