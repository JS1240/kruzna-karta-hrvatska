from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # hr, en, de, it
    name = Column(String(100), nullable=False)  # Croatian, English, German, Italian
    native_name = Column(
        String(100), nullable=False
    )  # Hrvatski, English, Deutsch, Italiano
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Display settings
    flag_emoji = Column(String(10), nullable=True)  # 🇭🇷, 🇬🇧, 🇩🇪, 🇮🇹
    rtl = Column(Boolean, default=False)  # Right-to-left languages like Arabic

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EventTranslation(Base):
    __tablename__ = "event_translations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    language_code = Column(String(10), ForeignKey("languages.code"), nullable=False)

    # Translated fields
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)  # For translated location names
    organizer = Column(String(255), nullable=True)  # Translated organizer name

    # SEO fields
    slug = Column(String(600), nullable=True)
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(300), nullable=True)

    # Quality indicators
    is_machine_translated = Column(Boolean, default=False)
    translation_quality = Column(
        String(20), default="pending"
    )  # pending, reviewed, approved
    translated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    event = relationship("Event")
    language = relationship("Language")
    translator = relationship("User", foreign_keys=[translated_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("event_id", "language_code", name="_event_language_uc"),
    )


class CategoryTranslation(Base):
    __tablename__ = "category_translations"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("event_categories.id"), nullable=False)
    language_code = Column(String(10), ForeignKey("languages.code"), nullable=False)

    # Translated fields
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(100), nullable=True)

    # Quality indicators
    is_machine_translated = Column(Boolean, default=False)
    translation_quality = Column(String(20), default="pending")
    translated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    category = relationship("EventCategory")
    language = relationship("Language")
    translator = relationship("User", foreign_keys=[translated_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("category_id", "language_code", name="_category_language_uc"),
    )


class VenueTranslation(Base):
    __tablename__ = "venue_translations"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    language_code = Column(String(10), ForeignKey("languages.code"), nullable=False)

    # Translated fields
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    description = Column(Text, nullable=True)  # Venue description

    # Quality indicators
    is_machine_translated = Column(Boolean, default=False)
    translation_quality = Column(String(20), default="pending")
    translated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    venue = relationship("Venue")
    language = relationship("Language")
    translator = relationship("User", foreign_keys=[translated_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("venue_id", "language_code", name="_venue_language_uc"),
    )


class StaticContentTranslation(Base):
    """For translating static content like UI labels, messages, etc."""

    __tablename__ = "static_content_translations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(
        String(200), nullable=False, index=True
    )  # 'welcome_message', 'search_placeholder', etc.
    language_code = Column(String(10), ForeignKey("languages.code"), nullable=False)

    # Content
    value = Column(Text, nullable=False)  # The translated text
    context = Column(String(100), nullable=True)  # Context for translators

    # Quality indicators
    is_machine_translated = Column(Boolean, default=False)
    translation_quality = Column(String(20), default="pending")
    translated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    language = relationship("Language")
    translator = relationship("User", foreign_keys=[translated_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("key", "language_code", name="_content_language_uc"),
    )
