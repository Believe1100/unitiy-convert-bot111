import re
from typing import Optional, Tuple

# ---------- Unit Definitions ----------
# Base units: meter, kilogram, Celsius (for internal conversions)
LENGTH_UNITS = {
    "meter": 1.0,
    "kilometer": 1000.0,
    "centimeter": 0.01,
    "mile": 1609.344,
    "foot": 0.3048,
    "inch": 0.0254,
}

WEIGHT_UNITS = {
    "kilogram": 1.0,
    "gram": 0.001,
    "pound": 0.453592,
    "ounce": 0.0283495,
}

# Temperature units are handled by formulas, not factors.
TEMPERATURE_UNITS = {"celsius", "fahrenheit", "kelvin"}

# Map category to its unit dict
CATEGORY_UNITS = {
    "length": LENGTH_UNITS,
    "weight": WEIGHT_UNITS,
    "temperature": TEMPERATURE_UNITS,  # special case
}

# Human‑friendly labels for display
UNIT_LABELS = {
    "meter": "Meter",
    "kilometer": "Kilometer",
    "centimeter": "Centimeter",
    "mile": "Mile",
    "foot": "Foot",
    "inch": "Inch",
    "kilogram": "Kilogram",
    "gram": "Gram",
    "pound": "Pound",
    "ounce": "Ounce",
    "celsius": "Celsius",
    "fahrenheit": "Fahrenheit",
    "kelvin": "Kelvin",
}

# Aliases for parsing user input (short forms, plurals, etc.)
UNIT_ALIASES = {
    # Length
    "m": "meter",
    "meters": "meter",
    "km": "kilometer",
    "kilometers": "kilometer",
    "cm": "centimeter",
    "centimeters": "centimeter",
    "mi": "mile",
    "miles": "mile",
    "ft": "foot",
    "feet": "foot",
    "in": "inch",
    "inches": "inch",
    # Weight
    "kg": "kilogram",
    "kilograms": "kilogram",
    "g": "gram",
    "grams": "gram",
    "lb": "pound",
    "lbs": "pound",
    "pounds": "pound",
    "oz": "ounce",
    "ounces": "ounce",
    # Temperature
    "c": "celsius",
    "celsius": "celsius",
    "f": "fahrenheit",
    "fahrenheit": "fahrenheit",
    "k": "kelvin",
    "kelvin": "kelvin",
}


def _get_category(unit: str) -> Optional[str]:
    """Return the category ('length', 'weight', 'temperature') for a given unit."""
    if unit in LENGTH_UNITS:
        return "length"
    if unit in WEIGHT_UNITS:
        return "weight"
    if unit in TEMPERATURE_UNITS:
        return "temperature"
    return None


def _convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """Convert length using base unit (meter)."""
    base = value * LENGTH_UNITS[from_unit]
    return base / LENGTH_UNITS[to_unit]


def _convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    """Convert weight using base unit (kilogram)."""
    base = value * WEIGHT_UNITS[from_unit]
    return base / WEIGHT_UNITS[to_unit]


def _convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature using formulas."""
    # Convert to Celsius first
    if from_unit == "celsius":
        celsius = value
    elif from_unit == "fahrenheit":
        celsius = (value - 32) * 5.0 / 9.0
    elif from_unit == "kelvin":
        celsius = value - 273.15
    else:
        raise ValueError(f"Unknown temperature unit: {from_unit}")

    # Convert from Celsius to target
    if to_unit == "celsius":
        return celsius
    elif to_unit == "fahrenheit":
        return celsius * 9.0 / 5.0 + 32
    elif to_unit == "kelvin":
        return celsius + 273.15
    else:
        raise ValueError(f"Unknown temperature unit: {to_unit}")


def convert_units(value: float, src: str, dst: str) -> float:
    """
    Convert a numeric value from one unit to another.
    Raises ValueError if units are incompatible or unknown.
    """
    src = src.lower()
    dst = dst.lower()
    # Resolve aliases
    src = UNIT_ALIASES.get(src, src)
    dst = UNIT_ALIASES.get(dst, dst)

    cat_src = _get_category(src)
    cat_dst = _get_category(dst)
    if not cat_src or not cat_dst:
        raise ValueError(f"Unknown unit(s): {src}, {dst}")
    if cat_src != cat_dst:
        raise ValueError(f"Incompatible categories: {cat_src} vs {cat_dst}")

    if cat_src == "length":
        return _convert_length(value, src, dst)
    elif cat_src == "weight":
        return _convert_weight(value, src, dst)
    else:  # temperature
        return _convert_temperature(value, src, dst)


def parse_inline_query(text: str) -> Optional[Tuple[float, str, str]]:
    """
    Parse user‑typed commands like:
      - "10 km to miles"
      - "70 kg lbs"  (without "to")
    Returns (value, from_unit, to_unit) if successful, else None.
    """
    text = text.strip().lower()
    # Try with explicit "to"
    pattern_with_to = r"^([\d.]+)\s*([a-z]+)\s+to\s+([a-z]+)$"
    match = re.match(pattern_with_to, text)
    if match:
        val_str, src_raw, dst_raw = match.groups()
        try:
            val = float(val_str)
        except ValueError:
            return None
        src = UNIT_ALIASES.get(src_raw, src_raw)
        dst = UNIT_ALIASES.get(dst_raw, dst_raw)
        # Verify both units exist and are compatible
        if _get_category(src) and _get_category(dst) and _get_category(src) == _get_category(dst):
            return val, src, dst
        return None

    # Try without "to": e.g., "70 kg lbs"
    pattern_no_to = r"^([\d.]+)\s*([a-z]+)\s+([a-z]+)$"
    match = re.match(pattern_no_to, text)
    if match:
        val_str, src_raw, dst_raw = match.groups()
        try:
            val = float(val_str)
        except ValueError:
            return None
        src = UNIT_ALIASES.get(src_raw, src_raw)
        dst = UNIT_ALIASES.get(dst_raw, dst_raw)
        if _get_category(src) and _get_category(dst) and _get_category(src) == _get_category(dst):
            return val, src, dst

    return None
