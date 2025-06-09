from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, extract
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import logging
from math import radians, cos, sin, asin, sqrt

from ..models.venue_management import (
    EnhancedVenue, Facility, VenueAvailability, VenueBooking, 
    VenueReview, VenueImage, VenuePricingRule, VenueMaintenanceLog,
    venue_facilities, VenueStatus, AvailabilityStatus, BookingStatus
)
from ..models.venue_schemas import (
    EnhancedVenueCreate, EnhancedVenueUpdate, VenueSearchParams,
    VenueAvailabilityCreate, VenueAvailabilityUpdate, AvailabilitySearchParams,
    VenueBookingCreate, VenueBookingUpdate, BookingSearchParams,
    VenueReviewCreate, VenueReviewUpdate
)

logger = logging.getLogger(__name__)


class VenueManagementService:
    """Comprehensive venue management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Venue Management
    def create_venue(self, venue_data: EnhancedVenueCreate, owner_id: int) -> EnhancedVenue:
        """Create a new venue"""
        # Generate slug from venue name
        slug = self._generate_slug(venue_data.name)
        
        venue = EnhancedVenue(
            **venue_data.dict(),
            slug=slug,
            owner_id=owner_id
        )
        
        self.db.add(venue)
        self.db.commit()
        self.db.refresh(venue)
        
        logger.info(f"Created venue: {venue.name} (ID: {venue.id})")
        return venue
    
    def get_venue(self, venue_id: int) -> Optional[EnhancedVenue]:
        """Get venue by ID"""
        return self.db.query(EnhancedVenue).filter(EnhancedVenue.id == venue_id).first()
    
    def get_venue_by_slug(self, slug: str) -> Optional[EnhancedVenue]:
        """Get venue by slug"""
        return self.db.query(EnhancedVenue).filter(EnhancedVenue.slug == slug).first()
    
    def update_venue(self, venue_id: int, venue_data: EnhancedVenueUpdate) -> Optional[EnhancedVenue]:
        """Update venue information"""
        venue = self.get_venue(venue_id)
        if not venue:
            return None
        
        update_data = venue_data.dict(exclude_unset=True)
        
        # Update slug if name changed
        if 'name' in update_data:
            update_data['slug'] = self._generate_slug(update_data['name'])
        
        for field, value in update_data.items():
            setattr(venue, field, value)
        
        self.db.commit()
        self.db.refresh(venue)
        
        logger.info(f"Updated venue: {venue.name} (ID: {venue.id})")
        return venue
    
    def delete_venue(self, venue_id: int) -> bool:
        """Soft delete venue by setting status to inactive"""
        venue = self.get_venue(venue_id)
        if not venue:
            return False
        
        venue.venue_status = VenueStatus.PERMANENTLY_CLOSED
        self.db.commit()
        
        logger.info(f"Deleted venue: {venue.name} (ID: {venue.id})")
        return True
    
    def search_venues(self, search_params: VenueSearchParams) -> Tuple[List[EnhancedVenue], int]:
        """Advanced venue search with filtering"""
        query = self.db.query(EnhancedVenue)
        
        # Base filters
        if search_params.venue_status:
            query = query.filter(EnhancedVenue.venue_status == search_params.venue_status)
        
        # Text search
        if search_params.q:
            search_term = f"%{search_params.q}%"
            query = query.filter(
                or_(
                    EnhancedVenue.name.ilike(search_term),
                    EnhancedVenue.description.ilike(search_term),
                    EnhancedVenue.city.ilike(search_term),
                    EnhancedVenue.address.ilike(search_term)
                )
            )
        
        # Location filters
        if search_params.city:
            query = query.filter(EnhancedVenue.city.ilike(f"%{search_params.city}%"))
        
        if search_params.region:
            query = query.filter(EnhancedVenue.region.ilike(f"%{search_params.region}%"))
        
        if search_params.venue_type:
            query = query.filter(EnhancedVenue.venue_type == search_params.venue_type)
        
        # Capacity filters
        if search_params.min_capacity:
            query = query.filter(EnhancedVenue.capacity >= search_params.min_capacity)
        
        if search_params.max_capacity:
            query = query.filter(EnhancedVenue.capacity <= search_params.max_capacity)
        
        # Geographic proximity search
        if all([search_params.latitude, search_params.longitude, search_params.radius_km]):
            distance_query = self._build_distance_query(
                search_params.latitude, 
                search_params.longitude, 
                search_params.radius_km
            )
            query = query.filter(distance_query)
        
        # Pricing filters
        if search_params.max_price_per_hour:
            query = query.filter(
                or_(
                    EnhancedVenue.base_price_per_hour == None,
                    EnhancedVenue.base_price_per_hour <= search_params.max_price_per_hour
                )
            )
        
        if search_params.max_price_per_day:
            query = query.filter(
                or_(
                    EnhancedVenue.base_price_per_day == None,
                    EnhancedVenue.base_price_per_day <= search_params.max_price_per_day
                )
            )
        
        # Rating filter
        if search_params.min_rating:
            query = query.filter(
                or_(
                    EnhancedVenue.average_rating == None,
                    EnhancedVenue.average_rating >= search_params.min_rating
                )
            )
        
        # Facility filters
        if search_params.has_parking:
            query = self._filter_by_facility(query, "parking", search_params.has_parking)
        
        if search_params.has_catering:
            query = self._filter_by_facility(query, "catering", search_params.has_catering)
        
        if search_params.has_av_equipment:
            query = self._filter_by_facility(query, "audio_visual", search_params.has_av_equipment)
        
        if search_params.is_accessible:
            query = self._filter_by_facility(query, "accessibility", search_params.is_accessible)
        
        # Availability filter
        if search_params.available_from and search_params.available_to:
            available_venues = self._get_available_venues(
                search_params.available_from, 
                search_params.available_to
            )
            if available_venues:
                query = query.filter(EnhancedVenue.id.in_(available_venues))
            else:
                # No venues available in the time range
                return [], 0
        
        # Get total count before pagination
        total = query.count()
        
        # Sorting
        if search_params.sort_by == "name":
            order_col = EnhancedVenue.name
        elif search_params.sort_by == "rating":
            order_col = EnhancedVenue.average_rating
        elif search_params.sort_by == "price":
            order_col = EnhancedVenue.base_price_per_hour
        elif search_params.sort_by == "created_at":
            order_col = EnhancedVenue.created_at
        elif search_params.sort_by == "distance" and all([search_params.latitude, search_params.longitude]):
            # Calculate distance for sorting
            query = query.add_columns(
                self._distance_formula(search_params.latitude, search_params.longitude).label('distance')
            )
            order_col = text('distance')
        else:
            order_col = EnhancedVenue.name
        
        if search_params.sort_order == "desc":
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())
        
        # Pagination
        offset = (search_params.page - 1) * search_params.size
        venues = query.offset(offset).limit(search_params.size).all()
        
        # Extract venue objects if distance was calculated
        if hasattr(venues[0] if venues else None, 'EnhancedVenue'):
            venues = [result.EnhancedVenue for result in venues]
        
        return venues, total
    
    # Facility Management
    def create_facility(self, facility_data: dict) -> Facility:
        """Create a new facility type"""
        facility = Facility(**facility_data)
        self.db.add(facility)
        self.db.commit()
        self.db.refresh(facility)
        return facility
    
    def get_facilities(self) -> List[Facility]:
        """Get all available facilities"""
        return self.db.query(Facility).order_by(Facility.facility_type, Facility.name).all()
    
    def add_venue_facility(self, venue_id: int, facility_id: int, **kwargs) -> bool:
        """Add facility to venue"""
        # Check if association already exists
        existing = self.db.query(venue_facilities).filter(
            and_(
                venue_facilities.c.venue_id == venue_id,
                venue_facilities.c.facility_id == facility_id
            )
        ).first()
        
        if existing:
            return False
        
        # Insert new association
        insert_stmt = venue_facilities.insert().values(
            venue_id=venue_id,
            facility_id=facility_id,
            **kwargs
        )
        self.db.execute(insert_stmt)
        self.db.commit()
        return True
    
    def remove_venue_facility(self, venue_id: int, facility_id: int) -> bool:
        """Remove facility from venue"""
        delete_stmt = venue_facilities.delete().where(
            and_(
                venue_facilities.c.venue_id == venue_id,
                venue_facilities.c.facility_id == facility_id
            )
        )
        result = self.db.execute(delete_stmt)
        self.db.commit()
        return result.rowcount > 0
    
    def get_venue_facilities(self, venue_id: int) -> List[Dict[str, Any]]:
        """Get all facilities for a venue"""
        query = self.db.query(
            Facility,
            venue_facilities.c.notes,
            venue_facilities.c.is_included,
            venue_facilities.c.additional_cost
        ).join(
            venue_facilities, Facility.id == venue_facilities.c.facility_id
        ).filter(venue_facilities.c.venue_id == venue_id)
        
        return [
            {
                "facility": facility,
                "notes": notes,
                "is_included": is_included,
                "additional_cost": additional_cost
            }
            for facility, notes, is_included, additional_cost in query.all()
        ]
    
    # Availability Management
    def create_availability_slot(self, availability_data: VenueAvailabilityCreate) -> VenueAvailability:
        """Create availability slot"""
        availability = VenueAvailability(**availability_data.dict())
        self.db.add(availability)
        self.db.commit()
        self.db.refresh(availability)
        return availability
    
    def get_venue_availability(self, venue_id: int, start_date: date, end_date: date) -> List[VenueAvailability]:
        """Get venue availability for date range"""
        return self.db.query(VenueAvailability).filter(
            and_(
                VenueAvailability.venue_id == venue_id,
                VenueAvailability.date >= start_date,
                VenueAvailability.date <= end_date
            )
        ).order_by(VenueAvailability.start_time).all()
    
    def update_availability_slot(self, availability_id: int, availability_data: VenueAvailabilityUpdate) -> Optional[VenueAvailability]:
        """Update availability slot"""
        availability = self.db.query(VenueAvailability).filter(VenueAvailability.id == availability_id).first()
        if not availability:
            return None
        
        update_data = availability_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(availability, field, value)
        
        self.db.commit()
        self.db.refresh(availability)
        return availability
    
    def check_availability(self, venue_id: int, start_time: datetime, end_time: datetime) -> bool:
        """Check if venue is available for the specified time"""
        conflicts = self.db.query(VenueAvailability).filter(
            and_(
                VenueAvailability.venue_id == venue_id,
                VenueAvailability.status.in_([AvailabilityStatus.BOOKED, AvailabilityStatus.BLOCKED]),
                or_(
                    and_(VenueAvailability.start_time <= start_time, VenueAvailability.end_time > start_time),
                    and_(VenueAvailability.start_time < end_time, VenueAvailability.end_time >= end_time),
                    and_(VenueAvailability.start_time >= start_time, VenueAvailability.end_time <= end_time)
                )
            )
        ).first()
        
        return conflicts is None
    
    # Booking Management
    def create_booking(self, booking_data: VenueBookingCreate, customer_id: Optional[int] = None) -> VenueBooking:
        """Create venue booking"""
        # Generate unique booking reference
        booking_reference = self._generate_booking_reference()
        
        # Calculate pricing
        pricing = self._calculate_booking_pricing(
            booking_data.venue_id,
            booking_data.start_datetime,
            booking_data.end_datetime
        )
        
        booking = VenueBooking(
            **booking_data.dict(),
            customer_id=customer_id,
            booking_reference=booking_reference,
            **pricing
        )
        
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        
        # Create corresponding availability slots
        self._create_booking_availability_slots(booking)
        
        logger.info(f"Created booking: {booking.booking_reference} for venue {booking.venue_id}")
        return booking
    
    def get_booking(self, booking_id: int) -> Optional[VenueBooking]:
        """Get booking by ID"""
        return self.db.query(VenueBooking).filter(VenueBooking.id == booking_id).first()
    
    def get_booking_by_reference(self, booking_reference: str) -> Optional[VenueBooking]:
        """Get booking by reference"""
        return self.db.query(VenueBooking).filter(VenueBooking.booking_reference == booking_reference).first()
    
    def update_booking(self, booking_id: int, booking_data: VenueBookingUpdate) -> Optional[VenueBooking]:
        """Update booking"""
        booking = self.get_booking(booking_id)
        if not booking:
            return None
        
        update_data = booking_data.dict(exclude_unset=True)
        
        # Handle status changes
        if 'booking_status' in update_data:
            self._handle_booking_status_change(booking, update_data['booking_status'])
        
        for field, value in update_data.items():
            setattr(booking, field, value)
        
        self.db.commit()
        self.db.refresh(booking)
        
        logger.info(f"Updated booking: {booking.booking_reference}")
        return booking
    
    def cancel_booking(self, booking_id: int, reason: str) -> bool:
        """Cancel booking"""
        booking = self.get_booking(booking_id)
        if not booking:
            return False
        
        booking.booking_status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason
        
        # Free up availability slots
        self._free_booking_availability_slots(booking)
        
        self.db.commit()
        
        logger.info(f"Cancelled booking: {booking.booking_reference}")
        return True
    
    def search_bookings(self, search_params: BookingSearchParams) -> Tuple[List[VenueBooking], int]:
        """Search bookings with filters"""
        query = self.db.query(VenueBooking)
        
        if search_params.venue_id:
            query = query.filter(VenueBooking.venue_id == search_params.venue_id)
        
        if search_params.customer_id:
            query = query.filter(VenueBooking.customer_id == search_params.customer_id)
        
        if search_params.booking_status:
            query = query.filter(VenueBooking.booking_status == search_params.booking_status)
        
        if search_params.start_date:
            query = query.filter(VenueBooking.start_datetime >= search_params.start_date)
        
        if search_params.end_date:
            query = query.filter(VenueBooking.end_datetime <= search_params.end_date)
        
        total = query.count()
        
        # Pagination
        offset = (search_params.page - 1) * search_params.size
        bookings = query.order_by(VenueBooking.created_at.desc()).offset(offset).limit(search_params.size).all()
        
        return bookings, total
    
    # Review Management
    def create_review(self, review_data: VenueReviewCreate, user_id: int) -> VenueReview:
        """Create venue review"""
        review = VenueReview(**review_data.dict(), user_id=user_id)
        self.db.add(review)
        
        # Update venue rating statistics
        self._update_venue_rating(review_data.venue_id)
        
        self.db.commit()
        self.db.refresh(review)
        
        logger.info(f"Created review for venue {review_data.venue_id} by user {user_id}")
        return review
    
    def get_venue_reviews(self, venue_id: int, limit: int = 20, offset: int = 0) -> Tuple[List[VenueReview], int]:
        """Get reviews for venue"""
        query = self.db.query(VenueReview).filter(
            and_(
                VenueReview.venue_id == venue_id,
                VenueReview.is_public == True
            )
        )
        
        total = query.count()
        reviews = query.order_by(VenueReview.created_at.desc()).offset(offset).limit(limit).all()
        
        return reviews, total
    
    def update_review(self, review_id: int, review_data: VenueReviewUpdate) -> Optional[VenueReview]:
        """Update review"""
        review = self.db.query(VenueReview).filter(VenueReview.id == review_id).first()
        if not review:
            return None
        
        update_data = review_data.dict(exclude_unset=True)
        
        # Handle venue response
        if 'venue_response' in update_data:
            update_data['venue_responded_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(review, field, value)
        
        # Update venue rating if rating changed
        if 'rating' in update_data:
            self._update_venue_rating(review.venue_id)
        
        self.db.commit()
        self.db.refresh(review)
        
        return review
    
    # Statistics and Analytics
    def get_venue_statistics(self, venue_id: int) -> Dict[str, Any]:
        """Get comprehensive venue statistics"""
        venue = self.get_venue(venue_id)
        if not venue:
            return {}
        
        # Booking statistics
        total_bookings = self.db.query(func.count(VenueBooking.id)).filter(VenueBooking.venue_id == venue_id).scalar()
        
        completed_bookings = self.db.query(func.count(VenueBooking.id)).filter(
            and_(
                VenueBooking.venue_id == venue_id,
                VenueBooking.booking_status == BookingStatus.COMPLETED
            )
        ).scalar()
        
        total_revenue = self.db.query(func.sum(VenueBooking.total_cost)).filter(
            and_(
                VenueBooking.venue_id == venue_id,
                VenueBooking.booking_status.in_([BookingStatus.COMPLETED, BookingStatus.CONFIRMED])
            )
        ).scalar() or Decimal('0')
        
        average_booking_value = self.db.query(func.avg(VenueBooking.total_cost)).filter(
            and_(
                VenueBooking.venue_id == venue_id,
                VenueBooking.booking_status.in_([BookingStatus.COMPLETED, BookingStatus.CONFIRMED])
            )
        ).scalar() or Decimal('0')
        
        # Calculate occupancy rate (last 12 months)
        year_ago = datetime.utcnow() - timedelta(days=365)
        occupancy_rate = self._calculate_occupancy_rate(venue_id, year_ago, datetime.utcnow())
        
        # Most popular months
        popular_months = self._get_popular_months(venue_id)
        
        return {
            "venue_id": venue_id,
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "total_revenue": total_revenue,
            "average_booking_value": average_booking_value,
            "occupancy_rate": occupancy_rate,
            "most_popular_months": popular_months,
            "average_rating": venue.average_rating,
            "total_reviews": venue.total_reviews
        }
    
    # Helper Methods
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from venue name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while self.db.query(EnhancedVenue).filter(EnhancedVenue.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference"""
        while True:
            ref = f"BK{uuid.uuid4().hex[:8].upper()}"
            if not self.db.query(VenueBooking).filter(VenueBooking.booking_reference == ref).first():
                return ref
    
    def _build_distance_query(self, lat: float, lon: float, radius_km: float):
        """Build distance query for geographic search"""
        # Haversine formula for distance calculation
        return self._distance_formula(lat, lon) <= radius_km
    
    def _distance_formula(self, lat: float, lon: float):
        """SQL expression for distance calculation using Haversine formula"""
        return func.acos(
            func.cos(func.radians(lat)) *
            func.cos(func.radians(EnhancedVenue.latitude)) *
            func.cos(func.radians(EnhancedVenue.longitude) - func.radians(lon)) +
            func.sin(func.radians(lat)) *
            func.sin(func.radians(EnhancedVenue.latitude))
        ) * 6371  # Earth's radius in kilometers
    
    def _filter_by_facility(self, query, facility_type: str, has_facility: bool):
        """Filter query by facility availability"""
        if has_facility:
            return query.join(venue_facilities).join(Facility).filter(
                Facility.facility_type == facility_type
            )
        else:
            # Venues that don't have this facility
            subquery = self.db.query(venue_facilities.c.venue_id).join(Facility).filter(
                Facility.facility_type == facility_type
            ).subquery()
            return query.filter(~EnhancedVenue.id.in_(subquery))
    
    def _get_available_venues(self, start_time: datetime, end_time: datetime) -> List[int]:
        """Get venue IDs that are available in the given time range"""
        # Find venues that have conflicts
        conflicted_venues = self.db.query(VenueAvailability.venue_id).filter(
            and_(
                VenueAvailability.status.in_([AvailabilityStatus.BOOKED, AvailabilityStatus.BLOCKED]),
                or_(
                    and_(VenueAvailability.start_time <= start_time, VenueAvailability.end_time > start_time),
                    and_(VenueAvailability.start_time < end_time, VenueAvailability.end_time >= end_time),
                    and_(VenueAvailability.start_time >= start_time, VenueAvailability.end_time <= end_time)
                )
            )
        ).distinct().subquery()
        
        # Return venues that are not in the conflicted list
        available_venues = self.db.query(EnhancedVenue.id).filter(
            ~EnhancedVenue.id.in_(conflicted_venues)
        ).all()
        
        return [venue_id for venue_id, in available_venues]
    
    def _calculate_booking_pricing(self, venue_id: int, start_time: datetime, end_time: datetime) -> Dict[str, Decimal]:
        """Calculate booking pricing"""
        venue = self.get_venue(venue_id)
        if not venue:
            return {"base_cost": Decimal('0'), "total_cost": Decimal('0')}
        
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        # Base pricing
        if venue.base_price_per_hour:
            base_cost = venue.base_price_per_hour * Decimal(str(duration_hours))
        elif venue.base_price_per_day and duration_hours >= 8:
            days = max(1, int(duration_hours / 24))
            base_cost = venue.base_price_per_day * Decimal(str(days))
        else:
            base_cost = Decimal('0')
        
        # Apply pricing rules (simplified)
        # In a real implementation, you'd apply dynamic pricing rules here
        
        facility_costs = Decimal('0')  # Calculate based on selected facilities
        additional_costs = Decimal('0')
        discount_amount = Decimal('0')
        tax_amount = base_cost * Decimal('0.25')  # 25% VAT for Croatia
        
        total_cost = base_cost + facility_costs + additional_costs - discount_amount + tax_amount
        
        return {
            "base_cost": base_cost,
            "facility_costs": facility_costs,
            "additional_costs": additional_costs,
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "total_cost": total_cost
        }
    
    def _create_booking_availability_slots(self, booking: VenueBooking):
        """Create availability slots for booking"""
        # Mark the time slot as booked
        availability = VenueAvailability(
            venue_id=booking.venue_id,
            date=booking.start_datetime.date(),
            start_time=booking.start_datetime,
            end_time=booking.end_datetime,
            status=AvailabilityStatus.BOOKED,
            booking_id=booking.id
        )
        
        self.db.add(availability)
    
    def _free_booking_availability_slots(self, booking: VenueBooking):
        """Free up availability slots when booking is cancelled"""
        self.db.query(VenueAvailability).filter(VenueAvailability.booking_id == booking.id).update({
            "status": AvailabilityStatus.AVAILABLE,
            "booking_id": None
        })
    
    def _handle_booking_status_change(self, booking: VenueBooking, new_status: BookingStatus):
        """Handle booking status changes"""
        if new_status == BookingStatus.CONFIRMED:
            booking.confirmed_at = datetime.utcnow()
        elif new_status == BookingStatus.COMPLETED:
            booking.completed_at = datetime.utcnow()
            # Update venue statistics
            venue = booking.venue
            venue.total_bookings += 1
            venue.total_revenue = (venue.total_revenue or Decimal('0')) + booking.total_cost
            venue.last_booking_at = datetime.utcnow()
    
    def _update_venue_rating(self, venue_id: int):
        """Update venue average rating and review count"""
        stats = self.db.query(
            func.avg(VenueReview.rating),
            func.count(VenueReview.id)
        ).filter(
            and_(
                VenueReview.venue_id == venue_id,
                VenueReview.is_public == True
            )
        ).first()
        
        avg_rating, review_count = stats
        
        venue = self.get_venue(venue_id)
        if venue:
            venue.average_rating = avg_rating
            venue.total_reviews = review_count or 0
    
    def _calculate_occupancy_rate(self, venue_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate venue occupancy rate for date range"""
        total_hours = (end_date - start_date).total_seconds() / 3600
        
        booked_hours = self.db.query(
            func.sum(
                func.extract('epoch', VenueAvailability.end_time - VenueAvailability.start_time) / 3600
            )
        ).filter(
            and_(
                VenueAvailability.venue_id == venue_id,
                VenueAvailability.status == AvailabilityStatus.BOOKED,
                VenueAvailability.start_time >= start_date,
                VenueAvailability.end_time <= end_date
            )
        ).scalar() or 0
        
        return (booked_hours / total_hours * 100) if total_hours > 0 else 0
    
    def _get_popular_months(self, venue_id: int) -> List[str]:
        """Get most popular booking months"""
        month_stats = self.db.query(
            extract('month', VenueBooking.start_datetime).label('month'),
            func.count(VenueBooking.id).label('booking_count')
        ).filter(
            and_(
                VenueBooking.venue_id == venue_id,
                VenueBooking.booking_status.in_([BookingStatus.COMPLETED, BookingStatus.CONFIRMED])
            )
        ).group_by('month').order_by(text('booking_count DESC')).limit(3).all()
        
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        return [month_names[int(month) - 1] for month, count in month_stats]