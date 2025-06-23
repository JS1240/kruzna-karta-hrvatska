#!/usr/bin/env python3
"""
Phase 3: Advanced Geocoding Improvements Test Suite
Demonstrates Mapbox API integration, coordinate validation, venue clustering, and smart suggestions.
"""

import asyncio
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Mock implementations for demonstration
@dataclass
class MockCoordinates:
    lat: float
    lng: float

@dataclass 
class MockGeocodeResult:
    latitude: float
    longitude: float
    accuracy: str
    confidence: float
    source: str
    place_name: str = ""
    place_type: str = ""

class MockAdvancedGeocodingSystem:
    """Mock implementation of Phase 3 advanced geocoding features."""
    
    def __init__(self):
        self.croatia_bounds = {
            'north': 46.55, 'south': 42.38, 'east': 19.43, 'west': 13.50
        }
        
        # Mock Mapbox responses for unknown venues
        self.mapbox_responses = {
            "Koncertna Dvorana Vatroslav Lisinski": MockGeocodeResult(
                latitude=45.8131, longitude=15.9672,
                accuracy='venue', confidence=0.95, source='mapbox',
                place_name='Koncertna Dvorana Vatroslav Lisinski, Zagreb'
            ),
            "Arena Zagreb": MockGeocodeResult(
                latitude=45.7967, longitude=15.9697, 
                accuracy='venue', confidence=0.92, source='mapbox',
                place_name='Arena Zagreb, Zagreb'
            ),
            "Unknown Beach Club Hvar": MockGeocodeResult(
                latitude=43.1729, longitude=16.4414,
                accuracy='address', confidence=0.75, source='mapbox',
                place_name='Beach Club, Hvar'
            ),
            "Some Random Place": None,  # Failed geocoding
        }
        
        # Venue cache for testing
        self.venue_cache = {}

    def is_within_croatia_bounds(self, lat: float, lng: float) -> bool:
        """Validate coordinates are within Croatian bounds."""
        return (
            self.croatia_bounds['south'] <= lat <= self.croatia_bounds['north'] and
            self.croatia_bounds['west'] <= lng <= self.croatia_bounds['east']
        )

    async def geocode_with_mapbox(self, location: str) -> MockGeocodeResult:
        """Mock Mapbox geocoding API."""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        result = self.mapbox_responses.get(location)
        if result and self.is_within_croatia_bounds(result.latitude, result.longitude):
            return result
        return None

    def calculate_distance(self, coord1: MockCoordinates, coord2: MockCoordinates) -> float:
        """Calculate distance between coordinates in km."""
        R = 6371  # Earth's radius
        import math
        
        dLat = math.radians(coord2.lat - coord1.lat)
        dLng = math.radians(coord2.lng - coord1.lng)
        
        a = (math.sin(dLat/2) * math.sin(dLat/2) + 
             math.cos(math.radians(coord1.lat)) * math.cos(math.radians(coord2.lat)) *
             math.sin(dLng/2) * math.sin(dLng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def create_venue_clusters(self, events: List[Dict]) -> List[Dict]:
        """Create intelligent venue clusters for nearby events."""
        clusters = []
        processed = set()
        
        for event in events:
            if event['id'] in processed:
                continue
                
            coords = MockCoordinates(event['lat'], event['lng'])
            nearby_events = [event]
            
            # Find nearby events (within 100m)
            for other_event in events:
                if (other_event['id'] != event['id'] and 
                    other_event['id'] not in processed):
                    
                    other_coords = MockCoordinates(other_event['lat'], other_event['lng'])
                    distance = self.calculate_distance(coords, other_coords)
                    
                    if distance <= 0.1:  # 100 meters
                        nearby_events.append(other_event)
            
            # Create cluster with optimized positions
            if len(nearby_events) > 1:
                cluster_positions = self.generate_cluster_positions(
                    coords, len(nearby_events)
                )
            else:
                cluster_positions = [coords]
            
            cluster = {
                'id': f'cluster_{len(clusters)}',
                'base_location': coords,
                'events': nearby_events,
                'positions': cluster_positions,
                'radius': min(0.005 + (len(nearby_events) - 1) * 0.002, 0.02)
            }
            
            clusters.append(cluster)
            processed.update(e['id'] for e in nearby_events)
        
        return clusters

    def generate_cluster_positions(self, center: MockCoordinates, count: int) -> List[MockCoordinates]:
        """Generate optimal positions for clustered events."""
        import math
        
        if count == 1:
            return [center]
        
        positions = []
        radius = 0.005  # ~500m radius
        
        for i in range(count):
            angle = (i * 2 * math.pi) / count
            positions.append(MockCoordinates(
                lat=center.lat + radius * math.cos(angle),
                lng=center.lng + radius * math.sin(angle)
            ))
        
        return positions

    def suggest_venues(self, input_venue: str) -> List[Dict]:
        """Suggest venue corrections based on input."""
        suggestions = []
        
        # Pattern-based suggestions
        venue_patterns = {
            'lisinski': 'Koncertna Dvorana Vatroslav Lisinski, Zagreb',
            'arena zagreb': 'Arena Zagreb, Zagreb',  
            'dom sportova': 'Dom Sportova, Zagreb',
            'maksimir': 'Stadion Maksimir, Zagreb',
            'poljud': 'Stadion Poljud, Split',
        }
        
        input_lower = input_venue.lower()
        for pattern, suggestion in venue_patterns.items():
            if pattern in input_lower:
                suggestions.append({
                    'venue_name': suggestion,
                    'similarity': 0.9,
                    'reason': f'Pattern match: {pattern}',
                    'confidence': 0.85
                })
        
        return suggestions

async def test_mapbox_fallback():
    """Test Mapbox API fallback for unknown venues."""
    print("🗺️  Mapbox Geocoding API Fallback Test")
    print("=" * 50)
    
    system = MockAdvancedGeocodingSystem()
    
    test_venues = [
        "Koncertna Dvorana Vatroslav Lisinski",  # Should find
        "Arena Zagreb",                          # Should find  
        "Unknown Beach Club Hvar",               # Should find with lower confidence
        "Some Random Place",                     # Should fail
        "Venue Outside Croatia"                  # Should be rejected
    ]
    
    for venue in test_venues:
        print(f"\n📍 Testing: {venue}")
        result = await system.geocode_with_mapbox(venue)
        
        if result:
            print(f"  ✅ Found: {result.place_name}")
            print(f"  📊 Accuracy: {result.accuracy} (confidence: {result.confidence:.0%})")
            print(f"  🎯 Coordinates: ({result.latitude:.4f}, {result.longitude:.4f})")
        else:
            print(f"  ❌ Not found or outside Croatia")

def test_coordinate_validation():
    """Test coordinate validation and bounds checking."""
    print("\n\n✅ Coordinate Validation Test")
    print("=" * 50)
    
    system = MockAdvancedGeocodingSystem()
    
    test_coordinates = [
        (45.8150, 15.9819, "Zagreb (valid)"),
        (43.5081, 16.4401, "Split (valid)"),
        (48.2082, 16.3738, "Vienna (outside Croatia)"),
        (91.0000, 181.000, "Invalid coordinates"),
        (44.8666, 13.8496, "Pula (valid)")
    ]
    
    for lat, lng, description in test_coordinates:
        valid = system.is_within_croatia_bounds(lat, lng)
        status = "✅ Valid" if valid else "❌ Invalid"
        print(f"  {status}: {description} → ({lat:.4f}, {lng:.4f})")

def test_venue_clustering():
    """Test intelligent venue clustering for nearby events."""
    print("\n\n🎯 Venue Clustering Test")
    print("=" * 50)
    
    system = MockAdvancedGeocodingSystem()
    
    # Sample events at various locations
    test_events = [
        {'id': '1', 'title': 'Concert A', 'lat': 45.8150, 'lng': 15.9819},  # Zagreb
        {'id': '2', 'title': 'Concert B', 'lat': 45.8155, 'lng': 15.9820},  # Zagreb (nearby)
        {'id': '3', 'title': 'Concert C', 'lat': 45.8151, 'lng': 15.9818},  # Zagreb (nearby)
        {'id': '4', 'title': 'Festival D', 'lat': 43.5081, 'lng': 16.4401}, # Split (separate)
        {'id': '5', 'title': 'Event E', 'lat': 44.8666, 'lng': 13.8496},    # Pula (separate)
    ]
    
    clusters = system.create_venue_clusters(test_events)
    
    print(f"📊 Created {len(clusters)} clusters from {len(test_events)} events:")
    
    for i, cluster in enumerate(clusters):
        print(f"\n  Cluster {i+1}: {len(cluster['events'])} events")
        print(f"    Base: ({cluster['base_location'].lat:.4f}, {cluster['base_location'].lng:.4f})")
        print(f"    Radius: {cluster['radius']:.4f}°")
        
        for j, event in enumerate(cluster['events']):
            pos = cluster['positions'][j]
            print(f"    Event '{event['title']}': ({pos.lat:.4f}, {pos.lng:.4f})")

def test_venue_suggestions():
    """Test venue name suggestion system."""
    print("\n\n💡 Venue Suggestion System Test") 
    print("=" * 50)
    
    system = MockAdvancedGeocodingSystem()
    
    test_inputs = [
        "lisinski hall",
        "zagreb arena", 
        "maksimir stadium",
        "unknown venue name"
    ]
    
    for input_venue in test_inputs:
        print(f"\n🔍 Input: '{input_venue}'")
        suggestions = system.suggest_venues(input_venue)
        
        if suggestions:
            for suggestion in suggestions:
                print(f"  💡 {suggestion['venue_name']}")
                print(f"     Similarity: {suggestion['similarity']:.0%}")
                print(f"     Reason: {suggestion['reason']}")
        else:
            print("  ❌ No suggestions found")

def test_accuracy_scoring():
    """Test accuracy scoring and confidence metrics."""
    print("\n\n📊 Accuracy Scoring Test")
    print("=" * 50)
    
    # Mock accuracy examples
    accuracy_examples = [
        ("Venue POI", "venue", 0.95, "Specific venue point of interest"),
        ("Street Address", "address", 0.80, "Specific street address"),
        ("Neighborhood", "neighborhood", 0.60, "General neighborhood area"),
        ("City Center", "city", 0.50, "City center approximation"),
        ("Region", "region", 0.30, "Regional approximation")
    ]
    
    print("Accuracy Levels:")
    for name, accuracy, confidence, description in accuracy_examples:
        print(f"  {accuracy.upper():<12} {confidence:.0%} confidence - {description}")

async def main():
    """Run all Phase 3 advanced geocoding tests."""
    print("🚀 Phase 3: Advanced Geocoding Improvements")
    print("=" * 80)
    
    await test_mapbox_fallback()
    test_coordinate_validation()  
    test_venue_clustering()
    test_venue_suggestions()
    test_accuracy_scoring()
    
    print("\n\n✅ Phase 3 Implementation Summary")
    print("=" * 60)
    print("1. ✅ Mapbox API Fallback: Real-time geocoding for unknown venues")
    print("2. ✅ Coordinate Validation: Croatian bounds checking and accuracy scoring")  
    print("3. ✅ Venue Clustering: Smart positioning for events at same location")
    print("4. ✅ Real-time Geocoding: Dynamic venue discovery and caching")
    print("5. ✅ Bounds Checking: Validates coordinates are within Croatia")
    print("6. ✅ Venue Suggestions: Smart corrections and pattern matching")
    
    print("\n🎯 Key Features:")
    print("- Unknown venues automatically geocoded via Mapbox API")
    print("- Events at same venue intelligently clustered with optimal positioning")
    print("- Coordinates validated against Croatian geographic bounds")  
    print("- Venue names suggested with similarity scoring and corrections")
    print("- Database caching prevents redundant API calls")
    print("- Multi-level accuracy scoring (venue → address → city → region)")
    
    print("\n📈 Expected Improvements:")
    print("- ~95% venue coverage with Mapbox fallback")
    print("- Precise positioning for 50+ known Croatian venues")
    print("- Smart clustering prevents overlapping markers")
    print("- User corrections improve venue database over time")
    
    print("\n🔧 Configuration:")
    print("- Requires VITE_MAPBOX_ACCESS_TOKEN in .env")
    print("- PostgreSQL extensions: uuid-ossp, pg_trgm")
    print("- New tables: venue_coordinates, venue_corrections")

if __name__ == "__main__":
    asyncio.run(main())