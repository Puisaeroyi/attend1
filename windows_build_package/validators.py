"""Input validation functions"""

from pathlib import Path
from typing import Tuple, List
import pandas as pd


def validate_input_file(path: str) -> Tuple[bool, str]:
    """Validate input Excel file exists and is readable

    Returns:
        (is_valid, error_message)
    """
    p = Path(path)

    if not p.exists():
        return False, f"File not found: {path}"

    if p.suffix.lower() not in ['.xlsx', '.xls']:
        return False, f"Invalid file type (expected .xlsx or .xls): {path}"

    try:
        # Try to read just the header
        pd.read_excel(path, nrows=0, engine='openpyxl')
        return True, ""
    except Exception as e:
        return False, f"Cannot read file: {str(e)}"


def validate_excel_columns(df: pd.DataFrame, required: List[str]) -> Tuple[bool, str]:
    """Check required columns exist in DataFrame

    Returns:
        (is_valid, error_message)
    """
    missing = set(required) - set(df.columns)
    if missing:
        return False, f"Missing required columns: {', '.join(sorted(missing))}"
    return True, ""


def validate_yaml_config(config_path: str) -> Tuple[bool, str]:
    """Validate rule.yaml exists and can be loaded

    Returns:
        (is_valid, error_message)
    """
    from config import RuleConfig

    p = Path(config_path)
    if not p.exists():
        return False, f"Configuration file not found: {config_path}"

    try:
        RuleConfig.load_from_yaml(config_path)
        return True, ""
    except Exception as e:
        return False, f"Invalid rule.yaml: {str(e)}"
