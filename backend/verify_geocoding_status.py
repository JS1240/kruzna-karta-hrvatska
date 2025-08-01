#!/usr/bin/env python3
"""
Verify final geocoding status for all events.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal
from app.models.event import Event
from sqlalchemy import text

def verify_geocoding_status():
    """Verify geocoding status across all events."""
    print("🗺️ Verifying final geocoding status...")
    
    try:
        db = SessionLocal()
        
        # Get comprehensive statistics
        query = text("""
            SELECT 
                source,
                COUNT(*) as total,
                COUNT(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 END) as geocoded,
                ROUND(
                    (COUNT(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 END) * 100.0 / COUNT(*)), 
                    1
                ) as success_rate
            FROM events 
            GROUP BY source
            ORDER BY source;
        """)
        
        results = db.execute(query).fetchall()
        
        print("\n" + "=" * 70)
        print("🎯 FINAL GEOCODING STATISTICS")
        print("=" * 70)
        
        total_events = 0
        total_geocoded = 0
        
        for row in results:
            source, total, geocoded, success_rate = row
            total_events += total
            total_geocoded += geocoded
            
            print(f"  📍 {source.upper():>8} | Total: {total:>3} | Geocoded: {geocoded:>3} | Success: {success_rate:>5}%")
        
        overall_success = (total_geocoded / total_events * 100) if total_events > 0 else 0
        
        print("-" * 70)
        print(f"  🌍 OVERALL   | Total: {total_events:>3} | Geocoded: {total_geocoded:>3} | Success: {overall_success:>5.1f}%")
        print("=" * 70)
        
        # Check specifically for Croatia events
        croatia_query = text("""
            SELECT 
                title, location, latitude, longitude
            FROM events 
            WHERE source = 'croatia' 
            ORDER BY title
            LIMIT 10;
        """)
        
        croatia_results = db.execute(croatia_query).fetchall()
        
        if croatia_results:
            print("\n📋 Sample Croatia Events (showing 10 of them):")
            print("-" * 70)
            for row in croatia_results:
                title, location, lat, lng = row
                coords_status = "✅ GEOCODED" if lat and lng else "❌ NO COORDS"
                print(f"  • {title[:40]:<40} | {location:<15} | {coords_status}")
        
        # Check for any remaining ungeocodable events
        ungeocodable_query = text("""
            SELECT source, COUNT(*) as count
            FROM events 
            WHERE latitude IS NULL OR longitude IS NULL
            GROUP BY source;
        """)
        
        ungeocodable_results = db.execute(ungeocodable_query).fetchall()
        
        if ungeocodable_results:
            print("\n⚠️  Events still without coordinates:")
            for row in ungeocodable_results:
                source, count = row
                print(f"  • {source}: {count} events")
        else:
            print("\n🎉 ALL EVENTS ARE SUCCESSFULLY GEOCODED AND WILL APPEAR ON THE MAP!")
        
        return total_geocoded == total_events
        
    except Exception as e:
        print(f"❌ Failed to verify geocoding status: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = verify_geocoding_status()
    sys.exit(0 if success else 1)