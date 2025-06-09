"""
Recurring events and event series management service.
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta
from dateutil.rrule import (
    DAILY,
    FR,
    MO,
    MONTHLY,
    SA,
    SU,
    TH,
    TU,
    WE,
    WEEKLY,
    YEARLY,
    rrule,
)
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.event import Event
from ..models.recurring_events import (
    EventInstance,
    EventInstanceStatus,
    EventSeries,
    InstanceModification,
    RecurrenceEndType,
    RecurrencePattern,
    RecurrenceRule,
    SeriesModification,
    SeriesStatus,
    SeriesTemplate,
)
from ..models.user import User
from .database import get_db

logger = logging.getLogger(__name__)


class RecurringEventsServiceError(Exception):
    """Base exception for recurring events service errors."""

    pass


class RecurringEventsService:
    """Service for managing recurring events and event series."""

    def __init__(self):
        self.max_instances_per_generation = 100
        self.default_advance_notice_days = 30

        # Weekday mapping for dateutil
        self.weekday_map = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU}

        logger.info("Recurring events service initialized")

    def create_event_series(
        self, db: Session, organizer_id: int, series_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new event series with recurrence pattern."""
        try:
            # Validate recurrence pattern
            self._validate_recurrence_pattern(series_data)

            # Create event series
            series = EventSeries(
                title=series_data["title"],
                description=series_data.get("description"),
                organizer_id=organizer_id,
                category_id=series_data.get("category_id"),
                venue_id=series_data.get("venue_id"),
                template_title=series_data.get("template_title"),
                template_description=series_data.get("template_description"),
                template_price=series_data.get("template_price"),
                template_image=series_data.get("template_image"),
                template_tags=series_data.get("template_tags"),
                start_date=series_data["start_date"],
                start_time=series_data.get("start_time"),
                duration_minutes=series_data.get("duration_minutes", 60),
                recurrence_pattern=RecurrencePattern(series_data["recurrence_pattern"]),
                recurrence_interval=series_data.get("recurrence_interval", 1),
                recurrence_end_type=RecurrenceEndType(
                    series_data.get("recurrence_end_type", "never")
                ),
                recurrence_end_date=series_data.get("recurrence_end_date"),
                max_occurrences=series_data.get("max_occurrences"),
                recurrence_days=series_data.get("recurrence_days"),
                custom_recurrence_rules=series_data.get("custom_recurrence_rules"),
                auto_publish=series_data.get("auto_publish", False),
                advance_notice_days=series_data.get(
                    "advance_notice_days", self.default_advance_notice_days
                ),
            )

            db.add(series)
            db.flush()  # Get series ID

            # Generate initial instances
            instances = self._generate_instances(db, series)

            # Update series statistics
            series.total_instances = len(instances)
            series.last_generated_at = datetime.now()

            db.commit()

            return {
                "status": "success",
                "series": {
                    "id": series.id,
                    "title": series.title,
                    "recurrence_pattern": series.recurrence_pattern.value,
                    "total_instances": series.total_instances,
                    "next_instance_date": (
                        instances[0].scheduled_date.isoformat() if instances else None
                    ),
                },
                "instances_generated": len(instances),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in create_event_series: {e}")
            raise RecurringEventsServiceError("Database operation failed")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in create_event_series: {e}")
            raise RecurringEventsServiceError(str(e))

    def _validate_recurrence_pattern(self, series_data: Dict[str, Any]) -> None:
        """Validate recurrence pattern configuration."""
        pattern = series_data["recurrence_pattern"]

        if pattern not in [p.value for p in RecurrencePattern]:
            raise RecurringEventsServiceError(f"Invalid recurrence pattern: {pattern}")

        if pattern == "weekly" and not series_data.get("recurrence_days"):
            raise RecurringEventsServiceError(
                "Weekly recurrence requires recurrence_days"
            )

        if series_data.get("recurrence_end_type") == "after_occurrences":
            if not series_data.get("max_occurrences"):
                raise RecurringEventsServiceError(
                    "max_occurrences required for 'after_occurrences' end type"
                )

        if series_data.get("recurrence_end_type") == "on_date":
            if not series_data.get("recurrence_end_date"):
                raise RecurringEventsServiceError(
                    "recurrence_end_date required for 'on_date' end type"
                )

    def _generate_instances(
        self, db: Session, series: EventSeries
    ) -> List[EventInstance]:
        """Generate event instances based on recurrence pattern."""
        instances = []

        # Calculate generation window
        start_date = series.start_date
        end_date = self._calculate_generation_end_date(series)

        # Generate dates based on recurrence pattern
        occurrence_dates = self._calculate_occurrence_dates(
            series, start_date, end_date
        )

        # Create instances
        for i, occurrence_date in enumerate(
            occurrence_dates[: self.max_instances_per_generation]
        ):
            instance = EventInstance(
                series_id=series.id,
                title=self._format_instance_title(series, i + 1),
                description=series.template_description,
                price=series.template_price,
                image=series.template_image,
                location=series.venue.name if series.venue else None,
                scheduled_date=occurrence_date,
                scheduled_time=series.start_time,
                duration_minutes=series.duration_minutes,
                timezone=series.timezone,
                sequence_number=i + 1,
                instance_status=(
                    EventInstanceStatus.PUBLISHED
                    if series.auto_publish
                    else EventInstanceStatus.SCHEDULED
                ),
            )

            db.add(instance)
            instances.append(instance)

            # Auto-publish if configured
            if series.auto_publish:
                self._publish_instance(db, instance)

        return instances

    def _calculate_generation_end_date(self, series: EventSeries) -> date:
        """Calculate the end date for instance generation."""
        advance_days = series.advance_notice_days or self.default_advance_notice_days
        default_end = date.today() + timedelta(days=advance_days)

        if series.recurrence_end_type == RecurrenceEndType.ON_DATE:
            return min(default_end, series.recurrence_end_date)
        elif series.recurrence_end_type == RecurrenceEndType.AFTER_OCCURRENCES:
            # For limited occurrences, generate all
            return default_end
        else:
            # Never-ending series
            return default_end

    def _calculate_occurrence_dates(
        self, series: EventSeries, start_date: date, end_date: date
    ) -> List[date]:
        """Calculate occurrence dates based on recurrence pattern."""
        if series.recurrence_pattern == RecurrencePattern.CUSTOM:
            return self._calculate_custom_occurrences(series, start_date, end_date)

        # Use dateutil.rrule for standard patterns
        freq_map = {
            RecurrencePattern.DAILY: DAILY,
            RecurrencePattern.WEEKLY: WEEKLY,
            RecurrencePattern.BIWEEKLY: WEEKLY,
            RecurrencePattern.MONTHLY: MONTHLY,
            RecurrencePattern.YEARLY: YEARLY,
        }

        freq = freq_map[series.recurrence_pattern]
        interval = series.recurrence_interval

        # Adjust for biweekly
        if series.recurrence_pattern == RecurrencePattern.BIWEEKLY:
            interval = 2

        # Set up rrule parameters
        rrule_kwargs = {
            "freq": freq,
            "interval": interval,
            "dtstart": datetime.combine(start_date, datetime.min.time()),
        }

        # Add end condition
        if series.recurrence_end_type == RecurrenceEndType.ON_DATE:
            rrule_kwargs["until"] = datetime.combine(
                series.recurrence_end_date, datetime.max.time()
            )
        elif series.recurrence_end_type == RecurrenceEndType.AFTER_OCCURRENCES:
            rrule_kwargs["count"] = series.max_occurrences

        # Add weekday restrictions for weekly/biweekly
        if series.recurrence_pattern in [
            RecurrencePattern.WEEKLY,
            RecurrencePattern.BIWEEKLY,
        ]:
            if series.recurrence_days:
                weekdays = [self.weekday_map[day] for day in series.recurrence_days]
                rrule_kwargs["byweekday"] = weekdays

        # Generate dates
        try:
            rule = rrule(**rrule_kwargs)
            occurrence_dates = [dt.date() for dt in rule if dt.date() <= end_date]

            # Apply exclusions
            if series.excluded_dates:
                excluded = {
                    datetime.fromisoformat(d).date() for d in series.excluded_dates
                }
                occurrence_dates = [d for d in occurrence_dates if d not in excluded]

            # Add inclusions
            if series.included_dates:
                included = {
                    datetime.fromisoformat(d).date() for d in series.included_dates
                }
                occurrence_dates.extend(included)
                occurrence_dates = sorted(set(occurrence_dates))

            return occurrence_dates

        except Exception as e:
            logger.error(f"Error calculating occurrence dates: {e}")
            return []

    def _calculate_custom_occurrences(
        self, series: EventSeries, start_date: date, end_date: date
    ) -> List[date]:
        """Calculate occurrences for custom recurrence patterns."""
        if not series.custom_recurrence_rules:
            return []

        # Implement custom logic based on rules
        # This is a simplified version - can be extended for complex patterns
        rules = series.custom_recurrence_rules
        occurrences = []

        current_date = start_date
        while current_date <= end_date:
            if self._matches_custom_rule(current_date, rules):
                occurrences.append(current_date)

            current_date += timedelta(days=1)

            # Safety limit
            if len(occurrences) >= self.max_instances_per_generation:
                break

        return occurrences

    def _matches_custom_rule(self, check_date: date, rules: Dict[str, Any]) -> bool:
        """Check if a date matches custom recurrence rules."""
        # Implement custom matching logic
        # This is a placeholder for complex custom patterns
        return False

    def _format_instance_title(self, series: EventSeries, sequence: int) -> str:
        """Format the title for an event instance."""
        if series.template_title:
            # Replace placeholders
            title = series.template_title
            title = title.replace("{sequence}", str(sequence))
            title = title.replace("{series_title}", series.title)
            return title

        return f"{series.title} #{sequence}"

    def _publish_instance(self, db: Session, instance: EventInstance) -> None:
        """Publish an event instance by creating an actual Event."""
        try:
            # Create actual event from instance
            event = Event(
                title=instance.title,
                description=instance.description,
                date=instance.scheduled_date,
                time=instance.scheduled_time,
                price=instance.price,
                image=instance.image,
                location=instance.location,
                category_id=instance.series.category_id,
                venue_id=instance.series.venue_id,
                organizer=(
                    instance.series.organizer.username
                    if instance.series.organizer
                    else None
                ),
                source="recurring_series",
                is_recurring=True,
                external_id=f"series_{instance.series_id}_instance_{instance.id}",
            )

            db.add(event)
            db.flush()

            # Link instance to event
            instance.event_id = event.id
            instance.instance_status = EventInstanceStatus.PUBLISHED
            instance.published_at = datetime.now()

        except Exception as e:
            logger.error(f"Error publishing instance {instance.id}: {e}")
            raise

    def update_series(
        self,
        db: Session,
        series_id: int,
        update_data: Dict[str, Any],
        user_id: int,
        apply_to_future: bool = True,
        apply_to_existing: bool = False,
    ) -> Dict[str, Any]:
        """Update an event series and optionally apply changes to instances."""
        try:
            series = db.query(EventSeries).filter(EventSeries.id == series_id).first()
            if not series:
                raise RecurringEventsServiceError("Series not found")

            # Track modifications
            modifications = []

            # Update series fields
            for field, new_value in update_data.items():
                if hasattr(series, field):
                    old_value = getattr(series, field)
                    if old_value != new_value:
                        setattr(series, field, new_value)

                        # Record modification
                        modification = SeriesModification(
                            series_id=series_id,
                            modification_type="field_update",
                            field_changed=field,
                            old_value=str(old_value),
                            new_value=str(new_value),
                            applies_to_future=apply_to_future,
                            applies_to_existing=apply_to_existing,
                            modified_by=user_id,
                        )
                        db.add(modification)
                        modifications.append(modification)

            # Apply changes to instances if requested
            affected_instances = 0
            if apply_to_future or apply_to_existing:
                affected_instances = self._apply_series_changes_to_instances(
                    db, series, update_data, apply_to_future, apply_to_existing
                )

            # Regenerate instances if recurrence changed
            if any(field.startswith("recurrence_") for field in update_data.keys()):
                self._regenerate_future_instances(db, series)

            db.commit()

            return {
                "status": "success",
                "series_id": series_id,
                "modifications": len(modifications),
                "affected_instances": affected_instances,
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in update_series: {e}")
            raise RecurringEventsServiceError("Database operation failed")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in update_series: {e}")
            raise RecurringEventsServiceError(str(e))

    def _apply_series_changes_to_instances(
        self,
        db: Session,
        series: EventSeries,
        update_data: Dict[str, Any],
        apply_to_future: bool,
        apply_to_existing: bool,
    ) -> int:
        """Apply series changes to appropriate instances."""
        query = db.query(EventInstance).filter(EventInstance.series_id == series.id)

        if apply_to_future and not apply_to_existing:
            # Only future instances
            query = query.filter(EventInstance.scheduled_date >= date.today())
        elif apply_to_existing and not apply_to_future:
            # Only existing instances
            query = query.filter(EventInstance.scheduled_date < date.today())
        # If both are True, apply to all instances

        instances = query.all()

        for instance in instances:
            # Only apply template fields that aren't overridden
            for field, new_value in update_data.items():
                instance_field = field.replace("template_", "")
                override_field = f"{instance_field}_overridden"

                if (
                    hasattr(instance, instance_field)
                    and hasattr(instance, override_field)
                    and not getattr(instance, override_field, False)
                ):
                    setattr(instance, instance_field, new_value)

        return len(instances)

    def _regenerate_future_instances(self, db: Session, series: EventSeries) -> None:
        """Regenerate future instances after recurrence changes."""
        # Delete non-published future instances
        future_instances = (
            db.query(EventInstance)
            .filter(
                EventInstance.series_id == series.id,
                EventInstance.scheduled_date >= date.today(),
                EventInstance.instance_status == EventInstanceStatus.SCHEDULED,
            )
            .all()
        )

        for instance in future_instances:
            db.delete(instance)

        # Generate new instances
        new_instances = self._generate_instances(db, series)

        # Update series statistics
        series.total_instances = (
            db.query(EventInstance).filter(EventInstance.series_id == series.id).count()
        )
        series.last_generated_at = datetime.now()

    def modify_instance(
        self,
        db: Session,
        instance_id: int,
        modification_data: Dict[str, Any],
        user_id: int,
    ) -> Dict[str, Any]:
        """Modify a specific event instance."""
        try:
            instance = (
                db.query(EventInstance).filter(EventInstance.id == instance_id).first()
            )
            if not instance:
                raise RecurringEventsServiceError("Instance not found")

            # Track modifications
            modifications = []

            for field, new_value in modification_data.items():
                if hasattr(instance, field):
                    old_value = getattr(instance, field)
                    if old_value != new_value:
                        setattr(instance, field, new_value)

                        # Mark field as overridden
                        override_field = f"{field}_overridden"
                        if hasattr(instance, override_field):
                            setattr(instance, override_field, True)

                        # Record modification
                        modification = InstanceModification(
                            instance_id=instance_id,
                            modification_type="field_update",
                            field_changed=field,
                            old_value=str(old_value),
                            new_value=str(new_value),
                            modified_by=user_id,
                        )
                        db.add(modification)
                        modifications.append(modification)

            # Mark instance as modified
            if modifications:
                instance.instance_status = EventInstanceStatus.MODIFIED

            # Update linked event if published
            if instance.event_id:
                self._update_published_event(db, instance)

            db.commit()

            return {
                "status": "success",
                "instance_id": instance_id,
                "modifications": len(modifications),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in modify_instance: {e}")
            raise RecurringEventsServiceError("Database operation failed")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in modify_instance: {e}")
            raise RecurringEventsServiceError(str(e))

    def _update_published_event(self, db: Session, instance: EventInstance) -> None:
        """Update the published event when instance is modified."""
        if not instance.event:
            return

        event = instance.event
        event.title = instance.title
        event.description = instance.description
        event.date = instance.scheduled_date
        event.time = instance.scheduled_time
        event.price = instance.price
        event.image = instance.image
        event.location = instance.location

    def cancel_instance(
        self, db: Session, instance_id: int, user_id: int, reason: str = None
    ) -> Dict[str, Any]:
        """Cancel a specific event instance."""
        try:
            instance = (
                db.query(EventInstance).filter(EventInstance.id == instance_id).first()
            )
            if not instance:
                raise RecurringEventsServiceError("Instance not found")

            # Update instance status
            old_status = instance.instance_status
            instance.instance_status = EventInstanceStatus.CANCELLED

            # Record modification
            modification = InstanceModification(
                instance_id=instance_id,
                modification_type="cancellation",
                field_changed="instance_status",
                old_value=old_status.value,
                new_value=EventInstanceStatus.CANCELLED.value,
                reason=reason,
                modified_by=user_id,
            )
            db.add(modification)

            # Cancel linked event if published
            if instance.event:
                instance.event.event_status = "cancelled"

            db.commit()

            return {
                "status": "success",
                "instance_id": instance_id,
                "cancellation_reason": reason,
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in cancel_instance: {e}")
            raise RecurringEventsServiceError("Database operation failed")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in cancel_instance: {e}")
            raise RecurringEventsServiceError(str(e))

    def get_series_instances(
        self,
        db: Session,
        series_id: int,
        status_filter: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ) -> Dict[str, Any]:
        """Get instances for a specific series."""
        query = db.query(EventInstance).filter(EventInstance.series_id == series_id)

        # Apply filters
        if status_filter:
            try:
                status_enum = EventInstanceStatus(status_filter)
                query = query.filter(EventInstance.instance_status == status_enum)
            except ValueError:
                raise RecurringEventsServiceError(
                    f"Invalid status filter: {status_filter}"
                )

        if date_from:
            query = query.filter(EventInstance.scheduled_date >= date_from)

        if date_to:
            query = query.filter(EventInstance.scheduled_date <= date_to)

        # Get total count and apply pagination
        total = query.count()
        skip = (page - 1) * size
        pages = (total + size - 1) // size if total > 0 else 0

        instances = (
            query.order_by(EventInstance.scheduled_date.asc())
            .offset(skip)
            .limit(size)
            .all()
        )

        # Format response
        instance_list = []
        for instance in instances:
            instance_list.append(
                {
                    "id": instance.id,
                    "title": instance.title,
                    "scheduled_date": instance.scheduled_date.isoformat(),
                    "scheduled_time": instance.scheduled_time,
                    "status": instance.instance_status.value,
                    "sequence_number": instance.sequence_number,
                    "is_published": instance.event_id is not None,
                    "event_id": instance.event_id,
                    "published_at": (
                        instance.published_at.isoformat()
                        if instance.published_at
                        else None
                    ),
                }
            )

        return {
            "instances": instance_list,
            "total": total,
            "page": page,
            "size": len(instance_list),
            "pages": pages,
        }

    def get_upcoming_instances(
        self,
        db: Session,
        user_id: Optional[int] = None,
        days_ahead: int = 30,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get upcoming event instances."""
        end_date = date.today() + timedelta(days=days_ahead)

        query = db.query(EventInstance).filter(
            EventInstance.scheduled_date >= date.today(),
            EventInstance.scheduled_date <= end_date,
            EventInstance.instance_status.in_(
                [EventInstanceStatus.SCHEDULED, EventInstanceStatus.PUBLISHED]
            ),
        )

        if user_id:
            query = query.join(EventSeries).filter(EventSeries.organizer_id == user_id)

        instances = (
            query.order_by(EventInstance.scheduled_date.asc()).limit(limit).all()
        )

        return [
            {
                "id": instance.id,
                "title": instance.title,
                "series_title": instance.series.title,
                "scheduled_date": instance.scheduled_date.isoformat(),
                "scheduled_time": instance.scheduled_time,
                "status": instance.instance_status.value,
                "is_published": instance.event_id is not None,
            }
            for instance in instances
        ]

    def generate_series_statistics(self, db: Session, series_id: int) -> Dict[str, Any]:
        """Generate comprehensive statistics for a series."""
        series = db.query(EventSeries).filter(EventSeries.id == series_id).first()
        if not series:
            raise RecurringEventsServiceError("Series not found")

        # Instance statistics
        total_instances = (
            db.query(EventInstance).filter(EventInstance.series_id == series_id).count()
        )

        published_instances = (
            db.query(EventInstance)
            .filter(
                EventInstance.series_id == series_id,
                EventInstance.instance_status == EventInstanceStatus.PUBLISHED,
            )
            .count()
        )

        cancelled_instances = (
            db.query(EventInstance)
            .filter(
                EventInstance.series_id == series_id,
                EventInstance.instance_status == EventInstanceStatus.CANCELLED,
            )
            .count()
        )

        completed_instances = (
            db.query(EventInstance)
            .filter(
                EventInstance.series_id == series_id,
                EventInstance.instance_status == EventInstanceStatus.COMPLETED,
            )
            .count()
        )

        # Next instance
        next_instance = (
            db.query(EventInstance)
            .filter(
                EventInstance.series_id == series_id,
                EventInstance.scheduled_date >= date.today(),
                EventInstance.instance_status.in_(
                    [EventInstanceStatus.SCHEDULED, EventInstanceStatus.PUBLISHED]
                ),
            )
            .order_by(EventInstance.scheduled_date.asc())
            .first()
        )

        return {
            "series_id": series_id,
            "series_title": series.title,
            "series_status": series.series_status.value,
            "recurrence_pattern": series.recurrence_pattern.value,
            "created_at": series.created_at.isoformat(),
            "statistics": {
                "total_instances": total_instances,
                "published_instances": published_instances,
                "cancelled_instances": cancelled_instances,
                "completed_instances": completed_instances,
                "cancellation_rate": (
                    (cancelled_instances / total_instances * 100)
                    if total_instances > 0
                    else 0
                ),
            },
            "next_instance": (
                {
                    "date": next_instance.scheduled_date.isoformat(),
                    "title": next_instance.title,
                    "status": next_instance.instance_status.value,
                }
                if next_instance
                else None
            ),
        }


# Global service instance
recurring_events_service = RecurringEventsService()


def get_recurring_events_service() -> RecurringEventsService:
    """Get recurring events service instance."""
    return recurring_events_service
