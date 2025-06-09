from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime, date

from ..core.database import get_db
from ..core.venue_service import VenueManagementService
from ..models.user import User
from ..models.venue_management import (
    EnhancedVenue as EnhancedVenueModel, 
    VenueAvailability as VenueAvailabilityModel, 
    VenueReview as VenueReviewModel
)
from ..models.venue_schemas import (
    EnhancedVenue, EnhancedVenueCreate, EnhancedVenueUpdate, VenueSearchParams,
    Facility, FacilityCreate, FacilityUpdate, VenueFacilityCreate,
    VenueAvailability, VenueAvailabilityCreate, VenueAvailabilityUpdate, AvailabilitySearchParams,
    VenueBooking, VenueBookingCreate, VenueBookingUpdate, BookingSearchParams,
    VenueReview, VenueReviewCreate, VenueReviewUpdate,
    VenueImage, VenueImageCreate, VenueImageUpdate,
    VenueListResponse, VenueAvailabilityResponse, VenueBookingResponse, VenueReviewResponse,
    FacilityResponse, VenueStatistics
)
from ..routes.auth import get_current_user

router = APIRouter(prefix="/venue-management", tags=["Venue Management"])


# Venue Endpoints
@router.post("/venues", response_model=EnhancedVenue, status_code=status.HTTP_201_CREATED)
def create_venue(
    venue_data: EnhancedVenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new venue"""
    service = VenueManagementService(db)
    return service.create_venue(venue_data, current_user.id)


@router.get("/venues/{venue_id}", response_model=EnhancedVenue)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Get venue by ID"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.get("/venues/slug/{slug}", response_model=EnhancedVenue)
def get_venue_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get venue by slug"""
    service = VenueManagementService(db)
    venue = service.get_venue_by_slug(slug)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.put("/venues/{venue_id}", response_model=EnhancedVenue)
def update_venue(
    venue_id: int,
    venue_data: EnhancedVenueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update venue information"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check permissions (owner or manager)
    if venue.owner_id != current_user.id and venue.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this venue")
    
    updated_venue = service.update_venue(venue_id, venue_data)
    return updated_venue


@router.delete("/venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (deactivate) venue"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check permissions (owner only)
    if venue.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only venue owner can delete venue")
    
    success = service.delete_venue(venue_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete venue")


@router.get("/venues", response_model=VenueListResponse)
def search_venues(
    q: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    venue_type: Optional[str] = None,
    min_capacity: Optional[int] = Query(None, ge=1),
    max_capacity: Optional[int] = Query(None, ge=1),
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = Query(None, gt=0),
    max_price_per_hour: Optional[float] = Query(None, ge=0),
    max_price_per_day: Optional[float] = Query(None, ge=0),
    has_parking: Optional[bool] = None,
    has_catering: Optional[bool] = None,
    has_av_equipment: Optional[bool] = None,
    is_accessible: Optional[bool] = None,
    available_from: Optional[datetime] = None,
    available_to: Optional[datetime] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db)
):
    """Search venues with advanced filtering"""
    search_params = VenueSearchParams(
        q=q, city=city, region=region, venue_type=venue_type,
        min_capacity=min_capacity, max_capacity=max_capacity,
        latitude=latitude, longitude=longitude, radius_km=radius_km,
        max_price_per_hour=max_price_per_hour, max_price_per_day=max_price_per_day,
        has_parking=has_parking, has_catering=has_catering,
        has_av_equipment=has_av_equipment, is_accessible=is_accessible,
        available_from=available_from, available_to=available_to,
        min_rating=min_rating, page=page, size=size,
        sort_by=sort_by, sort_order=sort_order
    )
    
    service = VenueManagementService(db)
    venues, total = service.search_venues(search_params)
    
    pages = (total + size - 1) // size
    
    return VenueListResponse(
        venues=venues,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/venues/{venue_id}/statistics", response_model=VenueStatistics)
def get_venue_statistics(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive venue statistics"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check permissions (owner or manager)
    if venue.owner_id != current_user.id and venue.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view venue statistics")
    
    stats = service.get_venue_statistics(venue_id)
    return VenueStatistics(**stats)


# Facility Endpoints
@router.post("/facilities", response_model=Facility, status_code=status.HTTP_201_CREATED)
def create_facility(
    facility_data: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new facility type (admin only)"""
    # TODO: Add admin permission check
    service = VenueManagementService(db)
    return service.create_facility(facility_data.dict())


@router.get("/facilities", response_model=FacilityResponse)
def get_facilities(db: Session = Depends(get_db)):
    """Get all available facilities"""
    service = VenueManagementService(db)
    facilities = service.get_facilities()
    return FacilityResponse(facilities=facilities, total=len(facilities))


@router.post("/venues/{venue_id}/facilities")
def add_venue_facility(
    venue_id: int,
    facility_data: VenueFacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add facility to venue"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check permissions
    if venue.owner_id != current_user.id and venue.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify venue facilities")
    
    success = service.add_venue_facility(
        venue_id, 
        facility_data.facility_id,
        notes=facility_data.notes,
        is_included=facility_data.is_included,
        additional_cost=facility_data.additional_cost
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Facility already added or invalid")
    
    return {"message": "Facility added to venue"}


@router.delete("/venues/{venue_id}/facilities/{facility_id}")
def remove_venue_facility(
    venue_id: int,
    facility_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove facility from venue"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check permissions
    if venue.owner_id != current_user.id and venue.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify venue facilities")
    
    success = service.remove_venue_facility(venue_id, facility_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Facility not found on venue")
    
    return {"message": "Facility removed from venue"}


@router.get("/venues/{venue_id}/facilities")
def get_venue_facilities(venue_id: int, db: Session = Depends(get_db)):
    """Get all facilities for a venue"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    facilities = service.get_venue_facilities(venue_id)
    return {"facilities": facilities}


# Availability Endpoints
@router.post("/venues/{venue_id}/availability", response_model=VenueAvailability, status_code=status.HTTP_201_CREATED)
def create_availability_slot(
    venue_id: int,
    availability_data: VenueAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create availability slot"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check permissions
    if venue.owner_id != current_user.id and venue.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage venue availability")
    
    # Ensure venue_id matches
    availability_data.venue_id = venue_id
    
    return service.create_availability_slot(availability_data)


@router.get("/venues/{venue_id}/availability", response_model=VenueAvailabilityResponse)
def get_venue_availability(
    venue_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Get venue availability for date range"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    availability_slots = service.get_venue_availability(venue_id, start_date, end_date)
    
    return VenueAvailabilityResponse(
        availability_slots=availability_slots,
        total=len(availability_slots)
    )


@router.put("/availability/{availability_id}", response_model=VenueAvailability)
def update_availability_slot(
    availability_id: int,
    availability_data: VenueAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update availability slot"""
    service = VenueManagementService(db)
    availability = db.query(VenueAvailabilityModel).filter(VenueAvailabilityModel.id == availability_id).first()
    
    if not availability:
        raise HTTPException(status_code=404, detail="Availability slot not found")
    
    venue = service.get_venue(availability.venue_id)
    
    # Check permissions
    if venue.owner_id != current_user.id and venue.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify venue availability")
    
    updated_availability = service.update_availability_slot(availability_id, availability_data)
    return updated_availability


@router.get("/venues/{venue_id}/check-availability")
def check_venue_availability(
    venue_id: int,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db)
):
    """Check if venue is available for specified time"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    is_available = service.check_availability(venue_id, start_time, end_time)
    
    return {
        "venue_id": venue_id,
        "start_time": start_time,
        "end_time": end_time,
        "is_available": is_available
    }


# Booking Endpoints
@router.post("/venues/{venue_id}/bookings", response_model=VenueBooking, status_code=status.HTTP_201_CREATED)
def create_venue_booking(
    venue_id: int,
    booking_data: VenueBookingCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create venue booking"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check availability
    is_available = service.check_availability(venue_id, booking_data.start_datetime, booking_data.end_datetime)
    if not is_available:
        raise HTTPException(status_code=400, detail="Venue not available for selected time")
    
    # Ensure venue_id matches
    booking_data.venue_id = venue_id
    
    customer_id = current_user.id if current_user else None
    return service.create_booking(booking_data, customer_id)


@router.get("/bookings/{booking_id}", response_model=VenueBooking)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Get booking by ID"""
    service = VenueManagementService(db)
    booking = service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return booking


@router.get("/bookings/reference/{booking_reference}", response_model=VenueBooking)
def get_booking_by_reference(booking_reference: str, db: Session = Depends(get_db)):
    """Get booking by reference"""
    service = VenueManagementService(db)
    booking = service.get_booking_by_reference(booking_reference)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return booking


@router.put("/bookings/{booking_id}", response_model=VenueBooking)
def update_booking(
    booking_id: int,
    booking_data: VenueBookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update booking"""
    service = VenueManagementService(db)
    booking = service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check permissions (customer, venue owner, or venue manager)
    venue = service.get_venue(booking.venue_id)
    if (booking.customer_id != current_user.id and 
        venue.owner_id != current_user.id and 
        venue.manager_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to modify this booking")
    
    updated_booking = service.update_booking(booking_id, booking_data)
    return updated_booking


@router.post("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel booking"""
    service = VenueManagementService(db)
    booking = service.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check permissions
    venue = service.get_venue(booking.venue_id)
    if (booking.customer_id != current_user.id and 
        venue.owner_id != current_user.id and 
        venue.manager_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
    
    success = service.cancel_booking(booking_id, reason)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel booking")
    
    return {"message": "Booking cancelled successfully"}


@router.get("/bookings", response_model=VenueBookingResponse)
def search_bookings(
    venue_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    booking_status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search bookings with filters"""
    search_params = BookingSearchParams(
        venue_id=venue_id,
        customer_id=customer_id,
        booking_status=booking_status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size
    )
    
    service = VenueManagementService(db)
    bookings, total = service.search_bookings(search_params)
    
    # Filter results based on user permissions
    if venue_id:
        venue = service.get_venue(venue_id)
        if venue and (venue.owner_id != current_user.id and venue.manager_id != current_user.id):
            # User can only see their own bookings
            bookings = [b for b in bookings if b.customer_id == current_user.id]
            total = len(bookings)
    else:
        # User can only see their own bookings unless they're venue owners/managers
        user_venues = [v.id for v in db.query(EnhancedVenueModel).filter(
            or_(EnhancedVenueModel.owner_id == current_user.id, EnhancedVenueModel.manager_id == current_user.id)
        ).all()]
        
        bookings = [b for b in bookings if b.customer_id == current_user.id or b.venue_id in user_venues]
        total = len(bookings)
    
    pages = (total + size - 1) // size
    
    return VenueBookingResponse(
        bookings=bookings,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


# Review Endpoints
@router.post("/venues/{venue_id}/reviews", response_model=VenueReview, status_code=status.HTTP_201_CREATED)
def create_venue_review(
    venue_id: int,
    review_data: VenueReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create venue review"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Ensure venue_id matches
    review_data.venue_id = venue_id
    
    return service.create_review(review_data, current_user.id)


@router.get("/venues/{venue_id}/reviews", response_model=VenueReviewResponse)
def get_venue_reviews(
    venue_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get venue reviews"""
    service = VenueManagementService(db)
    venue = service.get_venue(venue_id)
    
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    offset = (page - 1) * size
    reviews, total = service.get_venue_reviews(venue_id, size, offset)
    
    # Calculate rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        count = db.query(VenueReviewModel).filter(
            and_(VenueReviewModel.venue_id == venue_id, VenueReviewModel.rating == i, VenueReviewModel.is_public == True)
        ).count()
        rating_distribution[i] = count
    
    return VenueReviewResponse(
        reviews=reviews,
        total=total,
        average_rating=float(venue.average_rating) if venue.average_rating else None,
        rating_distribution=rating_distribution
    )


@router.put("/reviews/{review_id}", response_model=VenueReview)
def update_review(
    review_id: int,
    review_data: VenueReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update review or add venue response"""
    service = VenueManagementService(db)
    review = db.query(VenueReviewModel).filter(VenueReviewModel.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check permissions
    venue = service.get_venue(review.venue_id)
    is_review_author = review.user_id == current_user.id
    is_venue_manager = venue.owner_id == current_user.id or venue.manager_id == current_user.id
    
    if not (is_review_author or is_venue_manager):
        raise HTTPException(status_code=403, detail="Not authorized to modify this review")
    
    # Venue managers can only add responses
    if is_venue_manager and not is_review_author:
        if any(field in review_data.dict(exclude_unset=True) for field in ['rating', 'title', 'review_text']):
            raise HTTPException(status_code=403, detail="Venue managers can only add responses")
    
    updated_review = service.update_review(review_id, review_data)
    return updated_review