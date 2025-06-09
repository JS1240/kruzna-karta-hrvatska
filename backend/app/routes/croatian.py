"""
Croatian-specific features API endpoints.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.auth import get_current_user
from ..core.croatian import (
    CroatianHolidayType,
    CroatianRegion,
    get_croatian_currency_service,
    get_croatian_events_service,
    get_croatian_holiday_service,
)
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/croatian", tags=["croatian"])


@router.get("/holidays")
async def get_croatian_holidays(
    year: int = Query(
        default=None, description="Year to get holidays for (defaults to current year)"
    ),
    holiday_type: Optional[str] = Query(
        default=None,
        description="Filter by holiday type: national, religious, cultural, regional, international",
    ),
    upcoming_only: bool = Query(
        default=False, description="Only return upcoming holidays"
    ),
    days_ahead: int = Query(
        default=30, description="Number of days ahead to look for upcoming holidays"
    ),
) -> Dict[str, Any]:
    """Get Croatian holidays for a specific year or upcoming holidays."""
    try:
        holiday_service = get_croatian_holiday_service()

        if upcoming_only:
            holidays = holiday_service.get_upcoming_holidays(days_ahead)
        else:
            if year is None:
                year = datetime.now().year
            holidays = holiday_service.get_croatian_holidays(year)

        # Filter by type if specified
        if holiday_type:
            try:
                filter_type = CroatianHolidayType(holiday_type.lower())
                holidays = [h for h in holidays if h.holiday_type == filter_type]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid holiday type. Valid types: {[t.value for t in CroatianHolidayType]}",
                )

        # Convert to response format
        holiday_list = []
        for holiday in holidays:
            holiday_list.append(
                {
                    "name": holiday.name,
                    "name_hr": holiday.name_hr,
                    "date": holiday.date.isoformat(),
                    "holiday_type": holiday.holiday_type.value,
                    "is_work_free": holiday.is_work_free,
                    "description": holiday.description,
                    "description_hr": holiday.description_hr,
                    "regions": (
                        [r.value for r in holiday.regions] if holiday.regions else None
                    ),
                }
            )

        return {
            "year": year if not upcoming_only else datetime.now().year,
            "total_holidays": len(holiday_list),
            "upcoming_only": upcoming_only,
            "holidays": holiday_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Croatian holidays: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get holidays: {str(e)}",
        )


@router.get("/holidays/check/{check_date}")
async def check_croatian_holiday(check_date: str) -> Dict[str, Any]:
    """Check if a specific date is a Croatian holiday."""
    try:
        # Parse date
        try:
            date_obj = datetime.fromisoformat(check_date).date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

        holiday_service = get_croatian_holiday_service()
        holiday = holiday_service.is_croatian_holiday(date_obj)

        if holiday:
            return {
                "is_holiday": True,
                "holiday": {
                    "name": holiday.name,
                    "name_hr": holiday.name_hr,
                    "date": holiday.date.isoformat(),
                    "holiday_type": holiday.holiday_type.value,
                    "is_work_free": holiday.is_work_free,
                    "description": holiday.description,
                    "description_hr": holiday.description_hr,
                },
            }
        else:
            return {"is_holiday": False, "holiday": None}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check Croatian holiday: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check holiday: {str(e)}",
        )


@router.get("/regions")
async def get_croatian_regions() -> List[Dict[str, Any]]:
    """Get information about Croatian regions (counties)."""
    try:
        holiday_service = get_croatian_holiday_service()

        regions = []
        for region in CroatianRegion:
            region_info = holiday_service.get_regional_info(region)
            if region_info:
                regions.append(
                    {
                        "code": region.value,
                        "name_hr": region_info.region_name_hr,
                        "name_en": region_info.region_name_en,
                        "major_cities": region_info.major_cities,
                        "cultural_highlights": region_info.cultural_highlights,
                        "typical_events": region_info.typical_events,
                        "tourism_season": region_info.tourism_season,
                        "coordinates": {
                            "latitude": region_info.coordinates[0],
                            "longitude": region_info.coordinates[1],
                        },
                    }
                )

        return regions

    except Exception as e:
        logger.error(f"Failed to get Croatian regions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get regions: {str(e)}",
        )


@router.get("/regions/{region_code}")
async def get_region_info(region_code: str) -> Dict[str, Any]:
    """Get detailed information about a specific Croatian region."""
    try:
        # Find region by code
        region = None
        for r in CroatianRegion:
            if r.value == region_code:
                region = r
                break

        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Region not found: {region_code}",
            )

        holiday_service = get_croatian_holiday_service()
        region_info = holiday_service.get_regional_info(region)

        if not region_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No information available for region: {region_code}",
            )

        # Get seasonal recommendations for current month
        current_month = datetime.now().month
        seasonal_recommendations = holiday_service.get_seasonal_events_recommendation(
            region, current_month
        )

        return {
            "code": region.value,
            "name_hr": region_info.region_name_hr,
            "name_en": region_info.region_name_en,
            "major_cities": region_info.major_cities,
            "cultural_highlights": region_info.cultural_highlights,
            "typical_events": region_info.typical_events,
            "tourism_season": region_info.tourism_season,
            "coordinates": {
                "latitude": region_info.coordinates[0],
                "longitude": region_info.coordinates[1],
            },
            "seasonal_recommendations": {
                "month": current_month,
                "recommended_events": seasonal_recommendations,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get region info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get region info: {str(e)}",
        )


@router.get("/currency/rates")
async def get_exchange_rates() -> Dict[str, Any]:
    """Get current exchange rates for supported currencies."""
    try:
        currency_service = get_croatian_currency_service()
        supported_currencies = currency_service.get_supported_currencies()

        rates = {}
        base_currency = "EUR"

        for currency_info in supported_currencies:
            currency_code = currency_info["code"]
            if currency_code != base_currency:
                rate = currency_service.get_exchange_rate(base_currency, currency_code)
                if rate:
                    rates[currency_code] = {
                        "rate": rate,
                        "name": currency_info["name"],
                        "name_hr": currency_info["name_hr"],
                        "symbol": currency_info["symbol"],
                    }

        return {
            "base_currency": base_currency,
            "last_updated": datetime.now().isoformat(),
            "rates": rates,
            "source": "Croatian National Bank (HNB)",
        }

    except Exception as e:
        logger.error(f"Failed to get exchange rates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exchange rates: {str(e)}",
        )


@router.get("/currency/convert")
async def convert_currency(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency code (e.g., EUR)"),
    to_currency: str = Query(..., description="Target currency code (e.g., USD)"),
) -> Dict[str, Any]:
    """Convert amount between currencies."""
    try:
        currency_service = get_croatian_currency_service()

        # Validate currencies
        supported_codes = [
            c["code"] for c in currency_service.get_supported_currencies()
        ]

        if from_currency not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source currency: {from_currency}. Supported: {supported_codes}",
            )

        if to_currency not in supported_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target currency: {to_currency}. Supported: {supported_codes}",
            )

        # Convert currency
        converted_amount = currency_service.convert_currency(
            amount, from_currency, to_currency
        )

        if converted_amount is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to convert from {from_currency} to {to_currency}",
            )

        # Get exchange rate
        rate = currency_service.get_exchange_rate(from_currency, to_currency)

        return {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": converted_amount,
            "exchange_rate": rate,
            "formatted_original": currency_service.format_croatian_price(
                amount, from_currency
            ),
            "formatted_converted": currency_service.format_croatian_price(
                converted_amount, to_currency
            ),
            "conversion_time": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to convert currency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert currency: {str(e)}",
        )


@router.get("/currency/supported")
async def get_supported_currencies() -> List[Dict[str, str]]:
    """Get list of supported currencies for Croatian market."""
    try:
        currency_service = get_croatian_currency_service()
        return currency_service.get_supported_currencies()

    except Exception as e:
        logger.error(f"Failed to get supported currencies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported currencies: {str(e)}",
        )


@router.post("/events/enrich")
async def enrich_event_with_croatian_context(
    event_data: Dict[str, Any], current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Enrich event data with Croatian cultural context."""
    try:
        events_service = get_croatian_events_service()
        enriched_event = events_service.enrich_event_with_croatian_context(event_data)

        return {
            "status": "success",
            "original_event": event_data,
            "enriched_event": enriched_event,
            "enrichment_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to enrich event with Croatian context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enrich event: {str(e)}",
        )


@router.get("/events/categories")
async def get_croatian_cultural_categories() -> List[Dict[str, str]]:
    """Get Croatian-specific event categories."""
    try:
        events_service = get_croatian_events_service()
        return events_service.get_croatian_cultural_categories()

    except Exception as e:
        logger.error(f"Failed to get Croatian cultural categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}",
        )


@router.get("/events/timing-suggestions")
async def get_event_timing_suggestions(
    event_type: str = Query(
        ..., description="Type of event (e.g., 'outdoor festival', 'cultural event')"
    ),
    region_code: Optional[str] = Query(
        default=None, description="Croatian region code"
    ),
) -> Dict[str, Any]:
    """Get suggestions for optimal event timing in Croatia."""
    try:
        events_service = get_croatian_events_service()

        # Parse region if provided
        region = None
        if region_code:
            for r in CroatianRegion:
                if r.value == region_code:
                    region = r
                    break

            if not region:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid region code: {region_code}",
                )

        suggestions = events_service.suggest_croatian_event_timing(event_type, region)

        return {
            "event_type": event_type,
            "region": region_code,
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event timing suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timing suggestions: {str(e)}",
        )


@router.get("/location/region")
async def get_region_by_city(
    city: str = Query(..., description="City name to lookup region for")
) -> Dict[str, Any]:
    """Get Croatian region information based on city name."""
    try:
        holiday_service = get_croatian_holiday_service()
        region = holiday_service.get_region_by_city(city)

        if not region:
            return {
                "city": city,
                "region": None,
                "message": "Region not found for this city",
            }

        region_info = holiday_service.get_regional_info(region)

        return {
            "city": city,
            "region": {
                "code": region.value,
                "name_hr": region_info.region_name_hr,
                "name_en": region_info.region_name_en,
                "major_cities": region_info.major_cities,
                "tourism_season": region_info.tourism_season,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get region by city: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get region info: {str(e)}",
        )


@router.get("/cultural-info")
async def get_croatian_cultural_info() -> Dict[str, Any]:
    """Get general Croatian cultural information for events platform."""
    try:
        return {
            "country": {
                "name": "Croatia",
                "name_hr": "Hrvatska",
                "capital": "Zagreb",
                "capital_hr": "Zagreb",
                "currency": "EUR",
                "language": "Croatian",
                "language_hr": "Hrvatski",
                "timezone": "Europe/Zagreb",
                "calling_code": "+385",
            },
            "cultural_notes": {
                "greeting": "Pozdravljamo!",
                "business_hours": "08:00-16:00 Monday-Friday",
                "lunch_break": "12:00-13:00 typical lunch break",
                "weekend": "Saturday-Sunday",
                "work_free_holidays": "11 national holidays per year",
            },
            "tourism_info": {
                "peak_season": "June-September",
                "shoulder_season": "April-May, October",
                "off_season": "November-March",
                "major_destinations": [
                    "Zagreb",
                    "Split",
                    "Dubrovnik",
                    "Pula",
                    "Rovinj",
                    "Zadar",
                ],
            },
            "event_traditions": {
                "summer_festivals": "Outdoor festivals along the coast",
                "winter_celebrations": "Advent markets in Zagreb",
                "cultural_events": "Film festivals, music festivals",
                "religious_celebrations": "Catholic traditions predominant",
                "folk_culture": "Klapa singing, traditional dances",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get Croatian cultural info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cultural info: {str(e)}",
        )
