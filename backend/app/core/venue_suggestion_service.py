"""
Venue suggestion and correction system for Croatian events.
Provides intelligent venue name suggestions and handles user corrections.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from .database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

@dataclass
class VenueSuggestion:
    """Venue suggestion with similarity score."""
    venue_name: str
    similarity: float
    coordinates: Tuple[float, float]
    source: str
    confidence: float
    reason: str

class VenueSuggestionService:
    """Service for venue name suggestions and corrections."""
    
    def __init__(self):
        # Known Croatian venue patterns and aliases
        self.venue_patterns = {
            # Stadium patterns
            r'poljud|stadion.*split': 'Stadion Poljud, Split',
            r'maksimir|stadion.*zagreb': 'Stadion Maksimir, Zagreb',
            r'rujevica|stadion.*rijeka': 'Stadion Rujevica, Rijeka',
            r'gradski.*vrt|stadion.*osijek': 'Stadion Gradski vrt, Osijek',
            
            # Arena patterns  
            r'arena.*pula|pula.*arena|amfiteatar': 'Arena Pula, Pula',
            r'arena.*zagreb|dom.*sportova': 'Dom Sportova, Zagreb',
            
            # Theatre patterns
            r'hnk|narodno.*kazalište': 'Hrvatsko narodno kazalište',
            r'malo.*rimsko|small.*roman': 'Small Roman Theatre, Pula',
            
            # Hotel patterns
            r'amadria.*park|hotel.*royal': 'Amadria Park Hotel Royal, Opatija',
            r'hotel.*milenij': 'Hotel Milenij, Opatija',
            
            # Other venues
            r'jarun|jezero.*jarun': 'Jarun Lake, Zagreb',
            r'tvornica.*kulture': 'Tvornica Kulture, Zagreb',
            r'dioklecijan|diocletian': "Diocletian's Palace, Split",
        }
        
        # Croatian venue aliases
        self.venue_aliases = {
            'poljud': 'Stadion Poljud, Split',
            'maksimir': 'Stadion Maksimir, Zagreb', 
            'arena': 'Arena Pula, Pula',
            'dom sportova': 'Dom Sportova, Zagreb',
            'hnk': 'Hrvatsko narodno kazalište',
            'jarun': 'Jarun Lake, Zagreb',
            'amadria': 'Amadria Park Hotel Royal, Opatija',
        }

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two venue names."""
        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # Direct match
        if text1 == text2:
            return 1.0
            
        # Sequence matcher
        similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Boost for partial matches
        if text1 in text2 or text2 in text1:
            similarity = max(similarity, 0.8)
            
        # Boost for word matches
        words1 = set(text1.split())
        words2 = set(text2.split())
        word_overlap = len(words1.intersection(words2)) / max(len(words1), len(words2))
        similarity = max(similarity, word_overlap * 0.9)
        
        return similarity

    def suggest_venues_from_patterns(self, venue_input: str) -> List[VenueSuggestion]:
        """Suggest venues using pattern matching."""
        suggestions = []
        venue_lower = venue_input.lower()
        
        # Pattern matching
        for pattern, suggested_venue in self.venue_patterns.items():
            if re.search(pattern, venue_lower):
                suggestions.append(VenueSuggestion(
                    venue_name=suggested_venue,
                    similarity=0.9,
                    coordinates=(0.0, 0.0),  # Would be filled from database
                    source='pattern',
                    confidence=0.85,
                    reason=f'Matched pattern: {pattern}'
                ))
        
        # Alias matching
        for alias, suggested_venue in self.venue_aliases.items():
            if alias in venue_lower:
                suggestions.append(VenueSuggestion(
                    venue_name=suggested_venue,
                    similarity=0.95,
                    coordinates=(0.0, 0.0),
                    source='alias',
                    confidence=0.9,
                    reason=f'Matched alias: {alias}'
                ))
        
        return suggestions

    async def suggest_venues_from_database(
        self, 
        venue_input: str, 
        limit: int = 5
    ) -> List[VenueSuggestion]:
        """Suggest venues from cached venue database."""
        suggestions = []
        
        try:
            async with SessionLocal() as session:
                # Fuzzy search in venue coordinates cache
                query = text("""
                    SELECT venue_name, latitude, longitude, confidence, source
                    FROM venue_coordinates
                    WHERE LOWER(venue_name) LIKE LOWER(:search_pattern)
                       OR venue_name % :venue_input
                    ORDER BY confidence DESC, 
                             similarity(LOWER(venue_name), LOWER(:venue_input)) DESC
                    LIMIT :limit
                """)
                
                search_pattern = f"%{venue_input.lower()}%"
                result = await session.execute(query, {
                    "search_pattern": search_pattern,
                    "venue_input": venue_input,
                    "limit": limit
                })
                
                for row in result.fetchall():
                    similarity = self.calculate_similarity(venue_input, row[0])
                    if similarity > 0.4:  # Minimum similarity threshold
                        suggestions.append(VenueSuggestion(
                            venue_name=row[0],
                            similarity=similarity,
                            coordinates=(float(row[1]), float(row[2])),
                            source=row[4],
                            confidence=float(row[3]),
                            reason='Database match'
                        ))
                        
        except Exception as e:
            logger.error(f"Database venue search failed: {e}")
        
        return suggestions

    async def get_venue_suggestions(
        self, 
        venue_input: str,
        context: str = "",
        limit: int = 5
    ) -> List[VenueSuggestion]:
        """Get comprehensive venue suggestions."""
        all_suggestions = []
        
        # Pattern-based suggestions
        pattern_suggestions = self.suggest_venues_from_patterns(venue_input)
        all_suggestions.extend(pattern_suggestions)
        
        # Database suggestions
        db_suggestions = await self.suggest_venues_from_database(venue_input, limit)
        all_suggestions.extend(db_suggestions)
        
        # Remove duplicates and sort by similarity
        unique_suggestions = {}
        for suggestion in all_suggestions:
            key = suggestion.venue_name.lower()
            if key not in unique_suggestions or suggestion.similarity > unique_suggestions[key].similarity:
                unique_suggestions[key] = suggestion
        
        # Sort by similarity and confidence
        sorted_suggestions = sorted(
            unique_suggestions.values(),
            key=lambda s: (s.similarity, s.confidence),
            reverse=True
        )
        
        return sorted_suggestions[:limit]

    async def record_user_correction(
        self,
        original_venue: str,
        corrected_venue: str,
        latitude: float,
        longitude: float,
        user_id: Optional[str] = None
    ) -> bool:
        """Record user correction for venue name/location."""
        try:
            async with SessionLocal() as session:
                # Create venue corrections table entry
                query = text("""
                    INSERT INTO venue_corrections (
                        original_venue, corrected_venue, latitude, longitude,
                        user_id, created_at, status
                    ) VALUES (
                        :original_venue, :corrected_venue, :latitude, :longitude,
                        :user_id, CURRENT_TIMESTAMP, 'pending'
                    )
                """)
                
                await session.execute(query, {
                    "original_venue": original_venue,
                    "corrected_venue": corrected_venue,
                    "latitude": latitude,
                    "longitude": longitude,
                    "user_id": user_id
                })
                
                await session.commit()
                
                logger.info(f"Recorded venue correction: {original_venue} → {corrected_venue}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to record venue correction: {e}")
            return False

    def validate_venue_name(self, venue_name: str) -> Dict[str, any]:
        """Validate venue name and provide suggestions."""
        validation = {
            'valid': True,
            'confidence': 0.5,
            'suggestions': [],
            'issues': []
        }
        
        venue_clean = venue_name.strip()
        
        # Basic validation
        if len(venue_clean) < 3:
            validation['valid'] = False
            validation['issues'].append('Venue name too short')
            return validation
        
        if len(venue_clean) > 200:
            validation['valid'] = False
            validation['issues'].append('Venue name too long')
            return validation
        
        # Check for common issues
        if venue_clean.lower() in ['unknown', 'tbd', 'tba', '']:
            validation['confidence'] = 0.1
            validation['issues'].append('Generic or placeholder venue name')
        
        # Check for Croatian venue patterns
        venue_lower = venue_clean.lower()
        croatian_indicators = [
            'stadium', 'stadion', 'arena', 'kazalište', 'hotel', 'park',
            'zagreb', 'split', 'rijeka', 'pula', 'dubrovnik', 'opatija'
        ]
        
        if any(indicator in venue_lower for indicator in croatian_indicators):
            validation['confidence'] = min(validation['confidence'] + 0.3, 1.0)
        
        return validation

    async def get_venue_analytics(self) -> Dict[str, any]:
        """Get analytics about venue data quality."""
        analytics = {
            'total_venues': 0,
            'high_confidence': 0,
            'needs_review': 0,
            'user_corrections': 0,
            'common_issues': []
        }
        
        try:
            async with SessionLocal() as session:
                # Count total venues
                total_query = text("SELECT COUNT(*) FROM venue_coordinates")
                result = await session.execute(total_query)
                analytics['total_venues'] = result.scalar()
                
                # Count high confidence venues
                confidence_query = text("""
                    SELECT COUNT(*) FROM venue_coordinates 
                    WHERE confidence >= 0.8
                """)
                result = await session.execute(confidence_query)
                analytics['high_confidence'] = result.scalar()
                
                # Count venues needing review
                review_query = text("""
                    SELECT COUNT(*) FROM venue_coordinates 
                    WHERE confidence < 0.6
                """)
                result = await session.execute(review_query)
                analytics['needs_review'] = result.scalar()
                
                # Count user corrections (if table exists)
                try:
                    corrections_query = text("SELECT COUNT(*) FROM venue_corrections")
                    result = await session.execute(corrections_query)
                    analytics['user_corrections'] = result.scalar()
                except:
                    analytics['user_corrections'] = 0
                    
        except Exception as e:
            logger.error(f"Failed to get venue analytics: {e}")
        
        return analytics

# Global instance
venue_suggestion_service = VenueSuggestionService()