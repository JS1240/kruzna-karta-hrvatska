"""
Croatian Geographic Database
Contains major Croatian cities, regions, and venues with coordinates for fallback geocoding.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CroatianLocation:
    """Croatian location with coordinates and metadata."""
    name: str
    latitude: float
    longitude: float
    location_type: str  # city, region, venue, landmark
    aliases: List[str]
    confidence: float
    population: Optional[int] = None
    region: Optional[str] = None

class CroatianGeoDatabase:
    """Database of Croatian locations for fallback geocoding."""
    
    def __init__(self):
        self.locations = self._load_croatian_locations()
        self.aliases_map = self._build_aliases_map()
    
    def _load_croatian_locations(self) -> Dict[str, CroatianLocation]:
        """Load Croatian cities, regions, and venues with coordinates."""
        locations = {}
        
        # Major Croatian cities with accurate coordinates
        cities_data = [
            # Format: (name, lat, lng, aliases, population, region)
            ("Zagreb", 45.8150, 15.9819, ["zagreb", "main city", "capital"], 806341, "Zagreb County"),
            ("Split", 43.5147, 16.4435, ["split", "second city"], 178192, "Split-Dalmatia County"),
            ("Rijeka", 45.3371, 14.4087, ["rijeka", "port city"], 128384, "Primorje-Gorski Kotar County"),
            ("Osijek", 45.5550, 18.6955, ["osijek"], 84104, "Osijek-Baranja County"),
            ("Zadar", 44.1194, 15.2314, ["zadar"], 75062, "Zadar County"),
            ("Slavonski Brod", 45.1600, 18.0158, ["slavonski brod", "brod"], 59141, "Brod-Posavina County"),
            ("Pula", 44.8666, 13.8496, ["pula", "istria main"], 57765, "Istria County"),
            ("Karlovac", 45.4870, 15.5470, ["karlovac"], 55705, "Karlovac County"),
            ("Sisak", 45.4667, 16.3833, ["sisak"], 47768, "Sisak-Moslavina County"),
            ("Varaždin", 46.3044, 16.3377, ["varazdin", "varaždin"], 46946, "Varaždin County"),
            
            # Important smaller cities and tourist destinations
            ("Dubrovnik", 42.6507, 18.0944, ["dubrovnik", "pearl of adriatic"], 42615, "Dubrovnik-Neretva County"),
            ("Šibenik", 43.7350, 15.8952, ["sibenik", "šibenik"], 34302, "Šibenik-Knin County"),
            ("Velika Gorica", 45.7131, 16.0758, ["velika gorica"], 31341, "Zagreb County"),
            ("Vinkovci", 45.2883, 18.8047, ["vinkovci"], 28112, "Vukovar-Syrmia County"),
            ("Vukovar", 45.3517, 19.0044, ["vukovar"], 26468, "Vukovar-Syrmia County"),
            ("Sesvete", 45.8311, 16.1117, ["sesvete"], 25410, "Zagreb County"),
            ("Bjelovar", 45.8986, 16.8422, ["bjelovar"], 23142, "Bjelovar-Bilogora County"),
            ("Koprivnica", 46.1631, 16.8267, ["koprivnica"], 21255, "Koprivnica-Križevci County"),
            ("Požega", 45.3400, 17.6856, ["pozega", "požega"], 19506, "Požega-Slavonia County"),
            ("Čakovec", 46.3836, 16.4267, ["cakovec", "čakovec"], 15147, "Međimurje County"),
            
            # Island and coastal cities
            ("Hvar", 43.1725, 16.4422, ["hvar island", "hvar"], 4251, "Split-Dalmatia County"),
            ("Korčula", 42.9600, 17.1356, ["korcula", "korčula"], 3134, "Dubrovnik-Neretva County"),
            ("Krk", 45.0264, 14.5756, ["krk island", "krk"], 3065, "Primorje-Gorski Kotar County"),
            ("Rab", 44.7553, 14.7553, ["rab island", "rab"], 2059, "Primorje-Gorski Kotar County"),
            ("Vis", 43.0622, 16.1833, ["vis island", "vis"], 1934, "Split-Dalmatia County"),
            ("Lastovo", 42.7667, 16.9000, ["lastovo island", "lastovo"], 792, "Dubrovnik-Neretva County"),
            
            # Regional centers and important towns
            ("Rovinj", 45.0847, 13.6400, ["rovinj", "rovigno"], 14294, "Istria County"),
            ("Umag", 45.4319, 13.5208, ["umag", "umago"], 13467, "Istria County"),
            ("Poreč", 45.2269, 13.5947, ["porec", "poreč", "parenzo"], 16696, "Istria County"),
            ("Opatija", 45.3378, 14.3061, ["opatija"], 11659, "Primorje-Gorski Kotar County"),
            ("Trogir", 43.5150, 16.2519, ["trogir"], 10266, "Split-Dalmatia County"),
            ("Makarska", 43.2975, 17.0175, ["makarska"], 13834, "Split-Dalmatia County"),
            ("Omiš", 43.4444, 16.6889, ["omis", "omiš"], 14936, "Split-Dalmatia County"),
            
            # URL-based locations from Croatia.hr
            ("Dugo Selo", 45.7978, 16.2119, ["dugo selo", "long village"], 17466, "Zagreb County"),
            ("Vrsar", 45.1514, 13.6006, ["vrsar", "orsera"], 2703, "Istria County"),
            ("Central Istria", 45.2369, 13.9300, ["central istria", "central-istria", "srednja istra"], None, "Istria County"),
            ("Bakar", 45.3097, 14.5319, ["bakar"], 8279, "Primorje-Gorski Kotar County"),
            ("Jasenovac", 45.2667, 16.9333, ["jasenovac"], 2391, "Sisak-Moslavina County"),
            ("Preloga", 46.3333, 16.6167, ["preloga"], 1625, "Međimurje County"),
            ("Senj", 44.9894, 14.9061, ["senj"], 7182, "Lika-Senj County"),
            ("Nin", 44.2425, 15.1786, ["nin"], 1132, "Zadar County"),
            ("Novigrad", 45.3167, 13.5667, ["novigrad", "cittanova"], 4345, "Istria County"),
            ("Labin", 45.0950, 14.1200, ["labin", "albona"], 11642, "Istria County"),
        ]
        
        # Convert to CroatianLocation objects
        for name, lat, lng, aliases, population, region in cities_data:
            # Determine confidence based on population and importance
            if population and population > 100000:
                confidence = 0.9
            elif population and population > 50000:
                confidence = 0.8  
            elif population and population > 10000:
                confidence = 0.7
            else:
                confidence = 0.6
                
            locations[name.lower()] = CroatianLocation(
                name=name,
                latitude=lat,
                longitude=lng,
                location_type="city",
                aliases=[alias.lower() for alias in aliases],
                confidence=confidence,
                population=population,
                region=region
            )
        
        # Add Croatian regions as fallback
        regions_data = [
            ("Istria County", 45.2369, 13.9300, ["istria", "istra", "istrian peninsula"], 0.5),
            ("Split-Dalmatia County", 43.5147, 16.4435, ["dalmatia", "dalmacija", "split region"], 0.5),
            ("Dubrovnik-Neretva County", 42.6507, 18.0944, ["dubrovnik region", "southern dalmatia"], 0.5),
            ("Primorje-Gorski Kotar County", 45.3371, 14.4087, ["primorje", "gorski kotar", "coastal region"], 0.5),
            ("Zagreb County", 45.8150, 15.9819, ["zagreb region", "central croatia"], 0.5),
            ("Lika-Senj County", 44.7306, 15.3847, ["lika", "senj region"], 0.4),
            ("Zadar County", 44.1194, 15.2314, ["zadar region", "northern dalmatia"], 0.5),
        ]
        
        for name, lat, lng, aliases, confidence in regions_data:
            locations[name.lower()] = CroatianLocation(
                name=name,
                latitude=lat,
                longitude=lng,
                location_type="region",
                aliases=[alias.lower() for alias in aliases],
                confidence=confidence
            )
        
        return locations
    
    def _build_aliases_map(self) -> Dict[str, str]:
        """Build a map from aliases to canonical location names."""
        aliases_map = {}
        
        for canonical_name, location in self.locations.items():
            # Add the canonical name itself
            aliases_map[canonical_name] = canonical_name
            
            # Add all aliases
            for alias in location.aliases:
                aliases_map[alias] = canonical_name
        
        return aliases_map
    
    def find_location(self, query: str) -> Optional[CroatianLocation]:
        """Find a Croatian location by name or alias."""
        if not query:
            return None
            
        query_lower = query.lower().strip()
        
        # Direct match
        if query_lower in self.aliases_map:
            canonical_name = self.aliases_map[query_lower]
            return self.locations[canonical_name]
        
        # Fuzzy matching for common variations
        for alias, canonical_name in self.aliases_map.items():
            if self._fuzzy_match(query_lower, alias):
                return self.locations[canonical_name]
        
        return None
    
    def _fuzzy_match(self, query: str, candidate: str) -> bool:
        """Simple fuzzy matching for Croatian place names."""
        # Remove common variations
        query_clean = query.replace("-", " ").replace("_", " ")
        candidate_clean = candidate.replace("-", " ").replace("_", " ")
        
        # Check if one is contained in the other
        if query_clean in candidate_clean or candidate_clean in query_clean:
            return True
        
        # Check Croatian character variations
        croatian_chars = {
            'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': 'd'
        }
        
        for hr_char, latin_char in croatian_chars.items():
            query_latin = query_clean.replace(hr_char, latin_char)
            candidate_latin = candidate_clean.replace(hr_char, latin_char)
            
            if query_latin == candidate_latin:
                return True
        
        return False
    
    def get_fallback_coordinates(self, location_type: str = "city") -> Tuple[float, float]:
        """Get fallback coordinates for Croatia (Zagreb center)."""
        zagreb = self.locations.get("zagreb")
        if zagreb:
            return zagreb.latitude, zagreb.longitude
        return 45.8150, 15.9819  # Zagreb coordinates as ultimate fallback
    
    def get_cities_by_region(self, region: str) -> List[CroatianLocation]:
        """Get all cities in a specific region."""
        region_lower = region.lower()
        cities = []
        
        for location in self.locations.values():
            if (location.location_type == "city" and 
                location.region and 
                region_lower in location.region.lower()):
                cities.append(location)
        
        return cities
    
    def get_all_cities(self) -> List[CroatianLocation]:
        """Get all Croatian cities sorted by population."""
        cities = [loc for loc in self.locations.values() if loc.location_type == "city"]
        return sorted(cities, key=lambda x: x.population or 0, reverse=True)

# Global instance
croatian_geo_db = CroatianGeoDatabase()