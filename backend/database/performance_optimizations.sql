-- Performance optimization queries for Kruzna Karta Hrvatska database
-- Run these after initial data migration for optimal performance

-- ===============================================
-- INDEX OPTIMIZATIONS
-- ===============================================

-- Events table performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_date_status 
ON events(date, event_status) WHERE event_status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_location_gin 
ON events USING gin(to_tsvector('croatian', location));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_featured_date 
ON events(is_featured, date) WHERE is_featured = true AND event_status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_category_date 
ON events(category_id, date) WHERE event_status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_venue_date 
ON events(venue_id, date) WHERE event_status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_view_count 
ON events(view_count DESC) WHERE event_status = 'active';

-- Geographic index for location-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_geographic 
ON events USING gist(ll_to_earth(latitude, longitude)) 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND event_status = 'active';

-- Full-text search optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_search_vector_gin 
ON events USING gin(search_vector);

-- Composite index for common filtered queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_category_status_date 
ON events(category_id, event_status, date) WHERE event_status = 'active';

-- Translation table indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_translations_event_lang 
ON event_translations(event_id, language_code);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_category_translations_category_lang 
ON category_translations(category_id, language_code);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venue_translations_venue_lang 
ON venue_translations(venue_id, language_code);

-- Analytics table indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_views_event_date_user 
ON event_views(event_id, viewed_at, user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_logs_date_query 
ON search_logs(searched_at, query);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_interactions_type_entity_date 
ON user_interactions(interaction_type, entity_type, entity_id, interacted_at);

-- Performance metrics indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_performance_event_date 
ON event_performance_metrics(event_id, date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_metrics_type_date 
ON platform_metrics(metric_type, date DESC);

-- User activity indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_created 
ON users(is_active, created_at) WHERE is_active = true;

-- ===============================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ===============================================

-- Popular events materialized view (refreshed periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_popular_events AS
SELECT 
    e.id,
    e.name,
    e.date,
    e.time,
    e.location,
    e.image,
    e.is_featured,
    e.view_count,
    e.category_id,
    e.venue_id,
    COALESCE(em.total_views, 0) as total_views_7d,
    COALESCE(em.unique_views, 0) as unique_views_7d,
    COALESCE(em.bounce_rate, 0) as bounce_rate_7d,
    c.name as category_name,
    v.name as venue_name,
    v.city as venue_city
FROM events e
LEFT JOIN event_categories c ON e.category_id = c.id
LEFT JOIN venues v ON e.venue_id = v.id
LEFT JOIN (
    SELECT 
        event_id,
        SUM(total_views) as total_views,
        SUM(unique_views) as unique_views,
        AVG(bounce_rate) as bounce_rate
    FROM event_performance_metrics 
    WHERE date >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY event_id
) em ON e.id = em.event_id
WHERE e.event_status = 'active' 
  AND e.date >= CURRENT_DATE
ORDER BY 
    e.is_featured DESC,
    COALESCE(em.total_views, e.view_count, 0) DESC,
    e.date ASC;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_popular_events_id ON mv_popular_events(id);
CREATE INDEX IF NOT EXISTS idx_mv_popular_events_views ON mv_popular_events(total_views_7d DESC);
CREATE INDEX IF NOT EXISTS idx_mv_popular_events_featured ON mv_popular_events(is_featured, total_views_7d DESC);

-- Events by city materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_events_by_city AS
SELECT 
    TRIM(SPLIT_PART(location, ',', 1)) as city,
    COUNT(*) as event_count,
    COUNT(*) FILTER (WHERE date >= CURRENT_DATE) as upcoming_events,
    COUNT(*) FILTER (WHERE is_featured = true) as featured_events,
    AVG(view_count) as avg_view_count,
    MAX(date) as latest_event_date
FROM events 
WHERE event_status = 'active' 
  AND location IS NOT NULL 
  AND location != ''
GROUP BY TRIM(SPLIT_PART(location, ',', 1))
HAVING COUNT(*) >= 3  -- Only cities with 3+ events
ORDER BY event_count DESC;

-- Create index on city view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_events_by_city_city ON mv_events_by_city(city);

-- ===============================================
-- PERFORMANCE STATISTICS TABLES
-- ===============================================

-- Query performance tracking table
CREATE TABLE IF NOT EXISTS query_performance_log (
    id SERIAL PRIMARY KEY,
    query_type VARCHAR(100) NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    rows_returned INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    executed_at TIMESTAMP DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_query_performance_type_time 
ON query_performance_log(query_type, executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_query_performance_hash_time 
ON query_performance_log(query_hash, executed_at DESC);

-- ===============================================
-- DATABASE MAINTENANCE FUNCTIONS
-- ===============================================

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_events;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_events_by_city;
    
    -- Log the refresh
    INSERT INTO query_performance_log (query_type, query_hash, execution_time_ms, rows_returned)
    VALUES ('materialized_view_refresh', 'mv_refresh', 0, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to analyze query performance
CREATE OR REPLACE FUNCTION analyze_slow_queries()
RETURNS TABLE(
    query_type VARCHAR(100),
    avg_execution_time_ms NUMERIC,
    max_execution_time_ms INTEGER,
    query_count BIGINT,
    cache_hit_ratio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        qpl.query_type,
        ROUND(AVG(qpl.execution_time_ms), 2) as avg_execution_time_ms,
        MAX(qpl.execution_time_ms) as max_execution_time_ms,
        COUNT(*) as query_count,
        ROUND(
            (COUNT(*) FILTER (WHERE qpl.cache_hit = true)::NUMERIC / COUNT(*)) * 100, 
            2
        ) as cache_hit_ratio
    FROM query_performance_log qpl
    WHERE qpl.executed_at >= NOW() - INTERVAL '24 hours'
    GROUP BY qpl.query_type
    ORDER BY avg_execution_time_ms DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to update search vectors
CREATE OR REPLACE FUNCTION update_search_vectors()
RETURNS void AS $$
BEGIN
    UPDATE events 
    SET search_vector = to_tsvector('croatian', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '') || ' ' || 
        COALESCE(location, '') || ' ' ||
        COALESCE(organizer, '')
    )
    WHERE search_vector IS NULL 
       OR updated_at > NOW() - INTERVAL '1 hour';
    
    -- Log the update
    INSERT INTO query_performance_log (query_type, query_hash, execution_time_ms, rows_returned)
    VALUES ('search_vector_update', 'search_update', 0, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to clean old analytics data
CREATE OR REPLACE FUNCTION cleanup_old_analytics(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM event_views 
    WHERE viewed_at < NOW() - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM search_logs 
    WHERE searched_at < NOW() - (retention_days || ' days')::INTERVAL;
    
    DELETE FROM user_interactions 
    WHERE interacted_at < NOW() - (retention_days || ' days')::INTERVAL;
    
    -- Log the cleanup
    INSERT INTO query_performance_log (query_type, query_hash, execution_time_ms, rows_returned)
    VALUES ('analytics_cleanup', 'cleanup', 0, deleted_count);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- PERFORMANCE OPTIMIZATION SETTINGS
-- ===============================================

-- Update PostgreSQL configuration for better performance
-- Note: These should be added to postgresql.conf, not run as SQL

/*
Recommended postgresql.conf settings for Kruzna Karta Hrvatska:

# Memory settings
shared_buffers = 256MB                    # 25% of total RAM
effective_cache_size = 1GB                # 75% of total RAM
work_mem = 16MB                           # For complex queries
maintenance_work_mem = 64MB               # For maintenance operations

# Connection settings
max_connections = 100                     # Adjust based on load
connection_limit = 50                     # Per database

# Query planner settings
random_page_cost = 1.1                    # For SSD storage
effective_io_concurrency = 200            # For SSD storage
seq_page_cost = 1.0                       # Sequential scan cost

# WAL settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9
wal_compression = on

# Logging settings for performance monitoring
log_min_duration_statement = 1000         # Log queries > 1 second
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Full-text search settings
default_text_search_config = 'croatian'   # Croatian language support

# Auto vacuum settings
autovacuum = on
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
*/

-- ===============================================
-- SCHEDULED MAINTENANCE TASKS
-- ===============================================

-- These should be run via cron or application scheduler

-- Daily tasks (run at 3 AM)
-- SELECT refresh_performance_views();
-- SELECT update_search_vectors();

-- Weekly tasks (run on Sunday at 4 AM)  
-- SELECT cleanup_old_analytics(90);
-- VACUUM ANALYZE;

-- Monthly tasks (run on 1st of month at 5 AM)
-- REINDEX DATABASE kruzna_karta_hrvatska;
-- VACUUM FULL pg_stat_statements; -- If pg_stat_statements is enabled

-- ===============================================
-- PERFORMANCE MONITORING QUERIES
-- ===============================================

-- Check index usage
CREATE OR REPLACE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE 
        WHEN idx_scan = 0 THEN 'Never used'
        WHEN idx_scan < 100 THEN 'Low usage'
        WHEN idx_scan < 1000 THEN 'Medium usage'
        ELSE 'High usage'
    END as usage_level
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Check table sizes
CREATE OR REPLACE VIEW v_table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check slow queries (requires pg_stat_statements extension)
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

CREATE OR REPLACE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    stddev_time,
    rows
FROM pg_stat_statements 
WHERE mean_time > 1000  -- Queries taking more than 1 second on average
ORDER BY mean_time DESC;

-- Grant permissions for monitoring views
GRANT SELECT ON v_index_usage TO PUBLIC;
GRANT SELECT ON v_table_sizes TO PUBLIC;
GRANT SELECT ON v_slow_queries TO PUBLIC;

-- ===============================================
-- COMPLETION MESSAGE
-- ===============================================

-- Log successful optimization setup
INSERT INTO query_performance_log (query_type, query_hash, execution_time_ms, rows_returned)
VALUES ('performance_optimization_setup', 'setup_complete', 0, 0);

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Performance optimization setup complete!';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Review and apply postgresql.conf settings';
    RAISE NOTICE '2. Set up scheduled maintenance tasks';
    RAISE NOTICE '3. Monitor performance using the created views';
    RAISE NOTICE '4. Configure Redis for application caching';
END $$;