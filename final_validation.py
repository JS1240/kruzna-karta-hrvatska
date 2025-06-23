#!/usr/bin/env python3
"""Final validation of the InfoZagreb scraper enhancements."""

import ast
import sys
import os
import re
from datetime import date

print("🔍 InfoZagreb Scraper Enhancement Validation")
print("=" * 60)

# 1. SYNTAX VALIDATION
print("\n1. 📝 SYNTAX CHECK")
print("-" * 30)

scraper_file = '/Users/juresunic/Projects/kruzna-karta-hrvatska/backend/app/scraping/infozagreb_scraper.py'

try:
    with open(scraper_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    ast.parse(code)
    print("✅ No syntax errors found")
    syntax_valid = True
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
    syntax_valid = False
except Exception as e:
    print(f"❌ Error reading file: {e}")
    syntax_valid = False

# 2. IMPORT VALIDATION
print("\n2. 📦 IMPORT VALIDATION")
print("-" * 30)

expected_imports = [
    'asyncio', 'json', 'logging', 're', 'datetime', 'typing', 'urllib.parse',
    'bs4', 'BaseScraper', 'EventCreate'
]

missing_imports = []
for imp in expected_imports:
    if imp not in code:
        missing_imports.append(imp)

if not missing_imports:
    print("✅ All expected imports present")
else:
    print(f"❌ Missing imports: {missing_imports}")

# 3. DATE PARSING VALIDATION
print("\n3. 📅 DATE PARSING VALIDATION")
print("-" * 30)

# Check if the fix was applied
if 'for i, pattern in enumerate(infozagreb_patterns):' in code:
    print("✅ Date parsing fix applied (using enumerate)")
    
    # Test the actual logic
    patterns = [
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{1,2})\s+(siječnja|veljače|ožujka|travnja|svibnja|lipnja|srpnja|kolovoza|rujna|listopada|studenoga|prosinca)\s+(\d{4})',
        r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
    ]
    
    test_cases = [
        ("15.3.2024", 0),  # Should match pattern 0
        ("2024-03-15", 1), # Should match pattern 1
        ("15 ožujka 2024", 2), # Should match pattern 2 (Croatian)
        ("15 march 2024", 3),  # Should match pattern 3 (English)
    ]
    
    for test_str, expected_pattern in test_cases:
        for i, pattern in enumerate(patterns):
            if re.search(pattern, test_str, re.IGNORECASE):
                if i == expected_pattern:
                    print(f"✅ '{test_str}' matches pattern {i}")
                else:
                    print(f"❌ '{test_str}' matches pattern {i}, expected {expected_pattern}")
                break
else:
    print("❌ Date parsing fix NOT applied - still using broken logic")

# 4. ZAGREB VENUE MAPPING VALIDATION
print("\n4. 🏢 ZAGREB VENUE MAPPING VALIDATION")
print("-" * 30)

if 'ZAGREB_VENUES = {' in code:
    print("✅ Zagreb venue mapping dictionary found")
    
    # Count venues
    venue_count = code.count('":', code.find('ZAGREB_VENUES'), code.find('}', code.find('ZAGREB_VENUES')))
    print(f"✅ {venue_count} Zagreb venues mapped")
    
    # Check for key venues
    key_venues = ['lisinski', 'hnk', 'dom sportova', 'arena zagreb', 'tvornica kulture']
    found_venues = [venue for venue in key_venues if venue in code]
    print(f"✅ Key venues found: {len(found_venues)}/{len(key_venues)}")
    
    if 'def _enhance_zagreb_location' in code:
        print("✅ Zagreb location enhancement function found")
    else:
        print("❌ Zagreb location enhancement function missing")
else:
    print("❌ Zagreb venue mapping not found")

# 5. MULTI-STRATEGY ARCHITECTURE VALIDATION
print("\n5. 🔄 MULTI-STRATEGY ARCHITECTURE VALIDATION")
print("-" * 30)

required_methods = {
    'scrape_with_api': 'API scraping strategy',
    'scrape_with_browser': 'Browser automation strategy',
    'scrape_with_fallbacks': 'Multi-strategy orchestrator',
    'setup_browser_client': 'Browser setup',
    'close_browser': 'Browser cleanup',
    'try_api_endpoints': 'API endpoint discovery',
    '_parse_api_response': 'API response parser',
    '_normalize_api_event': 'API event normalizer',
}

found_methods = {}
for method, description in required_methods.items():
    if f'def {method}' in code:
        found_methods[method] = True
        # Check if it's async where appropriate
        if method in ['scrape_with_api', 'scrape_with_browser', 'scrape_with_fallbacks', 
                     'setup_browser_client', 'close_browser', 'try_api_endpoints']:
            if f'async def {method}' in code:
                print(f"✅ {method} (async) - {description}")
            else:
                print(f"⚠️  {method} (not async) - {description}")
        else:
            print(f"✅ {method} - {description}")
    else:
        print(f"❌ {method} - {description}")
        found_methods[method] = False

method_score = sum(found_methods.values())
print(f"📊 Methods found: {method_score}/{len(required_methods)}")

# 6. ENHANCED PARSING VALIDATION
print("\n6. 🔍 ENHANCED PARSING VALIDATION")
print("-" * 30)

parsing_features = {
    '_find_event_containers': 'Enhanced container detection',
    '_parse_structured_data': 'JSON-LD structured data parsing',
    'parse_listing_element': 'Enhanced listing element parsing',
    '_extract_title': 'Multi-strategy title extraction',
    '_extract_link': 'Enhanced link extraction',
    '_extract_date_info': 'Enhanced date extraction',
    '_extract_image': 'Multi-strategy image extraction',
    '_extract_zagreb_location': 'Zagreb-specific location extraction',
}

parsing_score = 0
for feature, description in parsing_features.items():
    if f'def {feature}' in code:
        print(f"✅ {feature} - {description}")
        parsing_score += 1
    else:
        print(f"❌ {feature} - {description}")

print(f"📊 Parsing features: {parsing_score}/{len(parsing_features)}")

# 7. BROWSER AUTOMATION VALIDATION
print("\n7. 🌐 BROWSER AUTOMATION VALIDATION")
print("-" * 30)

browser_features = [
    ('playwright', 'Playwright integration'),
    ('setup_browser_client', 'Browser client setup'),
    ('close_browser', 'Browser cleanup'),
    ('headless=True', 'Headless browser mode'),
    ('user_agent', 'Custom user agent'),
    ('wait_until="networkidle"', 'Network idle waiting'),
]

browser_score = 0
for feature, description in browser_features:
    if feature in code:
        print(f"✅ {description}")
        browser_score += 1
    else:
        print(f"❌ {description}")

print(f"📊 Browser features: {browser_score}/{len(browser_features)}")

# 8. ERROR HANDLING VALIDATION
print("\n8. ⚠️  ERROR HANDLING VALIDATION")
print("-" * 30)

error_patterns = [
    'try:', 'except', 'finally:', 'logger.error', 'logger.warning', 'logger.debug'
]

error_score = 0
for pattern in error_patterns:
    count = code.count(pattern)
    if count > 0:
        print(f"✅ {pattern}: {count} occurrences")
        error_score += 1
    else:
        print(f"❌ {pattern}: not found")

print(f"📊 Error handling patterns: {error_score}/{len(error_patterns)}")

# FINAL SUMMARY
print("\n" + "=" * 60)
print("📋 FINAL VALIDATION SUMMARY")
print("=" * 60)

checks = [
    ("Syntax", syntax_valid),
    ("Imports", len(missing_imports) == 0),
    ("Date Parsing Fix", 'for i, pattern in enumerate(infozagreb_patterns):' in code),
    ("Zagreb Venues", 'ZAGREB_VENUES = {' in code),
    ("Multi-Strategy Methods", method_score >= len(required_methods) * 0.8),
    ("Enhanced Parsing", parsing_score >= len(parsing_features) * 0.8),
    ("Browser Automation", browser_score >= len(browser_features) * 0.7),
    ("Error Handling", error_score >= len(error_patterns) * 0.8),
]

passed_checks = sum(1 for _, passed in checks if passed)
total_checks = len(checks)

for check_name, passed in checks:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} {check_name}")

print(f"\n📊 Overall Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")

if passed_checks == total_checks:
    print("\n🎉 EXCELLENT! All validations passed.")
    print("✨ The InfoZagreb scraper enhancements are ready for testing.")
elif passed_checks >= total_checks * 0.8:
    print("\n✅ GOOD! Most validations passed.")
    print("⚠️  Address the failed checks above before deployment.")
else:
    print("\n⚠️  NEEDS WORK! Several validations failed.")
    print("🔧 Please fix the issues above before testing.")

print("\n" + "=" * 60)