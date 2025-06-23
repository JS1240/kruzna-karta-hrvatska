"""
LLM-powered location extraction service for Croatian events.
Uses OpenAI GPT to intelligently extract venue and location information from event text.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
import openai
from openai import AsyncOpenAI
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class LocationResult:
    """Result of LLM location extraction."""
    city: Optional[str] = None
    venue: Optional[str] = None
    full_location: Optional[str] = None
    confidence: float = 0.0
    reasoning: Optional[str] = None

class LLMLocationService:
    """Service for extracting location information using LLM."""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        self._location_cache = {}  # Simple in-memory cache
        self._setup_client()
        
        # Croatian cities for validation
        self.croatian_cities = {
            "zagreb", "split", "rijeka", "osijek", "zadar", "pula", "dubrovnik",
            "sisak", "karlovac", "varaždin", "velika gorica", "slavonski brod",
            "sesvete", "samobor", "zaprešić", "đakovo", "vinkovci", "vukovar",
            "bjelovar", "koprivnica", "požega", "nova gradiška", "cakovec",
            "opatija", "rovinj", "poreč", "umag", "krk", "crikvenica", "senj",
            "gospić", "makarska", "trogir", "hvar", "korčula", "sinj", "metković",
            "ploče", "otočac", "biograd", "pag", "nin", "novalja"
        }

    def _setup_client(self):
        """Initialize OpenAI client if API key is available."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                self.client = AsyncOpenAI(api_key=api_key)
                self.enabled = True
                logger.info("LLM Location Service initialized with OpenAI")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            logger.info("OpenAI API key not found - LLM location extraction disabled")
            self.enabled = False

    async def extract_location(
        self, 
        title: str, 
        description: str = "", 
        context: str = ""
    ) -> Optional[LocationResult]:
        """
        Extract location information from event text using LLM.
        
        Args:
            title: Event title
            description: Event description
            context: Additional context (e.g., venue, address)
            
        Returns:
            LocationResult with extracted location info or None if extraction fails
        """
        if not self.enabled:
            return None
        
        # Create cache key
        cache_key = f"{title}|{description}|{context}"
        if cache_key in self._location_cache:
            logger.debug(f"Cache hit for location extraction: {title}")
            return self._location_cache[cache_key]
            
        try:
            # Construct prompt for location extraction
            prompt = self._create_location_prompt(title, description, context)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use the faster, cheaper model for this task
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting location information from Croatian event listings. You understand Croatian geography, cities, venues, and cultural locations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            if result_text:
                result = self._parse_llm_response(result_text)
                # Cache the result
                if result:
                    self._location_cache[cache_key] = result
                return result
                
        except Exception as e:
            logger.error(f"LLM location extraction failed: {e}")
            
        return None

    def _create_location_prompt(self, title: str, description: str, context: str) -> str:
        """Create a structured prompt for location extraction."""
        
        text_parts = []
        if title:
            text_parts.append(f"Event Title: {title}")
        if description:
            text_parts.append(f"Description: {description}")
        if context:
            text_parts.append(f"Additional Context: {context}")
            
        event_text = "\n".join(text_parts)
        
        prompt = f"""
Extract the specific location information from this Croatian event listing:

{event_text}

Your task is to identify:
1. The specific venue or location name (e.g., "Poljud Stadium", "Arena Pula", "Jarun Lake")
2. The city where the event takes place
3. Create a complete location string

Guidelines:
- Focus on Croatian cities and venues
- Look for venue names, stadiums, theaters, hotels, beaches, parks
- Common Croatian venues: Poljud (Split), Arena Pula, Maksimir (Zagreb), Dom Sportova (Zagreb)
- Major cities: Zagreb, Split, Rijeka, Pula, Dubrovnik, Osijek, Zadar, Opatija
- If venue is unclear, focus on city identification
- Be specific: prefer "Poljud Stadium, Split" over just "Split"

Return your response as JSON with this exact structure:
{{
    "city": "City name or null",
    "venue": "Specific venue name or null", 
    "full_location": "Complete location string",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of extraction logic"
}}

Examples:
- "Ultra Europe Split" → {{"city": "Split", "venue": "Poljud Stadium", "full_location": "Poljud Stadium, Split", "confidence": 0.9}}
- "Concert Pula Arena" → {{"city": "Pula", "venue": "Arena Pula", "full_location": "Arena Pula, Pula", "confidence": 0.95}}
- "Zagreb event" → {{"city": "Zagreb", "venue": null, "full_location": "Zagreb", "confidence": 0.7}}
"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Optional[LocationResult]:
        """Parse LLM JSON response into LocationResult."""
        try:
            data = json.loads(response_text)
            
            # Validate city against known Croatian cities
            city = data.get("city")
            if city and city.lower() not in self.croatian_cities:
                # Check if it's a partial match
                city_lower = city.lower()
                for known_city in self.croatian_cities:
                    if city_lower in known_city or known_city in city_lower:
                        city = known_city.title()
                        break
                else:
                    # Unknown city, reduce confidence
                    data["confidence"] = max(0.0, data.get("confidence", 0.0) - 0.3)
            
            return LocationResult(
                city=city,
                venue=data.get("venue"),
                full_location=data.get("full_location"),
                confidence=data.get("confidence", 0.0),
                reasoning=data.get("reasoning")
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None

    async def normalize_venue_name(self, venue_name: str, city: str = "") -> Optional[str]:
        """
        Normalize venue name using LLM to handle aliases and variations.
        
        Args:
            venue_name: Raw venue name from event data
            city: City context for disambiguation
            
        Returns:
            Normalized venue name or None
        """
        if not self.enabled or not venue_name:
            return None
            
        try:
            prompt = f"""
Normalize this Croatian venue name to its standard form:

Venue: "{venue_name}"
City: "{city}"

Common Croatian venue aliases:
- "Poljud" → "Stadion Poljud" or "Poljud Stadium"
- "Arena" (in Pula) → "Arena Pula" or "Pula Arena"
- "Maksimir" → "Stadion Maksimir"
- "Dom Sportova" → "Dom Sportova Zagreb"
- "HNK" → "Hrvatsko narodno kazalište"

Return the standardized venue name as a simple string, or return the original if already standard.
Focus on Croatian venues and their common names.

Examples:
- "Poljud" → "Stadion Poljud"
- "Arena" (if city is Pula) → "Arena Pula"
- "Dom Sportova" → "Dom Sportova"
"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You normalize Croatian venue names to their standard forms."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            normalized = response.choices[0].message.content.strip()
            if normalized and len(normalized) > 0:
                # Remove quotes if present
                normalized = normalized.strip('"\'')
                return normalized
                
        except Exception as e:
            logger.error(f"Venue name normalization failed: {e}")
            
        return None

    def is_enabled(self) -> bool:
        """Check if LLM service is enabled and available."""
        return self.enabled

# Global instance
llm_location_service = LLMLocationService()