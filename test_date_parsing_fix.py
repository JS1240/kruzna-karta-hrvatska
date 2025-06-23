#!/usr/bin/env python3
"""Test the fixed date parsing function."""

import re
from datetime import date

def test_fixed_date_parsing():
    """Test the corrected date parsing logic."""
    
    # Replicate the fixed function
    def parse_infozagreb_date_fixed(date_str: str):
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        infozagreb_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',                    # DD.MM.YYYY (Croatian standard)
            r'(\d{4})-(\d{1,2})-(\d{1,2})',                     # YYYY-MM-DD (ISO format)
            r'(\d{1,2})\s+(siječnja|veljače|ožujka|travnja|svibnja|lipnja|srpnja|kolovoza|rujna|listopada|studenoga|prosinca)\s+(\d{4})',  # Croatian months
            r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',  # English months
            r'(\d{1,2})\.(\d{1,2})\.',                          # DD.MM. (current year)
            r'(\d{1,2})/(\d{1,2})/(\d{4})',                     # MM/DD/YYYY or DD/MM/YYYY
        ]
        
        croatian_months = {
            'siječnja': 1, 'veljače': 2, 'ožujka': 3, 'travnja': 4,
            'svibnja': 5, 'lipnja': 6, 'srpnja': 7, 'kolovoza': 8,
            'rujna': 9, 'listopada': 10, 'studenoga': 11, 'prosinca': 12
        }
        
        english_months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for i, pattern in enumerate(infozagreb_patterns):
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if i == 2:  # Croatian months pattern
                        day, month_name, year = match.groups()
                        month_num = croatian_months.get(month_name.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif i == 3:  # English months pattern
                        day, month_name, year = match.groups()
                        month_num = english_months.get(month_name.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif pattern.endswith(r'(\d{4})'):  # Full date with year
                        if '.' in pattern:  # DD.MM.YYYY
                            day, month, year = match.groups()
                            return date(int(year), int(month), int(day))
                        elif '-' in pattern:  # YYYY-MM-DD
                            year, month, day = match.groups()
                            return date(int(year), int(month), int(day))
                        elif '/' in pattern:  # DD/MM/YYYY (assume European format)
                            day, month, year = match.groups()
                            return date(int(year), int(month), int(day))
                    elif pattern.endswith(r'\.'):  # DD.MM. (assume current year)
                        day, month = match.groups()
                        current_year = date.today().year
                        parsed_date = date(current_year, int(month), int(day))
                        # If date is in the past, assume next year
                        if parsed_date < date.today():
                            parsed_date = date(current_year + 1, int(month), int(day))
                        return parsed_date
                        
                except (ValueError, TypeError) as e:
                    print(f"Date parsing failed for pattern {pattern} with data {match.groups()}: {e}")
                    continue
        
        return None
    
    # Test cases
    print("=== Testing Fixed Date Parsing ===")
    
    test_cases = [
        # (input, expected_result)
        ("15.3.2024", date(2024, 3, 15)),
        ("2024-03-15", date(2024, 3, 15)),
        ("15 ožujka 2024", date(2024, 3, 15)),
        ("15 march 2024", date(2024, 3, 15)),
        ("25 prosinca 2024", date(2024, 12, 25)),
        ("25 december 2024", date(2024, 12, 25)),
        ("15/3/2024", date(2024, 3, 15)),
        ("invalid date", None),
        ("", None),
    ]
    
    all_passed = True
    for test_input, expected in test_cases:
        result = parse_infozagreb_date_fixed(test_input)
        
        if result == expected:
            print(f"✓ '{test_input}' -> {result}")
        else:
            print(f"✗ '{test_input}' -> {result}, expected {expected}")
            all_passed = False
    
    # Test the DD.MM. pattern (current year logic)
    print("\n--- Testing current year logic ---")
    result = parse_infozagreb_date_fixed("15.3.")
    if result and isinstance(result, date):
        print(f"✓ '15.3.' -> {result} (current/next year logic)")
    else:
        print(f"✗ '15.3.' -> {result} (should return a date)")
        all_passed = False
    
    print(f"\n=== Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'} ===")
    return all_passed

if __name__ == "__main__":
    test_fixed_date_parsing()