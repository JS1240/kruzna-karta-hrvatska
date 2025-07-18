# Scraper System Maintenance Guide

## Overview

This guide provides comprehensive instructions for maintaining and operating the Croatian event scraper system after the improvements implemented in the code quality upgrade.

## Daily Operations

### 1. System Health Monitoring

**Check System Status**:
```bash
# Get overall system status
curl -X GET "http://localhost:8000/scraping/status"

# Check individual scraper status
curl -X GET "http://localhost:8000/scraping/scrapers"
```

**Key Metrics to Monitor**:
- Success rate should be >95%
- Error rate should be <1%
- Processing time should be stable
- Circuit breaker state should be "closed"

### 2. Log Monitoring

**Check Scraping Logs**:
```bash
# View recent scraping logs
tail -f scraping.log

# Check for errors
grep -i "error" scraping.log | tail -20

# Monitor performance metrics
grep -i "completed" scraping.log | tail -10
```

**Log Patterns to Watch**:
- `Circuit breaker open` - System overload
- `Retry attempt` - Network issues
- `Database error` - Database connectivity problems
- `Processing time >30s` - Performance degradation

### 3. Database Monitoring

**Check Database Performance**:
```sql
-- Check recent scraping activity
SELECT source, COUNT(*) as events, MAX(created_at) as last_scraped
FROM events 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY source;

-- Monitor database size
SELECT pg_size_pretty(pg_database_size('diidemo'));

-- Check for duplicate events
SELECT source, COUNT(*) as total, COUNT(DISTINCT scrape_hash) as unique_hashes
FROM events 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY source;
```

## Weekly Operations

### 1. Performance Review

**Run Performance Analysis**:
```bash
# Test all scrapers with quick scraping
for scraper in entrio croatia ulaznice infozagreb; do
    echo "Testing $scraper..."
    curl -X GET "http://localhost:8000/scraping/$scraper/quick?max_pages=1"
done
```

**Review Metrics**:
- Database query performance
- Memory usage patterns
- Error frequency by scraper
- Success rate trends

### 2. Database Maintenance

**Cleanup Old Events**:
```sql
-- Archive events older than 6 months
DELETE FROM events 
WHERE date < CURRENT_DATE - INTERVAL '6 months'
AND event_status = 'active';

-- Update search vectors
UPDATE events 
SET search_vector = to_tsvector('simple', 
    COALESCE(title, '') || ' ' || 
    COALESCE(description, '') || ' ' || 
    COALESCE(location, '')
)
WHERE search_vector IS NULL;
```

**Optimize Database**:
```sql
-- Analyze tables for query optimization
ANALYZE events;

-- Vacuum tables to reclaim space
VACUUM ANALYZE events;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND tablename = 'events';
```

### 3. Error Analysis

**Review Error Patterns**:
```python
# Python script to analyze error patterns
import json
import requests

# Get error statistics
response = requests.get("http://localhost:8000/scraping/status")
status_data = response.json()

# Analyze error handlers
for source, handler_stats in status_data.get("error_handlers", {}).items():
    print(f"Source: {source}")
    print(f"  Circuit Breaker: {handler_stats.get('circuit_breaker_state')}")
    print(f"  Total Errors: {handler_stats.get('total_errors')}")
    print(f"  Error Summary: {handler_stats.get('error_summary')}")
```

## Monthly Operations

### 1. System Optimization

**Review Database Indexes**:
```sql
-- Check index performance
SELECT 
    schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND tablename = 'events'
ORDER BY idx_scan DESC;

-- Add missing indexes if needed
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_source_date_status 
ON events(source, date, event_status);
```

**Performance Tuning**:
```sql
-- Update table statistics
ANALYZE events;

-- Check query performance
EXPLAIN ANALYZE SELECT * FROM events 
WHERE source = 'entrio' AND date >= CURRENT_DATE
ORDER BY date LIMIT 100;
```

### 2. Capacity Planning

**Review Storage Usage**:
```sql
-- Check table sizes
SELECT 
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                   pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Monitor Growth Trends**:
```sql
-- Events per month trend
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as events_count,
    COUNT(DISTINCT source) as active_sources
FROM events
WHERE created_at >= NOW() - INTERVAL '12 months'
GROUP BY month
ORDER BY month;
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. High Error Rate

**Symptoms**: Success rate <90%, many failed requests
**Investigation**:
```bash
# Check error logs
grep -i "error" scraping.log | tail -50

# Check circuit breaker status
curl -X GET "http://localhost:8000/scraping/status" | jq '.error_handlers'
```

**Solutions**:
- Restart scraper services if circuit breakers are open
- Check network connectivity to target websites
- Verify proxy settings and credentials
- Review scraper code for parsing errors

#### 2. Database Performance Issues

**Symptoms**: Slow database queries, high CPU usage
**Investigation**:
```sql
-- Check active queries
SELECT pid, query, state, query_start, now() - query_start as duration
FROM pg_stat_activity
WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- Check lock conflicts
SELECT * FROM pg_locks WHERE NOT granted;
```

**Solutions**:
- Optimize slow queries with proper indexes
- Increase connection pool size
- Run VACUUM and ANALYZE on tables
- Consider partitioning large tables

#### 3. Memory Issues

**Symptoms**: High memory usage, out of memory errors
**Investigation**:
```bash
# Monitor memory usage
free -h
ps aux | grep python | sort -k4 -nr

# Check batch sizes
grep -i "batch" scraping.log | tail -10
```

**Solutions**:
- Reduce batch sizes in database operations
- Implement pagination for large result sets
- Add memory limits to scraper processes
- Monitor and restart processes with memory leaks

#### 4. Scraper Failures

**Symptoms**: Specific scrapers consistently failing
**Investigation**:
```bash
# Check specific scraper logs
grep -i "entrio" scraping.log | tail -20

# Test scraper manually
curl -X GET "http://localhost:8000/scraping/entrio/quick?max_pages=1"
```

**Solutions**:
- Update scraper parsing logic for website changes
- Adjust retry configurations
- Check website blocking or rate limiting
- Verify scraper authentication credentials

## Monitoring and Alerting

### Key Metrics to Track

1. **Success Rate**: >95% (alert if <90%)
2. **Error Rate**: <1% (alert if >5%)
3. **Processing Time**: <30s per page (alert if >60s)
4. **Database Performance**: <100ms queries (alert if >500ms)
5. **Memory Usage**: <2GB per process (alert if >4GB)

### Alerting Setup

**Example Alert Configuration**:
```yaml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 0.05"
    action: "email, slack"
    
  - name: "Database Slow Query"
    condition: "query_time > 500ms"
    action: "log, email"
    
  - name: "Circuit Breaker Open"
    condition: "circuit_breaker_state = 'open'"
    action: "immediate, email, sms"
```

## Backup and Recovery

### Database Backups

**Daily Backup**:
```bash
# Create daily backup
pg_dump -h localhost -U postgres -d diidemo > backup_$(date +%Y%m%d).sql

# Compress backup
gzip backup_$(date +%Y%m%d).sql

# Upload to cloud storage
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://your-backup-bucket/
```

**Recovery Process**:
```bash
# Restore from backup
gunzip backup_YYYYMMDD.sql.gz
psql -h localhost -U postgres -d diidemo < backup_YYYYMMDD.sql
```

### Configuration Backups

**Application Configuration**:
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  app/config/ \
  app/core/ \
  docker-compose.yml \
  requirements.txt
```

## Scaling Considerations

### Horizontal Scaling

**Multiple Scraper Instances**:
```yaml
# docker-compose.yml
services:
  scraper-1:
    build: .
    environment:
      - SCRAPER_ID=1
      - SCRAPER_SOURCES=entrio,croatia
      
  scraper-2:
    build: .
    environment:
      - SCRAPER_ID=2
      - SCRAPER_SOURCES=ulaznice,infozagreb
```

**Load Balancing**:
```nginx
# nginx.conf
upstream scraper_backend {
    server scraper-1:8000;
    server scraper-2:8000;
}

server {
    location /scraping/ {
        proxy_pass http://scraper_backend;
    }
}
```

### Database Scaling

**Connection Pooling**:
```python
# Database connection pool configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

**Read Replicas**:
```python
# Read/write splitting
DATABASES = {
    "write": "postgresql://user:pass@primary-db:5432/diidemo",
    "read": "postgresql://user:pass@replica-db:5432/diidemo"
}
```

## Security Considerations

### Access Control

**API Security**:
```python
# Add authentication to scraping endpoints
@router.post("/scraping/{source}")
async def scrape_source(source: str, current_user: User = Depends(get_current_user)):
    # Scraping logic
    pass
```

**Database Security**:
```sql
-- Create dedicated scraper user
CREATE USER scraper_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON events TO scraper_user;
```

### Data Protection

**Sensitive Data Handling**:
- Never log sensitive information
- Use environment variables for credentials
- Encrypt database connections
- Implement proper data retention policies

## Contact Information

**Team Contacts**:
- **System Administrator**: admin@diidemo.hr
- **Database Administrator**: dba@diidemo.hr
- **Development Team**: dev@diidemo.hr

**Emergency Contacts**:
- **On-call Engineer**: +385-XX-XXX-XXXX
- **Technical Lead**: +385-XX-XXX-XXXX

## Documentation Updates

This guide should be updated when:
- New scrapers are added
- System architecture changes
- Database schema modifications
- Performance tuning adjustments
- Security policy updates

**Last Updated**: [Current Date]
**Version**: 1.0
**Next Review**: [Next Month]