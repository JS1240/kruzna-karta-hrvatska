"""
Real-time geocoding service for Croatian venues.
Handles dynamic venue discovery and coordinate caching.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import httpx
import json
from datetime import datetime, timedelta

from .database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

@dataclass
class GeocodeResult:
    """Result of geocoding operation."""
    latitude: float
    longitude: float
    accuracy: str
    confidence: float
    source: str
    place_name: Optional[str] = None
    place_type: Optional[str] = None

class GeocodingService:
    """Service for real-time geocoding and venue discovery."""
    
    def __init__(self):
        self.mapbox_token = os.getenv("VITE_MAPBOX_ACCESS_TOKEN")
        self.cache = {}
        self._session = None
        
        # Croatian geographic bounds
        self.croatia_bounds = {
            'north': 46.55,
            'south': 42.38,
            'east': 19.43,
            'west': 13.50
        }

    async def get_session(self) -> httpx.AsyncClient:
        """Get or create async HTTP session."""
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=30.0)
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session:
            await self._session.aclose()
            self._session = None

    def is_within_croatia(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within Croatian bounds."""
        return (
            self.croatia_bounds['south'] <= lat <= self.croatia_bounds['north'] and
            self.croatia_bounds['west'] <= lng <= self.croatia_bounds['east']
        )

    async def geocode_with_mapbox(
        self, 
        location: str, 
        context: str = ""
    ) -> Optional[GeocodeResult]:
        """Geocode location using Mapbox API."""
        if not self.mapbox_token:
            logger.warning("Mapbox token not available for geocoding")
            return None

        try:
            session = await self.get_session()
            
            # Prepare query
            query_parts = [location.strip()]
            if context and context.strip():
                query_parts.append(context.strip())
            query_parts.append("Croatia")
            
            query = ", ".join(query_parts)
            encoded_query = httpx._utils.quote(query, safe='')
            
            url = (
                f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_query}.json"
                f"?access_token={self.mapbox_token}"
                f"&country=hr"
                f"&limit=5"
                f"&types=poi,address,place,neighborhood"
            )
            
            response = await session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('features'):
                return None
                
            # Get best result
            feature = data['features'][0]
            lng, lat = feature['center']
            
            # Validate coordinates
            if not self.is_within_croatia(lat, lng):
                logger.warning(f"Coordinates outside Croatia: {lat}, {lng} for {location}")
                return None
            
            # Determine accuracy and confidence
            place_types = feature.get('place_type', [])
            place_name = feature.get('place_name', '')
            
            accuracy = 'city'
            confidence = 0.5
            
            if 'poi' in place_types:
                accuracy = 'venue'
                confidence = 0.9
            elif 'address' in place_types:
                accuracy = 'address'
                confidence = 0.8
            elif 'neighborhood' in place_types:
                accuracy = 'neighborhood'
                confidence = 0.6
            
            # Boost confidence for known venue types
            venue_keywords = ['stadium', 'arena', 'theatre', 'theater', 'hotel', 'park', 'museum']
            if any(keyword in place_name.lower() for keyword in venue_keywords):
                confidence = min(confidence + 0.1, 1.0)
                
            return GeocodeResult(
                latitude=lat,
                longitude=lng,
                accuracy=accuracy,
                confidence=confidence,
                source='mapbox',
                place_name=place_name,
                place_type=place_types[0] if place_types else None
            )
            
        except Exception as e:
            logger.error(f"Mapbox geocoding failed for {location}: {e}")
            return None

    async def cache_venue_coordinates(
        self, 
        venue_name: str, 
        result: GeocodeResult
    ) -> bool:
        """Cache venue coordinates in database for future use."""
        try:
            async with SessionLocal() as session:
                # Check if venue already exists
                check_query = text("""
                    SELECT id FROM venue_coordinates 
                    WHERE LOWER(venue_name) = LOWER(:venue_name)
                """)
                
                existing = await session.execute(check_query, {"venue_name": venue_name})
                if existing.fetchone():
                    return True  # Already cached
                
                # Insert new venue
                insert_query = text("""
                    INSERT INTO venue_coordinates (
                        venue_name, latitude, longitude, accuracy, 
                        confidence, source, place_name, place_type, 
                        created_at, updated_at
                    ) VALUES (
                        :venue_name, :latitude, :longitude, :accuracy,
                        :confidence, :source, :place_name, :place_type,
                        :created_at, :updated_at
                    )
                """)
                
                now = datetime.utcnow()
                await session.execute(insert_query, {
                    "venue_name": venue_name,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "accuracy": result.accuracy,
                    "confidence": result.confidence,
                    "source": result.source,
                    "place_name": result.place_name,
                    "place_type": result.place_type,
                    "created_at": now,
                    "updated_at": now
                })
                
                await session.commit()
                logger.info(f"Cached venue coordinates: {venue_name} → {result.latitude}, {result.longitude}")
                return True
                
        except Exception as e:
            # If table doesn't exist, log warning but don't fail
            if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                logger.warning(f"venue_coordinates table does not exist, skipping cache for {venue_name}")
                return False
            logger.error(f"Failed to cache venue coordinates for {venue_name}: {e}")
            return False

    async def get_cached_venue_coordinates(
        self, 
        venue_name: str
    ) -> Optional[GeocodeResult]:
        """Get cached venue coordinates from database."""
        try:
            async with SessionLocal() as session:
                query = text("""
                    SELECT latitude, longitude, accuracy, confidence, 
                           source, place_name, place_type
                    FROM venue_coordinates 
                    WHERE LOWER(venue_name) = LOWER(:venue_name)
                    AND updated_at > :cutoff_date
                """)
                
                # Only use cache entries from last 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                result = await session.execute(query, {
                    "venue_name": venue_name,
                    "cutoff_date": cutoff_date
                })
                
                row = result.fetchone()
                if row:
                    return GeocodeResult(
                        latitude=float(row[0]),
                        longitude=float(row[1]),
                        accuracy=row[2],
                        confidence=float(row[3]),
                        source=row[4],
                        place_name=row[5],
                        place_type=row[6]
                    )
                    
        except Exception as e:
            # If table doesn't exist, log debug message but don't fail
            if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                logger.debug(f"venue_coordinates table does not exist, no cache available for {venue_name}")
            else:
                logger.error(f"Failed to get cached coordinates for {venue_name}: {e}")
            
        return None

    async def discover_new_venues(
        self, 
        event_locations: List[str]
    ) -> Dict[str, GeocodeResult]:
        """Discover and geocode new venues from event locations."""
        results = {}
        
        for location in event_locations:
            if not location or location.strip() == "":
                continue
                
            location = location.strip()
            
            # Check cache first
            cached = await self.get_cached_venue_coordinates(location)
            if cached:
                results[location] = cached
                continue
            
            # Try geocoding
            geocoded = await self.geocode_with_mapbox(location)
            if geocoded and geocoded.confidence > 0.6:
                results[location] = geocoded
                
                # Cache result for future use
                await self.cache_venue_coordinates(location, geocoded)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
        
        return results

    async def batch_geocode_venues(
        self, 
        venues: List[Tuple[str, str]]  # [(venue_name, context), ...]
    ) -> Dict[str, GeocodeResult]:
        """Batch geocode multiple venues with rate limiting."""
        results = {}
        
        for venue_name, context in venues:
            if not venue_name:
                continue
                
            # Check cache
            cached = await self.get_cached_venue_coordinates(venue_name)
            if cached:
                results[venue_name] = cached
                continue
            
            # Geocode
            result = await self.geocode_with_mapbox(venue_name, context)
            if result and result.confidence > 0.5:
                results[venue_name] = result
                await self.cache_venue_coordinates(venue_name, result)
            
            # Rate limiting
            await asyncio.sleep(0.2)
        
        return results

    async def validate_coordinates(
        self, 
        latitude: float, 
        longitude: float
    ) -> Dict[str, any]:
        """Validate coordinates and provide accuracy information."""
        validation = {
            'valid': False,
            'in_croatia': False,
            'accuracy_estimate': 'unknown',
            'nearest_city': None,
            'confidence': 0.0
        }
        
        # Basic validation
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return validation
            
        validation['valid'] = True
        validation['in_croatia'] = self.is_within_croatia(latitude, longitude)
        
        if validation['in_croatia']:
            validation['confidence'] = 0.8
            validation['accuracy_estimate'] = 'good'
            
            # Try reverse geocoding to get nearest city
            try:
                session = await self.get_session()
                url = (
                    f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
                    f"{longitude},{latitude}.json"
                    f"?access_token={self.mapbox_token}"
                    f"&types=place"
                    f"&limit=1"
                )
                
                response = await session.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('features'):
                        validation['nearest_city'] = data['features'][0]['place_name']
                        validation['confidence'] = 0.9
                        
            except Exception as e:
                logger.error(f"Reverse geocoding failed: {e}")
        
        return validation

# Global instance
geocoding_service = GeocodingService()