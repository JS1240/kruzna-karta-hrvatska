#!/usr/bin/env python3
"""
Test script to demonstrate LLM-enhanced location extraction.
This shows how the system would work with an OpenAI API key.
"""

import asyncio
import json
from typing import Dict, List

# Mock LLM responses for demonstration
MOCK_LLM_RESPONSES = {
    "Ultra Europe Festival 2025": {
        "city": "Split",
        "venue": "Poljud Stadium", 
        "full_location": "Poljud Stadium, Split",
        "confidence": 0.95,
        "reasoning": "Ultra Europe is Croatia's biggest electronic music festival, held annually at Poljud Stadium in Split"
    },
    "Amira Medunjanin Zagreb": {
        "city": "Pula",
        "venue": "Small Roman Theatre",
        "full_location": "Small Roman Theatre, Pula", 
        "confidence": 0.90,
        "reasoning": "Amira Medunjanin often performs at historic venues. The mention suggests Pula's Small Roman Theatre"
    },
    "Jim Jefferies Live In Zagreb": {
        "city": "Zagreb",
        "venue": "Dom Sportova",
        "full_location": "Dom Sportova, Zagreb",
        "confidence": 0.85,
        "reasoning": "Comedy shows in Zagreb typically happen at Dom Sportova or similar large venues"
    },
    "Symphonie Gourmet Experience Opatija": {
        "city": "Opatija", 
        "venue": "Amadria Park Hotel Royal",
        "full_location": "Amadria Park Hotel Royal, Opatija",
        "confidence": 0.92,
        "reasoning": "Gourmet experiences in Opatija often take place at luxury hotels like Amadria Park"
    },
    "Concert Zagreb unknown venue": {
        "city": "Zagreb",
        "venue": "Tvornica Kulture",
        "full_location": "Tvornica Kulture, Zagreb", 
        "confidence": 0.75,
        "reasoning": "Alternative music venues in Zagreb include Tvornica Kulture for contemporary acts"
    }
}

class MockLLMLocationService:
    """Mock LLM service for demonstration purposes."""
    
    def __init__(self):
        self.enabled = True
        self._cache = {}
    
    async def extract_location(self, title: str, description: str = "", context: str = ""):
        """Mock LLM location extraction."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Check cache first
        cache_key = f"{title}|{description}|{context}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Find best matching mock response
        for key, response in MOCK_LLM_RESPONSES.items():
            if any(word in title.lower() for word in key.lower().split()):
                result = MockLocationResult(**response)
                self._cache[cache_key] = result
                return result
        
        # Default fallback
        return MockLocationResult(
            city="Zagreb",
            venue=None,
            full_location="Zagreb", 
            confidence=0.3,
            reasoning="Could not determine specific venue from provided information"
        )

class MockLocationResult:
    """Mock location result for demonstration."""
    
    def __init__(self, city=None, venue=None, full_location=None, confidence=0.0, reasoning=None):
        self.city = city
        self.venue = venue  
        self.full_location = full_location
        self.confidence = confidence
        self.reasoning = reasoning

async def test_llm_location_extraction():
    """Test the enhanced location extraction system."""
    
    llm_service = MockLLMLocationService()
    
    # Test cases with problematic events
    test_events = [
        {
            "title": "Ultra Europe Festival 2025",
            "description": "The biggest electronic music festival in Croatia",
            "current_location": "Zagreb, Croatia",  # Wrong!
        },
        {
            "title": "Amira Medunjanin Concert", 
            "description": "Traditional Bosnian music in beautiful historic venue",
            "current_location": "Zagreb, Croatia",  # Wrong!
        },
        {
            "title": "Jim Jefferies Live In Zagreb",
            "description": "Stand-up comedy show by Australian comedian",
            "current_location": None,  # Missing!
        },
        {
            "title": "Symphonie Gourmet Experience",
            "description": "Fine dining experience with live music in Opatija",
            "current_location": "Opatija",  # Too generic
        },
        {
            "title": "Mysterious Concert Event",
            "description": "Some underground music event in Zagreb",
            "current_location": None,  # Missing venue details
        }
    ]
    
    print("🤖 LLM-Enhanced Location Extraction Test")
    print("=" * 60)
    
    for i, event in enumerate(test_events, 1):
        print(f"\n📍 Test Case {i}: {event['title']}")
        print("-" * 40)
        
        # Current system result
        current = event.get('current_location', 'Unknown')
        print(f"Current Location: {current}")
        
        # LLM enhanced result
        result = await llm_service.extract_location(
            event['title'], 
            event['description']
        )
        
        if result:
            print(f"✨ LLM Enhanced:  {result.full_location}")
            print(f"   Confidence:    {result.confidence:.0%}")
            print(f"   Reasoning:     {result.reasoning}")
            
            # Show improvement
            if current != result.full_location:
                print(f"🎯 IMPROVEMENT: {current} → {result.full_location}")
        else:
            print("❌ LLM extraction failed")

async def test_venue_normalization():
    """Test venue name normalization."""
    
    llm_service = MockLLMLocationService()
    
    print("\n\n🏟️  Venue Name Normalization Test")
    print("=" * 60)
    
    venue_tests = [
        ("Poljud", "Split"),
        ("Arena", "Pula"), 
        ("Dom Sportova", "Zagreb"),
        ("Maksimir", "Zagreb"),
        ("Amadria Park", "Opatija"),
    ]
    
    for venue, city in venue_tests:
        # Mock normalization (in real system this would call LLM)
        normalized = f"{venue} Stadium" if venue == "Poljud" else f"{venue}, {city}"
        print(f"'{venue}' → '{normalized}'")

def demonstrate_geocoding_improvements():
    """Show how the enhanced geocoding database works."""
    
    print("\n\n🗺️  Enhanced Geocoding Database")
    print("=" * 60)
    
    # Sample venue coordinates from our enhanced system
    enhanced_venues = {
        "Poljud Stadium, Split": (43.5133, 16.4439),
        "Arena Pula, Pula": (44.8737, 13.8467), 
        "Small Roman Theatre, Pula": (44.8688, 13.8467),
        "Dom Sportova, Zagreb": (45.7967, 15.9697),
        "Amadria Park Hotel Royal, Opatija": (45.3378, 14.3088),
        "Jarun Lake, Zagreb": (45.7833, 15.9167),
        "Tvornica Kulture, Zagreb": (45.8003, 15.9897),
    }
    
    for venue, (lat, lng) in enhanced_venues.items():
        print(f"{venue:<35} → ({lat:.4f}, {lng:.4f})")

async def main():
    """Run all demonstration tests."""
    
    print("🚀 Phase 2: LLM Location Enhancement Demo")
    print("=" * 80)
    
    await test_llm_location_extraction()
    await test_venue_normalization() 
    demonstrate_geocoding_improvements()
    
    print("\n\n✅ Phase 2 Implementation Summary")
    print("=" * 60)
    print("1. ✅ LLM Service: OpenAI GPT-4 integration with caching")
    print("2. ✅ Smart Extraction: Analyzes event titles + descriptions") 
    print("3. ✅ Venue Normalization: Maps aliases to standard names")
    print("4. ✅ Fallback Integration: Used when basic extraction fails")
    print("5. ✅ Confidence Scoring: Only uses high-confidence results")
    print("6. ✅ Croatian Context: Trained on Croatian venues and cities")
    
    print("\n🎯 Expected Results:")
    print("- Ultra Europe: Zagreb → Poljud Stadium, Split")
    print("- Amira Medunjanin: Zagreb → Small Roman Theatre, Pula")
    print("- Venue-specific coordinates instead of city centers")
    print("- Reduced 'Zagreb, Croatia' fallback positioning")
    
    print("\n🔑 To Enable: Add OPENAI_API_KEY to .env file")

if __name__ == "__main__":
    asyncio.run(main())