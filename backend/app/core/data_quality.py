"""
Advanced data quality validation and duplicate detection for scraped events.
"""

import hashlib
import re
import unicodedata
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from ..models.event import Event
from ..models.schemas import EventCreate


class DataQualityValidator:
    """Comprehensive data quality validation for event data."""

    # Quality thresholds
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 500
    MIN_DESCRIPTION_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 5000
    MIN_LOCATION_LENGTH = 3
    MAX_LOCATION_LENGTH = 200

    # Croatian city names for location validation
    CROATIAN_CITIES = {
        "zagreb",
        "split",
        "rijeka",
        "osijek",
        "zadar",
        "slavonski brod",
        "pula",
        "karlovac",
        "sisak",
        "šibenik",
        "varaždin",
        "dubrovnik",
        "bjelovar",
        "vinkovci",
        "vukovar",
        "velika gorica",
        "koprivnica",
        "požega",
        "čakovec",
        "virovitica",
        "đakovo",
        "gospić",
        "imotski",
        "makarska",
        "trogir",
        "korčula",
        "hvar",
        "brač",
        "vis",
        "lastovo",
        "krk",
        "cres",
        "lošinj",
        "rab",
        "pag",
        "ugljan",
        "dugi otok",
    }

    # Common spam/low-quality indicators
    SPAM_INDICATORS = [
        "click here",
        "call now",
        "limited time",
        "act now",
        "free money",
        "guaranteed",
        "no risk",
        "special promotion",
        "urgent",
        "winner",
        "congratulations",
        "selected",
        "claim",
        "prize",
    ]

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison (remove accents, lowercase, etc.)."""
        if not text:
            return ""

        # Normalize unicode characters (remove accents)
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")

        # Convert to lowercase and remove extra whitespace
        text = " ".join(text.lower().strip().split())

        # Remove common punctuation and special characters
        text = re.sub(r"[^\w\s-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @classmethod
    def validate_name(cls, name: str) -> Tuple[bool, List[str]]:
        """Validate event name quality."""
        issues = []

        if not name or not name.strip():
            issues.append("Event name is empty or missing")
            return False, issues

        name = name.strip()

        # Length validation
        if len(name) < cls.MIN_NAME_LENGTH:
            issues.append(
                f"Event name too short (minimum {cls.MIN_NAME_LENGTH} characters)"
            )

        if len(name) > cls.MAX_NAME_LENGTH:
            issues.append(
                f"Event name too long (maximum {cls.MAX_NAME_LENGTH} characters)"
            )

        # Content validation
        if name.lower() in ["event", "untitled", "no title", "test", "sample"]:
            issues.append("Event name appears to be placeholder text")

        # Check for excessive repetition
        words = name.split()
        if len(words) > 1 and len(set(words)) == 1:
            issues.append("Event name contains only repeated words")

        # Check for spam indicators
        name_lower = name.lower()
        for indicator in cls.SPAM_INDICATORS:
            if indicator in name_lower:
                issues.append(f"Event name contains spam indicator: '{indicator}'")

        # Check for excessive uppercase
        if name.isupper() and len(name) > 10:
            issues.append("Event name is in all caps (low quality indicator)")

        # Check for excessive special characters
        special_char_ratio = len(re.findall(r"[^a-zA-Z0-9\s]", name)) / len(name)
        if special_char_ratio > 0.3:
            issues.append("Event name contains too many special characters")

        return len(issues) == 0, issues

    @classmethod
    def validate_description(cls, description: str) -> Tuple[bool, List[str]]:
        """Validate event description quality."""
        issues = []

        if not description or not description.strip():
            issues.append("Event description is empty or missing")
            return False, issues

        description = description.strip()

        # Length validation
        if len(description) < cls.MIN_DESCRIPTION_LENGTH:
            issues.append(
                f"Description too short (minimum {cls.MIN_DESCRIPTION_LENGTH} characters)"
            )

        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            issues.append(
                f"Description too long (maximum {cls.MAX_DESCRIPTION_LENGTH} characters)"
            )

        # Content validation
        placeholder_texts = [
            "lorem ipsum",
            "placeholder",
            "sample text",
            "test description",
            "description here",
            "add description",
            "no description",
        ]

        desc_lower = description.lower()
        for placeholder in placeholder_texts:
            if placeholder in desc_lower:
                issues.append(f"Description contains placeholder text: '{placeholder}'")

        # Check for spam indicators
        for indicator in cls.SPAM_INDICATORS:
            if indicator in desc_lower:
                issues.append(f"Description contains spam indicator: '{indicator}'")

        # Check sentence structure
        sentences = re.split(r"[.!?]+", description)
        if len(sentences) == 1 and len(description) > 100:
            issues.append("Description lacks proper sentence structure")

        # Check for excessive repetition
        words = description.split()
        if len(words) > 10:
            word_count = {}
            for word in words:
                if len(word) > 3:  # Only count meaningful words
                    word_count[word.lower()] = word_count.get(word.lower(), 0) + 1

            # Check for words repeated more than 20% of total words
            for word, count in word_count.items():
                if count > len(words) * 0.2:
                    issues.append(
                        f"Description has excessive repetition of word: '{word}'"
                    )

        return len(issues) == 0, issues

    @classmethod
    def validate_location(cls, location: str) -> Tuple[bool, List[str]]:
        """Validate event location quality."""
        issues = []

        if not location or not location.strip():
            issues.append("Event location is empty or missing")
            return False, issues

        location = location.strip()

        # Length validation
        if len(location) < cls.MIN_LOCATION_LENGTH:
            issues.append(
                f"Location too short (minimum {cls.MIN_LOCATION_LENGTH} characters)"
            )

        if len(location) > cls.MAX_LOCATION_LENGTH:
            issues.append(
                f"Location too long (maximum {cls.MAX_LOCATION_LENGTH} characters)"
            )

        # Content validation
        placeholder_texts = ["location", "venue", "place", "tbd", "tba", "unknown"]
        location_lower = location.lower()

        for placeholder in placeholder_texts:
            if location_lower == placeholder:
                issues.append(f"Location appears to be placeholder: '{placeholder}'")

        # Check if it contains at least one Croatian city or "croatia"
        location_normalized = cls.normalize_text(location)
        has_croatian_reference = False

        if "croatia" in location_normalized or "hrvatska" in location_normalized:
            has_croatian_reference = True

        for city in cls.CROATIAN_CITIES:
            if city in location_normalized:
                has_croatian_reference = True
                break

        if not has_croatian_reference and len(location) > 10:
            issues.append("Location does not appear to be in Croatia")

        return len(issues) == 0, issues

    @classmethod
    def validate_date(cls, event_date: date) -> Tuple[bool, List[str]]:
        """Validate event date."""
        issues = []

        if not event_date:
            issues.append("Event date is missing")
            return False, issues

        today = date.today()

        # Check if date is too far in the past
        if event_date < today - timedelta(days=1):
            issues.append("Event date is in the past")

        # Check if date is too far in the future (more than 2 years)
        if event_date > today + timedelta(days=730):
            issues.append("Event date is too far in the future (more than 2 years)")

        # Check for obviously wrong dates (year 1900, etc.)
        if event_date.year < 2020 or event_date.year > 2030:
            issues.append(f"Event date has suspicious year: {event_date.year}")

        return len(issues) == 0, issues

    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, List[str]]:
        """Validate URL quality."""
        issues = []

        if not url:
            return True, []  # URL is optional

        try:
            parsed = urlparse(url)

            if not parsed.scheme:
                issues.append("URL is missing protocol (http/https)")
            elif parsed.scheme not in ["http", "https"]:
                issues.append(f"URL has unsupported protocol: {parsed.scheme}")

            if not parsed.netloc:
                issues.append("URL is missing domain")

            # Check for suspicious domains
            suspicious_domains = ["localhost", "127.0.0.1", "example.com", "test.com"]
            if any(domain in parsed.netloc.lower() for domain in suspicious_domains):
                issues.append(f"URL contains suspicious domain: {parsed.netloc}")

        except Exception as e:
            issues.append(f"URL format is invalid: {str(e)}")

        return len(issues) == 0, issues

    @classmethod
    def calculate_quality_score(cls, event: EventCreate) -> float:
        """Calculate overall quality score (0-100)."""
        score = 100.0

        # Name validation (30% weight)
        name_valid, name_issues = cls.validate_name(event.name)
        if not name_valid:
            score -= 30 * (len(name_issues) / 5)  # Max 5 possible issues

        # Description validation (25% weight)
        desc_valid, desc_issues = cls.validate_description(event.description)
        if not desc_valid:
            score -= 25 * (len(desc_issues) / 5)

        # Location validation (20% weight)
        loc_valid, loc_issues = cls.validate_location(event.location)
        if not loc_valid:
            score -= 20 * (len(loc_issues) / 4)

        # Date validation (15% weight)
        date_valid, date_issues = cls.validate_date(event.date)
        if not date_valid:
            score -= 15 * len(date_issues)

        # URL validation (10% weight)
        if event.link:
            url_valid, url_issues = cls.validate_url(event.link)
            if not url_valid:
                score -= 10 * (len(url_issues) / 3)

        return max(0.0, score)

    @classmethod
    def validate_event(cls, event: EventCreate) -> Dict[str, Any]:
        """Comprehensive event validation."""
        validation_result = {
            "is_valid": True,
            "quality_score": 0.0,
            "issues": [],
            "warnings": [],
            "field_validation": {},
        }

        # Validate individual fields
        name_valid, name_issues = cls.validate_name(event.name)
        desc_valid, desc_issues = cls.validate_description(event.description)
        loc_valid, loc_issues = cls.validate_location(event.location)
        date_valid, date_issues = cls.validate_date(event.date)
        url_valid, url_issues = (
            cls.validate_url(event.link) if event.link else (True, [])
        )

        # Store field validation results
        validation_result["field_validation"] = {
            "name": {"valid": name_valid, "issues": name_issues},
            "description": {"valid": desc_valid, "issues": desc_issues},
            "location": {"valid": loc_valid, "issues": loc_issues},
            "date": {"valid": date_valid, "issues": date_issues},
            "url": {"valid": url_valid, "issues": url_issues},
        }

        # Collect all issues
        all_issues = name_issues + desc_issues + loc_issues + date_issues + url_issues
        validation_result["issues"] = all_issues

        # Determine if event is valid (critical issues fail validation)
        critical_issues = []
        if not name_valid:
            critical_issues.extend(
                [
                    issue
                    for issue in name_issues
                    if "empty" in issue or "missing" in issue
                ]
            )
        if not date_valid:
            critical_issues.extend(date_issues)

        validation_result["is_valid"] = len(critical_issues) == 0

        # Calculate quality score
        validation_result["quality_score"] = cls.calculate_quality_score(event)

        # Add warnings for non-critical issues
        if validation_result["quality_score"] < 70:
            validation_result["warnings"].append("Event has low quality score")

        if len(all_issues) > 0 and validation_result["is_valid"]:
            validation_result["warnings"].append(
                "Event has quality issues but passes validation"
            )

        return validation_result


class DuplicateDetector:
    """Advanced duplicate detection for events."""

    # Similarity thresholds
    NAME_SIMILARITY_THRESHOLD = 0.85
    DESCRIPTION_SIMILARITY_THRESHOLD = 0.70
    LOCATION_SIMILARITY_THRESHOLD = 0.80

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two text strings (0-1)."""
        if not text1 or not text2:
            return 0.0

        # Normalize texts
        norm1 = DataQualityValidator.normalize_text(text1)
        norm2 = DataQualityValidator.normalize_text(text2)

        if not norm1 or not norm2:
            return 0.0

        return SequenceMatcher(None, norm1, norm2).ratio()

    @staticmethod
    def calculate_date_similarity(date1: date, date2: date) -> float:
        """Calculate date similarity (1.0 for same date, decreases with distance)."""
        if not date1 or not date2:
            return 0.0

        if date1 == date2:
            return 1.0

        # Calculate days difference
        days_diff = abs((date1 - date2).days)

        # Similar dates within 1 day get high similarity
        if days_diff <= 1:
            return 0.9
        elif days_diff <= 7:
            return 0.7
        elif days_diff <= 30:
            return 0.3
        else:
            return 0.0

    @classmethod
    def calculate_event_similarity(
        cls, event1: EventCreate, event2: EventCreate
    ) -> Dict[str, float]:
        """Calculate comprehensive similarity between two events."""
        similarity = {
            "name": cls.calculate_text_similarity(event1.name, event2.name),
            "description": cls.calculate_text_similarity(
                event1.description, event2.description
            ),
            "location": cls.calculate_text_similarity(event1.location, event2.location),
            "date": cls.calculate_date_similarity(event1.date, event2.date),
            "overall": 0.0,
        }

        # Calculate weighted overall similarity
        # Name and date are most important for duplicate detection
        weights = {"name": 0.4, "location": 0.25, "date": 0.25, "description": 0.1}

        similarity["overall"] = sum(
            similarity[field] * weight for field, weight in weights.items()
        )

        return similarity

    @classmethod
    def is_duplicate(
        cls, event1: EventCreate, event2: EventCreate
    ) -> Tuple[bool, Dict[str, Any]]:
        """Determine if two events are duplicates."""
        similarity = cls.calculate_event_similarity(event1, event2)

        # Primary duplicate detection rules
        is_duplicate = False
        reason = None

        # Rule 1: High name similarity + same date
        if (
            similarity["name"] >= cls.NAME_SIMILARITY_THRESHOLD
            and similarity["date"] >= 0.9
        ):
            is_duplicate = True
            reason = "High name similarity with same date"

        # Rule 2: Exact name match + similar date
        elif similarity["name"] >= 0.95 and similarity["date"] >= 0.7:
            is_duplicate = True
            reason = "Exact name match with similar date"

        # Rule 3: High overall similarity
        elif similarity["overall"] >= 0.85:
            is_duplicate = True
            reason = "High overall similarity"

        # Rule 4: Same location + date + similar name
        elif (
            similarity["location"] >= cls.LOCATION_SIMILARITY_THRESHOLD
            and similarity["date"] >= 0.9
            and similarity["name"] >= 0.7
        ):
            is_duplicate = True
            reason = "Same location and date with similar name"

        return is_duplicate, {
            "similarity": similarity,
            "reason": reason,
            "confidence": similarity["overall"],
        }

    @classmethod
    def find_duplicates_in_batch(
        cls, events: List[EventCreate]
    ) -> List[Dict[str, Any]]:
        """Find duplicates within a batch of events."""
        duplicates = []
        processed = set()

        for i, event1 in enumerate(events):
            if i in processed:
                continue

            event_duplicates = []

            for j, event2 in enumerate(events[i + 1 :], start=i + 1):
                if j in processed:
                    continue

                is_dup, dup_info = cls.is_duplicate(event1, event2)
                if is_dup:
                    event_duplicates.append(
                        {"index": j, "event": event2, "duplicate_info": dup_info}
                    )
                    processed.add(j)

            if event_duplicates:
                duplicates.append(
                    {
                        "original_index": i,
                        "original_event": event1,
                        "duplicates": event_duplicates,
                        "total_duplicates": len(event_duplicates),
                    }
                )

        return duplicates

    @classmethod
    def find_duplicates_in_database(
        cls, new_event: EventCreate, db: Session, days_window: int = 30
    ) -> List[Tuple[Event, Dict[str, Any]]]:
        """Find potential duplicates of a new event in the database."""
        # Query events within date window for efficiency
        date_start = new_event.date - timedelta(days=days_window)
        date_end = new_event.date + timedelta(days=days_window)

        existing_events = (
            db.query(Event)
            .filter(Event.date >= date_start, Event.date <= date_end)
            .all()
        )

        duplicates = []

        for existing_event in existing_events:
            # Convert existing event to EventCreate for comparison
            existing_event_create = EventCreate(
                name=existing_event.name,
                description=existing_event.description or "",
                location=existing_event.location or "",
                date=existing_event.date,
                time=existing_event.time,
                price=existing_event.price or "",
                image=existing_event.image or "",
                link=existing_event.link or "",
            )

            is_dup, dup_info = cls.is_duplicate(new_event, existing_event_create)
            if is_dup:
                duplicates.append((existing_event, dup_info))

        return duplicates


class DataQualityService:
    """Main service for data quality management in scraping pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.validator = DataQualityValidator()
        self.duplicate_detector = DuplicateDetector()

    def process_scraped_events(
        self,
        events: List[EventCreate],
        quality_threshold: float = 60.0,
        remove_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """Process scraped events with quality validation and duplicate detection."""
        results = {
            "total_events": len(events),
            "valid_events": [],
            "invalid_events": [],
            "low_quality_events": [],
            "duplicates_found": [],
            "duplicates_in_db": [],
            "processing_summary": {},
        }

        print(f"Processing {len(events)} scraped events...")

        # Step 1: Quality validation
        for i, event in enumerate(events):
            validation = self.validator.validate_event(event)

            if validation["is_valid"]:
                if validation["quality_score"] >= quality_threshold:
                    results["valid_events"].append(
                        {"event": event, "validation": validation, "original_index": i}
                    )
                else:
                    results["low_quality_events"].append(
                        {"event": event, "validation": validation, "original_index": i}
                    )
            else:
                results["invalid_events"].append(
                    {"event": event, "validation": validation, "original_index": i}
                )

        print(
            f"Quality validation: {len(results['valid_events'])} valid, "
            f"{len(results['low_quality_events'])} low quality, "
            f"{len(results['invalid_events'])} invalid"
        )

        # Step 2: Remove duplicates within batch
        if remove_duplicates and len(results["valid_events"]) > 1:
            valid_events_only = [item["event"] for item in results["valid_events"]]
            batch_duplicates = self.duplicate_detector.find_duplicates_in_batch(
                valid_events_only
            )

            # Remove duplicates from valid events
            if batch_duplicates:
                print(f"Found {len(batch_duplicates)} duplicate groups in batch")

                # Keep track of which events to remove
                indices_to_remove = set()
                for dup_group in batch_duplicates:
                    results["duplicates_found"].append(dup_group)
                    # Remove all duplicates, keep only the original
                    for dup in dup_group["duplicates"]:
                        indices_to_remove.add(dup["index"])

                # Filter out duplicates
                results["valid_events"] = [
                    item
                    for i, item in enumerate(results["valid_events"])
                    if i not in indices_to_remove
                ]

                print(f"Removed {len(indices_to_remove)} duplicate events from batch")

        # Step 3: Check for duplicates in database
        final_valid_events = []
        for item in results["valid_events"]:
            event = item["event"]
            db_duplicates = self.duplicate_detector.find_duplicates_in_database(
                event, self.db
            )

            if db_duplicates:
                results["duplicates_in_db"].append(
                    {"new_event": event, "existing_duplicates": db_duplicates}
                )
                print(
                    f"Event '{event.name}' has {len(db_duplicates)} duplicates in database"
                )
            else:
                final_valid_events.append(item)

        results["valid_events"] = final_valid_events

        # Generate processing summary
        results["processing_summary"] = {
            "original_count": len(events),
            "valid_count": len(results["valid_events"]),
            "invalid_count": len(results["invalid_events"]),
            "low_quality_count": len(results["low_quality_events"]),
            "batch_duplicates_count": len(results["duplicates_found"]),
            "db_duplicates_count": len(results["duplicates_in_db"]),
            "final_processable_count": len(results["valid_events"]),
            "quality_threshold": quality_threshold,
            "duplicate_detection_enabled": remove_duplicates,
        }

        print(
            f"Final processing result: {len(results['valid_events'])} events ready for database"
        )

        return results

    def save_processed_events(self, processed_results: Dict[str, Any]) -> int:
        """Save processed events to database."""
        valid_events = processed_results["valid_events"]
        saved_count = 0

        try:
            for item in valid_events:
                event_data = item["event"]
                db_event = Event(**event_data.model_dump())
                self.db.add(db_event)
                saved_count += 1

            self.db.commit()
            print(f"Successfully saved {saved_count} events to database")

        except Exception as e:
            print(f"Error saving processed events: {e}")
            self.db.rollback()
            raise

        return saved_count

    def generate_quality_report(
        self, processed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        summary = processed_results["processing_summary"]

        # Calculate quality metrics
        total_events = summary["original_count"]
        success_rate = (
            (summary["final_processable_count"] / total_events * 100)
            if total_events > 0
            else 0
        )

        # Analyze common quality issues
        issue_frequency = {}
        for item in (
            processed_results["invalid_events"]
            + processed_results["low_quality_events"]
        ):
            for issue in item["validation"]["issues"]:
                issue_frequency[issue] = issue_frequency.get(issue, 0) + 1

        # Most common issues
        common_issues = sorted(
            issue_frequency.items(), key=lambda x: x[1], reverse=True
        )[:10]

        report = {
            "summary": summary,
            "success_rate": round(success_rate, 2),
            "quality_metrics": {
                "average_quality_score": 0.0,
                "quality_distribution": {"high": 0, "medium": 0, "low": 0},
                "common_issues": common_issues,
            },
            "duplicate_analysis": {
                "batch_duplicates": len(processed_results["duplicates_found"]),
                "database_duplicates": len(processed_results["duplicates_in_db"]),
                "duplicate_rate": 0.0,
            },
            "recommendations": [],
        }

        # Calculate average quality score
        all_validated = (
            processed_results["valid_events"]
            + processed_results["low_quality_events"]
            + processed_results["invalid_events"]
        )

        if all_validated:
            total_score = sum(
                item["validation"]["quality_score"] for item in all_validated
            )
            report["quality_metrics"]["average_quality_score"] = round(
                total_score / len(all_validated), 2
            )

        # Quality distribution
        for item in all_validated:
            score = item["validation"]["quality_score"]
            if score >= 80:
                report["quality_metrics"]["quality_distribution"]["high"] += 1
            elif score >= 60:
                report["quality_metrics"]["quality_distribution"]["medium"] += 1
            else:
                report["quality_metrics"]["quality_distribution"]["low"] += 1

        # Duplicate rate
        total_duplicates = (
            summary["batch_duplicates_count"] + summary["db_duplicates_count"]
        )
        duplicate_rate = (
            (total_duplicates / total_events * 100) if total_events > 0 else 0
        )
        report["duplicate_analysis"]["duplicate_rate"] = round(duplicate_rate, 2)

        # Generate recommendations
        if success_rate < 50:
            report["recommendations"].append(
                "Success rate is very low. Review scraping selectors and data extraction logic."
            )

        if report["quality_metrics"]["average_quality_score"] < 70:
            report["recommendations"].append(
                "Average quality score is low. Improve data cleaning and validation."
            )

        if duplicate_rate > 20:
            report["recommendations"].append(
                "High duplicate rate detected. Review scraping frequency and duplicate detection logic."
            )

        if common_issues:
            report["recommendations"].append(
                f"Most common issue: '{common_issues[0][0]}'. Focus on fixing this issue first."
            )

        return report


def get_data_quality_service(db: Session) -> DataQualityService:
    """Dependency to get data quality service instance."""
    return DataQualityService(db)
