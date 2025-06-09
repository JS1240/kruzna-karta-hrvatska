"""
Croatian-specific features: holidays, regional events, currency handling.
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import requests

from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .config import settings

logger = logging.getLogger(__name__)


class CroatianRegion(Enum):
    """Croatian regions (županije) for regional event filtering."""
    ZAGREB_CITY = "grad_zagreb"
    ZAGREB_COUNTY = "zagrebacka"
    KRAPINA_ZAGORJE = "krapinsko_zagorska"
    SISAK_MOSLAVINA = "sisacko_moslavacka"
    KARLOVAC = "karlovacka"
    VARAZDIN = "varazdinska"
    KOPRIVNICA_KRIZEVCI = "koprivnicko_krizevacka"
    BJELOVAR_BILOGORA = "bjelovarsko_bilogorska"
    PRIMORJE_GORSKI_KOTAR = "primorsko_goranska"
    LIKA_SENJ = "licko_senjska"
    VIROVITICA_PODRAVINA = "viroviticko_podravska"
    POZEGA_SLAVONIA = "pozega_slavonska"
    BROD_POSAVINA = "brodsko_posavska"
    ZADAR = "zadarska"
    OSIJEK_BARANJA = "osjecko_baranjska"
    SIBENIK_KNIN = "sibensko_kninska"
    VUKOVAR_SRIJEM = "vukovarsko_srijemska"
    SPLIT_DALMATIA = "splitsko_dalmatinska"
    ISTRIA = "istarska"
    DUBROVNIK_NERETVA = "dubrovnicko_neretvanska"
    MEDJIMURJE = "medjimurska"


class CroatianHolidayType(Enum):
    """Types of Croatian holidays."""
    NATIONAL = "national"           # National holidays (work-free days)
    RELIGIOUS = "religious"         # Religious holidays
    CULTURAL = "cultural"          # Cultural celebrations
    REGIONAL = "regional"          # Regional/local holidays
    INTERNATIONAL = "international" # International days celebrated in Croatia


class CurrencyType(Enum):
    """Supported currencies for Croatian market."""
    EUR = "EUR"  # Euro (official currency since 2023)
    USD = "USD"  # US Dollar (for international events)
    GBP = "GBP"  # British Pound
    CHF = "CHF"  # Swiss Franc (neighboring country)


@dataclass
class CroatianHoliday:
    """Croatian holiday definition."""
    name: str
    name_hr: str
    date: date
    holiday_type: CroatianHolidayType
    is_work_free: bool
    description: str
    description_hr: str
    regions: Optional[List[CroatianRegion]] = None  # For regional holidays


@dataclass
class RegionalEventInfo:
    """Regional event information for Croatian locations."""
    region: CroatianRegion
    region_name_hr: str
    region_name_en: str
    major_cities: List[str]
    cultural_highlights: List[str]
    typical_events: List[str]
    tourism_season: str
    coordinates: Tuple[float, float]  # (latitude, longitude)


@dataclass
class CurrencyRate:
    """Currency exchange rate information."""
    from_currency: str
    to_currency: str
    rate: float
    last_updated: datetime
    source: str


class CroatianHolidayService:
    """Service for managing Croatian holidays and cultural events."""
    
    def __init__(self):
        self.holidays_cache = {}
        self.cache_expiry = datetime.now() + timedelta(hours=24)
        
        # Croatian national holidays (fixed and variable dates)
        self.national_holidays = [
            # Fixed date holidays
            ("Nova godina", "New Year's Day", 1, 1, True),
            ("Bogojavljenje", "Epiphany", 1, 6, True),
            ("Praznik rada", "Labour Day", 5, 1, True),
            ("Dan državnosti", "Statehood Day", 5, 30, True),
            ("Dan antifašističke borbe", "Anti-Fascist Struggle Day", 6, 22, True),
            ("Dan domovinske zahvalnosti", "Homeland Thanksgiving Day", 8, 5, True),
            ("Velika Gospa", "Assumption of Mary", 8, 15, True),
            ("Dan neovisnosti", "Independence Day", 10, 8, True),
            ("Dan svih svetih", "All Saints' Day", 11, 1, True),
            ("Božić", "Christmas Day", 12, 25, True),
            ("Sveti Stjepan", "St. Stephen's Day", 12, 26, True),
        ]
        
        # Regional information
        self.regional_info = {
            CroatianRegion.ZAGREB_CITY: RegionalEventInfo(
                region=CroatianRegion.ZAGREB_CITY,
                region_name_hr="Grad Zagreb",
                region_name_en="Zagreb City",
                major_cities=["Zagreb"],
                cultural_highlights=["Zagreb Cathedral", "Upper Town", "Dolac Market"],
                typical_events=["Zagreb Film Festival", "Advent u Zagrebu", "Zagreb Classic"],
                tourism_season="year_round",
                coordinates=(45.8150, 15.9819)
            ),
            CroatianRegion.SPLIT_DALMATIA: RegionalEventInfo(
                region=CroatianRegion.SPLIT_DALMATIA,
                region_name_hr="Splitsko-dalmatinska županija",
                region_name_en="Split-Dalmatia County",
                major_cities=["Split", "Kaštela", "Solin", "Trogir"],
                cultural_highlights=["Diocletian's Palace", "Riva Promenade", "Marjan Hill"],
                typical_events=["Split Summer Festival", "Ultra Europe", "Split Film Festival"],
                tourism_season="summer_peak",
                coordinates=(43.5081, 16.4402)
            ),
            CroatianRegion.ISTRIA: RegionalEventInfo(
                region=CroatianRegion.ISTRIA,
                region_name_hr="Istarska županija",
                region_name_en="Istria County",
                major_cities=["Pula", "Rovinj", "Poreč", "Umag"],
                cultural_highlights=["Pula Arena", "Rovinj Old Town", "Euphrasian Basilica"],
                typical_events=["Pula Film Festival", "Outlook Festival", "Istria Gourmet Festival"],
                tourism_season="summer_peak",
                coordinates=(45.1667, 13.8333)
            ),
            CroatianRegion.DUBROVNIK_NERETVA: RegionalEventInfo(
                region=CroatianRegion.DUBROVNIK_NERETVA,
                region_name_hr="Dubrovačko-neretvanska županija",
                region_name_en="Dubrovnik-Neretva County",
                major_cities=["Dubrovnik", "Korčula", "Ston"],
                cultural_highlights=["Dubrovnik City Walls", "Game of Thrones locations", "Rector's Palace"],
                typical_events=["Dubrovnik Summer Festival", "Korčula Music Festival", "Good Food Festival"],
                tourism_season="summer_peak",
                coordinates=(42.6507, 18.0944)
            )
        }
        
        logger.info("Croatian holiday service initialized")
    
    def get_croatian_holidays(self, year: int) -> List[CroatianHoliday]:
        """Get all Croatian holidays for a specific year."""
        cache_key = f"holidays_{year}"
        
        if (cache_key in self.holidays_cache and 
            datetime.now() < self.cache_expiry):
            return self.holidays_cache[cache_key]
        
        holidays = []
        
        # Add fixed national holidays
        for name_hr, name_en, month, day, is_work_free in self.national_holidays:
            holiday_date = date(year, month, day)
            holidays.append(CroatianHoliday(
                name=name_en,
                name_hr=name_hr,
                date=holiday_date,
                holiday_type=CroatianHolidayType.NATIONAL,
                is_work_free=is_work_free,
                description=f"Croatian national holiday: {name_en}",
                description_hr=f"Hrvatski nacionalni praznik: {name_hr}"
            ))
        
        # Add variable holidays (Easter-based)
        easter_date = self._calculate_easter(year)
        
        # Easter Monday (Uskrsni ponedjeljak)
        easter_monday = easter_date + timedelta(days=1)
        holidays.append(CroatianHoliday(
            name="Easter Monday",
            name_hr="Uskrsni ponedjeljak",
            date=easter_monday,
            holiday_type=CroatianHolidayType.RELIGIOUS,
            is_work_free=True,
            description="Easter Monday - Croatian public holiday",
            description_hr="Uskrsni ponedjeljak - hrvatski državni praznik"
        ))
        
        # Corpus Christi (Tijelovo) - 60 days after Easter
        corpus_christi = easter_date + timedelta(days=60)
        holidays.append(CroatianHoliday(
            name="Corpus Christi",
            name_hr="Tijelovo",
            date=corpus_christi,
            holiday_type=CroatianHolidayType.RELIGIOUS,
            is_work_free=True,
            description="Corpus Christi - Croatian public holiday",
            description_hr="Tijelovo - hrvatski državni praznik"
        ))
        
        # Add cultural celebrations
        cultural_holidays = self._get_cultural_holidays(year)
        holidays.extend(cultural_holidays)
        
        # Sort by date
        holidays.sort(key=lambda h: h.date)
        
        # Cache the results
        self.holidays_cache[cache_key] = holidays
        
        return holidays
    
    def _calculate_easter(self, year: int) -> date:
        """Calculate Easter date using the Western (Gregorian) calendar."""
        # Algorithm for calculating Easter (Gregorian calendar)
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        
        return date(year, month, day)
    
    def _get_cultural_holidays(self, year: int) -> List[CroatianHoliday]:
        """Get Croatian cultural celebrations and observances."""
        cultural_holidays = []
        
        # Cultural celebrations
        celebrations = [
            ("Dan žena", "International Women's Day", 3, 8, CroatianHolidayType.INTERNATIONAL),
            ("Dan planeta Zemlje", "Earth Day", 4, 22, CroatianHolidayType.INTERNATIONAL),
            ("Dan Europe", "Europe Day", 5, 9, CroatianHolidayType.INTERNATIONAL),
            ("Dan državnog himna", "National Anthem Day", 6, 29, CroatianHolidayType.CULTURAL),
            ("Dan hrvatskog kazališta", "Croatian Theatre Day", 10, 14, CroatianHolidayType.CULTURAL),
            ("Dan hrvatskog filmskog stvaralaštva", "Croatian Film Day", 12, 21, CroatianHolidayType.CULTURAL),
        ]
        
        for name_hr, name_en, month, day, holiday_type in celebrations:
            holiday_date = date(year, month, day)
            cultural_holidays.append(CroatianHoliday(
                name=name_en,
                name_hr=name_hr,
                date=holiday_date,
                holiday_type=holiday_type,
                is_work_free=False,
                description=f"Croatian cultural observance: {name_en}",
                description_hr=f"Hrvatsko kulturno obilježavanje: {name_hr}"
            ))
        
        return cultural_holidays
    
    def is_croatian_holiday(self, check_date: date) -> Optional[CroatianHoliday]:
        """Check if a given date is a Croatian holiday."""
        holidays = self.get_croatian_holidays(check_date.year)
        
        for holiday in holidays:
            if holiday.date == check_date:
                return holiday
        
        return None
    
    def get_upcoming_holidays(self, days_ahead: int = 30) -> List[CroatianHoliday]:
        """Get upcoming Croatian holidays within specified days."""
        current_date = date.today()
        end_date = current_date + timedelta(days=days_ahead)
        
        upcoming_holidays = []
        
        # Check current year and next year if needed
        years_to_check = [current_date.year]
        if end_date.year != current_date.year:
            years_to_check.append(end_date.year)
        
        for year in years_to_check:
            holidays = self.get_croatian_holidays(year)
            for holiday in holidays:
                if current_date <= holiday.date <= end_date:
                    upcoming_holidays.append(holiday)
        
        return sorted(upcoming_holidays, key=lambda h: h.date)
    
    def get_regional_info(self, region: CroatianRegion) -> Optional[RegionalEventInfo]:
        """Get regional information for Croatian counties."""
        return self.regional_info.get(region)
    
    def get_region_by_city(self, city: str) -> Optional[CroatianRegion]:
        """Determine Croatian region based on city name."""
        city_lower = city.lower()
        
        # Map major cities to regions
        city_to_region = {
            "zagreb": CroatianRegion.ZAGREB_CITY,
            "split": CroatianRegion.SPLIT_DALMATIA,
            "rijeka": CroatianRegion.PRIMORJE_GORSKI_KOTAR,
            "osijek": CroatianRegion.OSIJEK_BARANJA,
            "zadar": CroatianRegion.ZADAR,
            "pula": CroatianRegion.ISTRIA,
            "slavonski brod": CroatianRegion.BROD_POSAVINA,
            "karlovac": CroatianRegion.KARLOVAC,
            "varaždin": CroatianRegion.VARAZDIN,
            "šibenik": CroatianRegion.SIBENIK_KNIN,
            "dubrovnik": CroatianRegion.DUBROVNIK_NERETVA,
            "bjelovar": CroatianRegion.BJELOVAR_BILOGORA,
            "vukovar": CroatianRegion.VUKOVAR_SRIJEM,
            "velika gorica": CroatianRegion.ZAGREB_COUNTY,
            "čakovec": CroatianRegion.MEDJIMURJE,
            "koprivnica": CroatianRegion.KOPRIVNICA_KRIZEVCI,
            "požega": CroatianRegion.POZEGA_SLAVONIA,
            "virovitica": CroatianRegion.VIROVITICA_PODRAVINA,
            "gospić": CroatianRegion.LIKA_SENJ,
            "sisak": CroatianRegion.SISAK_MOSLAVINA,
            "krapina": CroatianRegion.KRAPINA_ZAGORJE,
            "rovinj": CroatianRegion.ISTRIA,
            "poreč": CroatianRegion.ISTRIA,
            "kaštela": CroatianRegion.SPLIT_DALMATIA,
            "trogir": CroatianRegion.SPLIT_DALMATIA,
            "korčula": CroatianRegion.DUBROVNIK_NERETVA,
        }
        
        for city_name, region in city_to_region.items():
            if city_name in city_lower:
                return region
        
        return None
    
    def get_seasonal_events_recommendation(self, region: CroatianRegion, month: int) -> List[str]:
        """Get seasonal event recommendations for Croatian regions."""
        region_info = self.get_regional_info(region)
        if not region_info:
            return []
        
        # Summer events (June-September)
        if 6 <= month <= 9:
            if region in [CroatianRegion.SPLIT_DALMATIA, CroatianRegion.ISTRIA, CroatianRegion.DUBROVNIK_NERETVA]:
                return [
                    "Outdoor concerts",
                    "Beach festivals", 
                    "Wine tasting events",
                    "Cultural heritage tours",
                    "Summer theater performances"
                ]
            else:
                return [
                    "Open-air festivals",
                    "Traditional folk events",
                    "Sports competitions",
                    "Cultural celebrations"
                ]
        
        # Winter events (December-February)
        elif month in [12, 1, 2]:
            if region == CroatianRegion.ZAGREB_CITY:
                return [
                    "Advent Zagreb events",
                    "Christmas markets",
                    "New Year celebrations",
                    "Winter cultural events"
                ]
            else:
                return [
                    "Christmas celebrations",
                    "New Year events",
                    "Indoor cultural events",
                    "Traditional winter festivals"
                ]
        
        # Spring/Autumn events
        else:
            return [
                "Cultural festivals",
                "Food and wine events",
                "Art exhibitions",
                "Music concerts",
                "Local celebrations"
            ]


class CroatianCurrencyService:
    """Service for handling Croatian currency and exchange rates."""
    
    def __init__(self):
        self.base_currency = CurrencyType.EUR  # Croatia adopted Euro in 2023
        self.exchange_rates = {}
        self.rate_cache_expiry = datetime.now()
        
        # Croatian National Bank API for official rates
        self.cnb_api_url = "https://api.hnb.hr/tecajn-eur/v3"
        
        # Fallback exchange rates (approximate)
        self.fallback_rates = {
            "USD": 1.10,  # EUR to USD
            "GBP": 0.85,  # EUR to GBP  
            "CHF": 0.95,  # EUR to CHF
        }
        
        logger.info("Croatian currency service initialized")
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies."""
        if from_currency == to_currency:
            return 1.0
        
        # Update rates if cache expired
        if datetime.now() > self.rate_cache_expiry:
            self._update_exchange_rates()
        
        # Try to get rate from cache
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in self.exchange_rates:
            return self.exchange_rates[rate_key]
        
        # Try reverse rate
        reverse_key = f"{to_currency}_{from_currency}"
        if reverse_key in self.exchange_rates:
            return 1.0 / self.exchange_rates[reverse_key]
        
        # Use fallback rates
        if from_currency == "EUR" and to_currency in self.fallback_rates:
            return self.fallback_rates[to_currency]
        elif to_currency == "EUR" and from_currency in self.fallback_rates:
            return 1.0 / self.fallback_rates[from_currency]
        
        logger.warning(f"No exchange rate found for {from_currency} to {to_currency}")
        return None
    
    def _update_exchange_rates(self):
        """Update exchange rates from Croatian National Bank."""
        try:
            # Fetch from Croatian National Bank API
            response = requests.get(self.cnb_api_url, timeout=10)
            response.raise_for_status()
            
            rates_data = response.json()
            
            # Parse CNB response
            for rate_info in rates_data:
                currency_code = rate_info.get("valuta")
                rate_value = float(rate_info.get("srednji_tecaj", 0))
                
                if currency_code and rate_value > 0:
                    # CNB provides EUR to other currency rates
                    self.exchange_rates[f"EUR_{currency_code}"] = rate_value
            
            # Set cache expiry for 1 hour
            self.rate_cache_expiry = datetime.now() + timedelta(hours=1)
            
            logger.info("Exchange rates updated from Croatian National Bank")
            
        except Exception as e:
            logger.error(f"Failed to update exchange rates from CNB: {e}")
            
            # Use fallback rates
            for currency, rate in self.fallback_rates.items():
                self.exchange_rates[f"EUR_{currency}"] = rate
            
            # Set shorter cache expiry for fallback rates
            self.rate_cache_expiry = datetime.now() + timedelta(minutes=30)
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Convert amount from one currency to another."""
        rate = self.get_exchange_rate(from_currency, to_currency)
        if rate is None:
            return None
        
        return round(amount * rate, 2)
    
    def format_croatian_price(self, amount: float, currency: str = "EUR") -> str:
        """Format price in Croatian style."""
        if currency == "EUR":
            return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")
        elif currency == "USD":
            return f"${amount:,.2f}".replace(",", " ")
        else:
            return f"{amount:,.2f} {currency}".replace(",", " ").replace(".", ",")
    
    def get_supported_currencies(self) -> List[Dict[str, str]]:
        """Get list of supported currencies for Croatian market."""
        return [
            {"code": "EUR", "name": "Euro", "name_hr": "Euro", "symbol": "€"},
            {"code": "USD", "name": "US Dollar", "name_hr": "Američki dolar", "symbol": "$"},
            {"code": "GBP", "name": "British Pound", "name_hr": "Britanska funta", "symbol": "£"},
            {"code": "CHF", "name": "Swiss Franc", "name_hr": "Švicarski franak", "symbol": "CHF"},
        ]


class CroatianEventsService:
    """Service for Croatian-specific event management."""
    
    def __init__(self):
        self.holiday_service = CroatianHolidayService()
        self.currency_service = CroatianCurrencyService()
        
        logger.info("Croatian events service initialized")
    
    def enrich_event_with_croatian_context(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich event data with Croatian cultural context."""
        enriched_event = event_data.copy()
        
        # Add holiday context
        event_date = event_data.get("date")
        if event_date:
            if isinstance(event_date, str):
                event_date = datetime.fromisoformat(event_date).date()
            
            holiday = self.holiday_service.is_croatian_holiday(event_date)
            if holiday:
                enriched_event["croatian_holiday"] = {
                    "name": holiday.name,
                    "name_hr": holiday.name_hr,
                    "type": holiday.holiday_type.value,
                    "is_work_free": holiday.is_work_free,
                    "description_hr": holiday.description_hr
                }
        
        # Add regional context
        location = event_data.get("location", "")
        if location:
            # Extract city from location
            city = location.split(",")[0].strip()
            region = self.holiday_service.get_region_by_city(city)
            
            if region:
                region_info = self.holiday_service.get_regional_info(region)
                if region_info:
                    enriched_event["croatian_region"] = {
                        "region": region.value,
                        "name_hr": region_info.region_name_hr,
                        "name_en": region_info.region_name_en,
                        "cultural_highlights": region_info.cultural_highlights,
                        "tourism_season": region_info.tourism_season
                    }
        
        # Add seasonal recommendations
        if event_date:
            month = event_date.month
            region = self.holiday_service.get_region_by_city(location.split(",")[0].strip()) if location else None
            
            if region:
                seasonal_recommendations = self.holiday_service.get_seasonal_events_recommendation(region, month)
                enriched_event["seasonal_context"] = {
                    "month": month,
                    "season_type": self._get_season_type(month),
                    "recommended_event_types": seasonal_recommendations
                }
        
        # Add currency conversion for price
        price = event_data.get("price")
        if price and isinstance(price, (int, float)):
            original_currency = event_data.get("currency", "EUR")
            
            enriched_event["price_conversions"] = {}
            for currency_info in self.currency_service.get_supported_currencies():
                currency_code = currency_info["code"]
                if currency_code != original_currency:
                    converted_price = self.currency_service.convert_currency(
                        price, original_currency, currency_code
                    )
                    if converted_price:
                        enriched_event["price_conversions"][currency_code] = {
                            "amount": converted_price,
                            "formatted": self.currency_service.format_croatian_price(
                                converted_price, currency_code
                            )
                        }
        
        return enriched_event
    
    def _get_season_type(self, month: int) -> str:
        """Get season type for Croatian calendar."""
        if month in [6, 7, 8]:
            return "peak_summer"
        elif month in [4, 5, 9, 10]:
            return "shoulder_season"
        elif month in [12, 1, 2]:
            return "winter"
        else:
            return "spring_autumn"
    
    def get_croatian_cultural_categories(self) -> List[Dict[str, str]]:
        """Get Croatian-specific event categories."""
        return [
            {
                "name": "Croatian Folk Culture",
                "name_hr": "Hrvatska folklorna kultura",
                "description": "Traditional Croatian music, dance, and cultural events",
                "description_hr": "Tradicionalna hrvatska glazba, ples i kulturni događaji"
            },
            {
                "name": "Klapa Singing",
                "name_hr": "Klapa pjevanje",
                "description": "Traditional Croatian a cappella singing groups",
                "description_hr": "Tradicionalni hrvatski a cappella pjevački ansambli"
            },
            {
                "name": "Croatian Cuisine",
                "name_hr": "Hrvatska kuhinja",
                "description": "Food festivals featuring traditional Croatian dishes",
                "description_hr": "Gastronomski festivali s tradicionalnim hrvatskim jelima"
            },
            {
                "name": "Dalmatian Culture",
                "name_hr": "Dalmatinska kultura",
                "description": "Events celebrating Dalmatian coastal culture",
                "description_hr": "Događaji koji slave dalmatinsku obalnu kulturu"
            },
            {
                "name": "Croatian Film",
                "name_hr": "Hrvatski film",
                "description": "Croatian cinema and film festivals",
                "description_hr": "Hrvatska kinematografija i filmski festivali"
            },
            {
                "name": "Religious Celebrations",
                "name_hr": "Vjerska slavlja",
                "description": "Catholic and other religious celebrations in Croatia",
                "description_hr": "Katolička i druga vjerska slavlja u Hrvatskoj"
            }
        ]
    
    def suggest_croatian_event_timing(self, event_type: str, region: Optional[CroatianRegion] = None) -> Dict[str, Any]:
        """Suggest optimal timing for Croatian events."""
        suggestions = {
            "optimal_months": [],
            "avoid_periods": [],
            "cultural_considerations": [],
            "tourism_impact": ""
        }
        
        # General Croatian event timing
        if "outdoor" in event_type.lower() or "festival" in event_type.lower():
            suggestions["optimal_months"] = [5, 6, 7, 8, 9]  # May to September
            suggestions["avoid_periods"] = ["Christmas period", "Easter period"]
            suggestions["cultural_considerations"] = [
                "Avoid major Croatian holidays",
                "Consider summer vacation period (July-August)",
                "Consider local patron saint days"
            ]
        
        if "cultural" in event_type.lower():
            suggestions["optimal_months"] = [4, 5, 9, 10, 11]  # Spring and autumn
            suggestions["cultural_considerations"] = [
                "Croatian Cultural Day (October 14)",
                "Croatian Theatre Day",
                "Regional cultural celebrations"
            ]
        
        # Regional considerations
        if region in [CroatianRegion.SPLIT_DALMATIA, CroatianRegion.ISTRIA, CroatianRegion.DUBROVNIK_NERETVA]:
            suggestions["tourism_impact"] = "high_summer_tourism"
            suggestions["optimal_months"] = [6, 7, 8, 9]
            suggestions["avoid_periods"].append("Winter months (limited tourism)")
        elif region == CroatianRegion.ZAGREB_CITY:
            suggestions["tourism_impact"] = "year_round_business"
            suggestions["optimal_months"] = [4, 5, 6, 9, 10, 11, 12]
            suggestions["cultural_considerations"].append("Advent in Zagreb (December)")
        
        return suggestions


# Global service instances
croatian_holiday_service = CroatianHolidayService()
croatian_currency_service = CroatianCurrencyService()
croatian_events_service = CroatianEventsService()


def get_croatian_holiday_service() -> CroatianHolidayService:
    """Get Croatian holiday service instance."""
    return croatian_holiday_service


def get_croatian_currency_service() -> CroatianCurrencyService:
    """Get Croatian currency service instance."""
    return croatian_currency_service


def get_croatian_events_service() -> CroatianEventsService:
    """Get Croatian events service instance."""
    return croatian_events_service