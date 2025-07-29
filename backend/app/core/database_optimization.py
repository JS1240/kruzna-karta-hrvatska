"""
Database optimization module for scraping operations.
Provides efficient bulk operations, duplicate detection, and optimized queries.
"""

from __future__ import annotations

import logging
import hashlib
from typing import Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from sqlalchemy import (
    and_, or_, select, update, delete, func, text, 
    Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..core.database import get_db
from ..models.event import Event
from ..models.schemas import EventCreate

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization utilities for scraping operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_size = 1000
        self.duplicate_cache: Dict[str, Set[str]] = {}
        
    async def bulk_insert_events(
        self,
        events: List[EventCreate],
        source: str,
        update_duplicates: bool = True
    ) -> Dict[str, int]:
        """
        Efficiently insert events in bulk with duplicate handling.
        
        Args:
            events: List of events to insert
            source: Source identifier
            update_duplicates: Whether to update existing events
            
        Returns:
            Dictionary with statistics (inserted, updated, skipped)
        """
        if not events:
            return {"inserted": 0, "updated": 0, "skipped": 0}
        
        logger.info(f"Starting bulk insert of {len(events)} events from {source}")
        
        stats = {"inserted": 0, "updated": 0, "skipped": 0}
        
        # Process events in batches
        for i in range(0, len(events), self.batch_size):
            batch = events[i:i + self.batch_size]
            batch_stats = await self._process_event_batch(batch, source, update_duplicates)
            
            # Update total stats
            for key in stats:
                stats[key] += batch_stats[key]
            
            logger.debug(f"Processed batch {i//self.batch_size + 1}: {batch_stats}")
        
        # Update search vectors for new events
        await self._update_search_vectors(source)
        
        logger.info(f"Bulk insert completed for {source}: {stats}")
        return stats
    
    async def _process_event_batch(
        self,
        batch: List[EventCreate],
        source: str,
        update_duplicates: bool
    ) -> Dict[str, int]:
        """Process a batch of events."""
        stats = {"inserted": 0, "updated": 0, "skipped": 0}
        
        # Calculate hashes for all events in batch
        event_hashes = {}
        for event in batch:
            event_hash = self._calculate_event_hash(event)
            event_hashes[event_hash] = event
        
        # Check for existing events with same hashes
        existing_hashes = await self._get_existing_hashes(list(event_hashes.keys()), source)
        
        # Separate new and existing events
        new_events = []
        existing_events = []
        
        for event_hash, event in event_hashes.items():
            if event_hash in existing_hashes:
                if update_duplicates:
                    existing_events.append((event_hash, event))
                else:
                    stats["skipped"] += 1
            else:
                new_events.append((event_hash, event))
        
        # Insert new events
        if new_events:
            inserted_count = await self._bulk_insert_new_events(new_events, source)
            stats["inserted"] += inserted_count
        
        # Update existing events
        if existing_events:
            updated_count = await self._bulk_update_existing_events(existing_events, source)
            stats["updated"] += updated_count
        
        return stats
    
    async def _bulk_insert_new_events(
        self,
        events: List[Tuple[str, EventCreate]],
        source: str
    ) -> int:
        """Insert new events in bulk."""
        if not events:
            return 0
        
        # Prepare event data for bulk insert
        event_data = []
        for event_hash, event in events:
            event_dict = event.dict()
            event_dict['source'] = source
            event_dict['scrape_hash'] = event_hash
            event_dict['last_scraped_at'] = datetime.now()
            event_data.append(event_dict)
        
        # Use PostgreSQL's INSERT with ON CONFLICT for better performance
        stmt = insert(Event).values(event_data)
        
        # Handle conflicts by doing nothing (shouldn't happen with proper duplicate detection)
        stmt = stmt.on_conflict_do_nothing(index_elements=['scrape_hash'])
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount
    
    async def _bulk_update_existing_events(
        self,
        events: List[Tuple[str, EventCreate]],
        source: str
    ) -> int:
        """Update existing events in bulk."""
        if not events:
            return 0
        
        updated_count = 0
        
        # Update events one by one (could be optimized further with bulk updates)
        for event_hash, event in events:
            # Check if event actually needs updating
            if await self._should_update_event(event_hash, event, source):
                stmt = (
                    update(Event)
                    .where(and_(Event.scrape_hash == event_hash, Event.source == source))
                    .values(
                        **event.dict(),
                        last_scraped_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                )
                
                result = await self.session.execute(stmt)
                if result.rowcount > 0:
                    updated_count += 1
        
        await self.session.commit()
        return updated_count
    
    async def _should_update_event(
        self,
        event_hash: str,
        new_event: EventCreate,
        source: str
    ) -> bool:
        """Check if an existing event should be updated."""
        # Get existing event
        stmt = select(Event).where(
            and_(Event.scrape_hash == event_hash, Event.source == source)
        )
        result = await self.session.execute(stmt)
        existing_event = result.scalar_one_or_none()
        
        if not existing_event:
            return False
        
        # Check if significant fields have changed
        significant_fields = ['title', 'date', 'time', 'price', 'description', 'location']
        
        for field in significant_fields:
            if getattr(existing_event, field) != getattr(new_event, field):
                return True
        
        # Check if event was last scraped more than 24 hours ago
        if (existing_event.last_scraped_at and 
            datetime.now() - existing_event.last_scraped_at > timedelta(hours=24)):
            return True
        
        return False
    
    async def _get_existing_hashes(
        self,
        hashes: List[str],
        source: str
    ) -> Set[str]:
        """Get existing event hashes for given source."""
        if not hashes:
            return set()
        
        stmt = select(Event.scrape_hash).where(
            and_(Event.scrape_hash.in_(hashes), Event.source == source)
        )
        result = await self.session.execute(stmt)
        return {row.scrape_hash for row in result}
    
    def _calculate_event_hash(self, event: EventCreate) -> str:
        """Calculate a unique hash for an event."""
        # Use key fields to create a unique identifier
        hash_string = f"{event.title}|{event.date}|{event.time}|{event.location}|{event.source}"
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def _update_search_vectors(self, source: str) -> None:
        """Update search vectors for events from source."""
        try:
            # Update search vectors for events without them
            stmt = text("""
                UPDATE events 
                SET search_vector = to_tsvector('simple', 
                    COALESCE(title, '') || ' ' || 
                    COALESCE(description, '') || ' ' || 
                    COALESCE(location, '') || ' ' ||
                    COALESCE(organizer, '')
                )
                WHERE source = :source 
                AND (search_vector IS NULL OR updated_at > NOW() - INTERVAL '1 hour')
            """)
            
            await self.session.execute(stmt, {"source": source})
            await self.session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to update search vectors for {source}: {e}")
    
    async def cleanup_old_events(
        self,
        source: str,
        days_old: int = 30
    ) -> int:
        """Remove old events from a source."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        stmt = delete(Event).where(
            and_(
                Event.source == source,
                Event.date < cutoff_date.date(),
                Event.last_scraped_at < cutoff_date
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        logger.info(f"Cleaned up {result.rowcount} old events from {source}")
        return result.rowcount
    
    async def get_scraping_statistics(self, source: str) -> Dict[str, Union[int, float]]:
        """Get scraping statistics for a source."""
        # Total events
        total_stmt = select(func.count(Event.id)).where(Event.source == source)
        total_result = await self.session.execute(total_stmt)
        total_events = total_result.scalar() or 0
        
        # Recent events (last 7 days)
        recent_date = datetime.now() - timedelta(days=7)
        recent_stmt = select(func.count(Event.id)).where(
            and_(Event.source == source, Event.created_at >= recent_date)
        )
        recent_result = await self.session.execute(recent_stmt)
        recent_events = recent_result.scalar() or 0
        
        # Events by status
        status_stmt = select(
            Event.event_status,
            func.count(Event.id)
        ).where(Event.source == source).group_by(Event.event_status)
        
        status_result = await self.session.execute(status_stmt)
        status_counts = {row.event_status: row.count for row in status_result}
        
        # Average events per day (last 30 days)
        avg_stmt = select(func.count(Event.id)).where(
            and_(
                Event.source == source,
                Event.created_at >= datetime.now() - timedelta(days=30)
            )
        )
        avg_result = await self.session.execute(avg_stmt)
        avg_events = (avg_result.scalar() or 0) / 30
        
        return {
            "total_events": total_events,
            "recent_events": recent_events,
            "status_counts": status_counts,
            "average_events_per_day": avg_events
        }
    
    async def optimize_database_indexes(self) -> None:
        """Optimize database indexes for scraping operations."""
        try:
            # Create indexes for common query patterns
            indexes = [
                # Composite index for scraping queries
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_source_date ON events(source, date)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_source_scraped_at ON events(source, last_scraped_at)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_hash_source ON events(scrape_hash, source)",
                
                # Performance indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_location_date ON events(location, date)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_featured_status ON events(is_featured, event_status)",
                
                # Search optimization
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_search_vector ON events USING gin(search_vector)",
            ]
            
            for index_sql in indexes:
                await self.session.execute(text(index_sql))
            
            await self.session.commit()
            logger.info("Database indexes optimized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to optimize database indexes: {e}")
    
    async def analyze_duplicate_patterns(self, source: str) -> Dict[str, int]:
        """Analyze duplicate patterns for a source."""
        # Find events with similar titles/locations
        duplicate_stmt = text("""
            SELECT 
                COUNT(*) as total_duplicates,
                COUNT(DISTINCT scrape_hash) as unique_hashes,
                COUNT(DISTINCT title) as unique_titles,
                COUNT(DISTINCT location) as unique_locations
            FROM events 
            WHERE source = :source
            AND created_at > NOW() - INTERVAL '30 days'
        """)
        
        result = await self.session.execute(duplicate_stmt, {"source": source})
        row = result.first()
        
        if row:
            return {
                "total_events": row.total_duplicates,
                "unique_hashes": row.unique_hashes,
                "unique_titles": row.unique_titles,
                "unique_locations": row.unique_locations,
                "duplicate_ratio": (row.total_duplicates - row.unique_hashes) / row.total_duplicates if row.total_duplicates > 0 else 0
            }
        else:
            return {}


@asynccontextmanager
async def get_database_optimizer():
    """Context manager for database optimizer."""
    async with get_db() as session:
        optimizer = DatabaseOptimizer(session)
        try:
            yield optimizer
        finally:
            await session.close()




class BulkEventProcessor:
    """High-performance bulk event processor for scraping operations."""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.processed_count = 0
        self.error_count = 0
        
    async def process_events(
        self,
        events: List[EventCreate],
        source: str,
        update_duplicates: bool = True
    ) -> Dict[str, int]:
        """Process events with optimized bulk operations."""
        async with get_database_optimizer() as optimizer:
            # Optimize indexes before processing
            await optimizer.optimize_database_indexes()
            
            # Process events in bulk
            stats = await optimizer.bulk_insert_events(events, source, update_duplicates)
            
            # Clean up old events
            await optimizer.cleanup_old_events(source, days_old=30)
            
            return stats
    
    async def get_processing_statistics(self, source: str) -> Dict[str, Union[int, float]]:
        """Get processing statistics for a source."""
        async with get_database_optimizer() as optimizer:
            return await optimizer.get_scraping_statistics(source)