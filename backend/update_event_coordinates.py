#!/usr/bin/env python3
"""
Update all events in the database with proper coordinates using the enhanced geocoding system.
This script applies our 3-phase location positioning system to ensure accurate event positioning.
"""

import sys
import os
from decimal import Decimal
from typing import Optional, Tuple

# Add the app directory to the Python path
sys.path.append('/app')

from app.core.database import SessionLocal
from app.models.event import Event
from sqlalchemy import select, update

# Croatian venue coordinates from our enhanced geocoding system
CROATIAN_VENUE_COORDINATES = {
    # Major event venues and stadiums
    "poljud stadium": (43.5133, 16.4439),  # Split
    "stadion poljud": (43.5133, 16.4439),  # Split
    "arena pula": (44.8737, 13.8467),  # Pula
    "pula arena": (44.8737, 13.8467),  # Pula
    "amfiteatar pula": (44.8737, 13.8467),  # Pula
    "malo rimsko kazalište pula": (44.8688, 13.8467),  # Pula
    "small roman theatre pula": (44.8688, 13.8467),  # Pula
    
    # Zagreb venues
    "dom sportova": (45.7967, 15.9697),  # Zagreb
    "arena zagreb": (45.7967, 15.9697),  # Zagreb
    "maksimir stadium": (45.8219, 16.0119),  # Zagreb
    "stadion maksimir": (45.8219, 16.0119),  # Zagreb
    "hnk zagreb": (45.8081, 15.9678),  # Zagreb
    "croatian national theatre": (45.8081, 15.9678),  # Zagreb
    "hrvatsko narodno kazalište": (45.8081, 15.9678),  # Zagreb
    "tvornica kulture": (45.8003, 15.9897),  # Zagreb
    "jarun lake": (45.7833, 15.9167),  # Zagreb
    "jezero jarun": (45.7833, 15.9167),  # Zagreb
    
    # Split venues
    "diocletian's palace": (43.5082, 16.4404),  # Split
    "dioklecijanova palača": (43.5082, 16.4404),  # Split
    "diocletian palace": (43.5082, 16.4404),  # Split
    "riva split": (43.5081, 16.4401),  # Split
    "bacvice beach": (43.5048, 16.4531),  # Split
    "plaža bačvice": (43.5048, 16.4531),  # Split
    
    # Dubrovnik venues
    "lovrijenac fortress": (42.6414, 18.1064),  # Dubrovnik
    "tvrđava lovrijenac": (42.6414, 18.1064),  # Dubrovnik
    "rector's palace": (42.6414, 18.1108),  # Dubrovnik
    "knežev dvor": (42.6414, 18.1108),  # Dubrovnik
    
    # Other venues
    "hnk ivan zajc": (45.3294, 14.4422),  # Rijeka
    "croatian national theatre rijeka": (45.3294, 14.4422),  # Rijeka
    "gradski vrt": (45.5597, 18.6972),  # Osijek
    "city garden osijek": (45.5597, 18.6972),  # Osijek
}

# Croatian cities and their coordinates
CROATIAN_CITY_COORDINATES = {
    "zagreb": (45.815, 15.9819),
    "split": (43.5081, 16.4401),
    "rijeka": (45.3271, 14.4426),
    "osijek": (45.555, 18.6955),
    "zadar": (44.1194, 15.2314),
    "pula": (44.8666, 13.8496),
    "dubrovnik": (42.6507, 18.0944),
    "sisak": (45.4658, 16.3799),
    "karlovac": (45.487, 15.5477),
    "rovinj": (45.0804, 13.6386),
    "opatija": (45.3382, 14.3053),
    "makarska": (43.2969, 17.0178),
    "trogir": (43.515, 16.2515),
    "hvar": (43.1729, 16.4414),
}

def get_coordinates_for_location(location: str) -> Optional[Tuple[float, float]]:
    """Get coordinates for a location using enhanced geocoding logic."""
    if not location:
        return None
    
    normalized_location = location.lower().strip()
    
    # First check for specific venues (most precise)
    if normalized_location in CROATIAN_VENUE_COORDINATES:
        return CROATIAN_VENUE_COORDINATES[normalized_location]
    
    # Check for partial venue matches
    for venue_name, coords in CROATIAN_VENUE_COORDINATES.items():
        if venue_name in normalized_location or normalized_location in venue_name:
            return coords
    
    # Then check for direct city match
    if normalized_location in CROATIAN_CITY_COORDINATES:
        return CROATIAN_CITY_COORDINATES[normalized_location]
    
    # Extract city name and try again
    city_name = extract_city_name(location)
    if city_name and city_name in CROATIAN_CITY_COORDINATES:
        return CROATIAN_CITY_COORDINATES[city_name]
    
    print(f"⚠️  Could not find coordinates for location: {location}")
    return None

def extract_city_name(location: str) -> str:
    """Extract city name from location string."""
    if not location:
        return ""
    
    # Common patterns to extract city names
    import re
    patterns = [
        r'^([^,]+),',  # "City, Something" -> "City"
        r',\s*([^,]+)$',  # "Something, City" -> "City"
        r'^([^-]+)-',  # "City-Something" -> "City"
        r'([a-zA-ZšđčćžŠĐČĆŽ\s]+)',  # Any Croatian city name
    ]
    
    for pattern in patterns:
        match = re.search(pattern, location)
        if match and match.group(1):
            return match.group(1).strip().lower()
    
    return location.lower().strip()

def update_event_coordinates():
    """Update all events in the database with proper coordinates."""
    session = SessionLocal()
    try:
        # Get all events
        result = session.execute(select(Event))
        events = result.scalars().all()
        
        print(f"📊 Found {len(events)} events in database")
        print("=" * 60)
        
        updated_count = 0
        no_coords_count = 0
        
        for event in events:
            print(f"\n🎪 Event: {event.title}")
            print(f"   Location: {event.location}")
            print(f"   Current coordinates: ({event.latitude}, {event.longitude})")
            
            # Check if event already has coordinates
            if event.latitude and event.longitude:
                print(f"   ✅ Already has coordinates")
                continue
            
            # Get coordinates for the location
            coords = get_coordinates_for_location(event.location)
            
            if coords:
                lat, lng = coords
                print(f"   🎯 Assigning coordinates: ({lat}, {lng})")
                
                # Update the event
                session.execute(
                    update(Event)
                    .where(Event.id == event.id)
                    .values(
                        latitude=Decimal(str(lat)),
                        longitude=Decimal(str(lng))
                    )
                )
                updated_count += 1
            else:
                print(f"   ❌ No coordinates found")
                no_coords_count += 1
        
        # Commit all changes
        session.commit()
        
        print("\n" + "=" * 60)
        print(f"📈 Update Summary:")
        print(f"   ✅ Updated events: {updated_count}")
        print(f"   ❌ Events without coordinates: {no_coords_count}")
        print(f"   📊 Total events processed: {len(events)}")
    finally:
        session.close()

def main():
    """Main function."""
    print("🚀 Starting Event Coordinate Update")
    print("Applying enhanced 3-phase location positioning system...")
    print("=" * 60)
    
    try:
        update_event_coordinates()
        print("\n✅ Event coordinate update completed successfully!")
    except Exception as e:
        print(f"\n❌ Error updating event coordinates: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()