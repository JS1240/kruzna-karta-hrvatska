-- Security hardening and GDPR compliance schema for Kruzna Karta Hrvatska
-- Run this after initial schema setup to add security and compliance features

-- ===============================================
-- SECURITY HARDENING TABLES
-- ===============================================

-- Audit logging table for compliance tracking
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    operation VARCHAR(20) NOT NULL, -- SELECT, INSERT, UPDATE, DELETE
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    session_id VARCHAR(255),
    changes JSONB, -- Before/after values for UPDATE operations
    
    -- Indexes for performance
    INDEX idx_audit_logs_user_timestamp (user_id, timestamp),
    INDEX idx_audit_logs_table_timestamp (table_name, timestamp),
    INDEX idx_audit_logs_operation_timestamp (operation, timestamp)
);

-- User sessions table for session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Security constraints
    CONSTRAINT session_token_length CHECK (LENGTH(session_token) >= 32),
    
    -- Indexes
    INDEX idx_user_sessions_token (session_token),
    INDEX idx_user_sessions_user_active (user_id, is_active),
    INDEX idx_user_sessions_expires (expires_at)
);

-- Password history for password policy enforcement
CREATE TABLE IF NOT EXISTS user_password_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_password_history_user_date (user_id, created_at)
);

-- Role-based access control
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User role assignments
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    
    -- Prevent duplicate role assignments
    UNIQUE(user_id, role_id),
    
    -- Indexes
    INDEX idx_user_roles_user (user_id),
    INDEX idx_user_roles_role (role_id)
);

-- Permissions system
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(50), -- Table or API resource
    action VARCHAR(20), -- SELECT, INSERT, UPDATE, DELETE, etc.
    permissions JSONB, -- Detailed permissions configuration
    created_at TIMESTAMP DEFAULT NOW()
);

-- Role permissions mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    permission_id INTEGER NOT NULL REFERENCES permissions(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicate permission grants
    UNIQUE(role_id, permission_id),
    
    -- Indexes
    INDEX idx_role_permissions_role (role_id),
    INDEX idx_role_permissions_permission (permission_id)
);

-- Security incidents logging
CREATE TABLE IF NOT EXISTS security_incidents (
    id SERIAL PRIMARY KEY,
    incident_type VARCHAR(50) NOT NULL, -- failed_login, suspicious_activity, etc.
    user_id INTEGER REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_security_incidents_type_date (incident_type, created_at),
    INDEX idx_security_incidents_user_date (user_id, created_at),
    INDEX idx_security_incidents_severity (severity, resolved)
);

-- ===============================================
-- GDPR COMPLIANCE TABLES
-- ===============================================

-- Data subject requests tracking (GDPR Articles 15-22)
CREATE TABLE IF NOT EXISTS gdpr_requests (
    id SERIAL PRIMARY KEY,
    request_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    request_type VARCHAR(20) NOT NULL, -- access, rectification, erasure, portability, restriction
    user_id INTEGER REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    requested_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, rejected
    reason TEXT,
    processor_id INTEGER REFERENCES users(id),
    response_data JSONB, -- Data provided for access/portability requests
    
    -- GDPR compliance constraints
    CONSTRAINT valid_request_type CHECK (request_type IN ('access', 'rectification', 'erasure', 'portability', 'restriction')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'rejected')),
    
    -- Indexes
    INDEX idx_gdpr_requests_type_status (request_type, status),
    INDEX idx_gdpr_requests_user_date (user_id, requested_at),
    INDEX idx_gdpr_requests_email (email)
);

-- GDPR consent management
CREATE TABLE IF NOT EXISTS gdpr_consent (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    consent_type VARCHAR(50) NOT NULL, -- analytics, marketing, third_party
    consent_given BOOLEAN NOT NULL,
    consent_date TIMESTAMP DEFAULT NOW(),
    withdrawal_date TIMESTAMP,
    legal_basis VARCHAR(50), -- consent, contract, legitimate_interest, etc.
    purpose TEXT NOT NULL,
    data_categories TEXT[], -- Array of data categories
    
    -- Track consent changes
    version INTEGER DEFAULT 1,
    
    -- Indexes
    INDEX idx_gdpr_consent_user_type (user_id, consent_type),
    INDEX idx_gdpr_consent_type_given (consent_type, consent_given),
    INDEX idx_gdpr_consent_date (consent_date)
);

-- Data processing activities record (GDPR Article 30)
CREATE TABLE IF NOT EXISTS gdpr_processing_activities (
    id SERIAL PRIMARY KEY,
    activity_name VARCHAR(255) NOT NULL,
    purpose TEXT NOT NULL,
    legal_basis VARCHAR(50) NOT NULL,
    data_categories TEXT[] NOT NULL,
    data_subjects TEXT NOT NULL,
    recipients TEXT[],
    retention_period INTEGER, -- Days
    technical_measures TEXT[],
    organizational_measures TEXT[],
    cross_border_transfers BOOLEAN DEFAULT false,
    adequacy_decision BOOLEAN DEFAULT false,
    safeguards TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_processing_activities_name (activity_name),
    INDEX idx_processing_activities_legal_basis (legal_basis)
);

-- Data erasure log for audit trail
CREATE TABLE IF NOT EXISTS gdpr_erasure_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    request_id UUID NOT NULL REFERENCES gdpr_requests(request_id),
    erased_at TIMESTAMP DEFAULT NOW(),
    actions JSONB NOT NULL, -- Details of what was erased/anonymized
    retained_data JSONB, -- What data was retained and why
    
    -- Indexes
    INDEX idx_erasure_log_user (user_id),
    INDEX idx_erasure_log_request (request_id),
    INDEX idx_erasure_log_date (erased_at)
);

-- Processing restrictions tracking (GDPR Article 18)
CREATE TABLE IF NOT EXISTS gdpr_processing_restrictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    request_id UUID NOT NULL REFERENCES gdpr_requests(request_id),
    restricted_at TIMESTAMP DEFAULT NOW(),
    restriction_reason TEXT,
    lifted_at TIMESTAMP,
    lift_reason TEXT,
    
    -- Indexes
    INDEX idx_processing_restrictions_user (user_id),
    INDEX idx_processing_restrictions_active (user_id, lifted_at)
);

-- Data breach incidents (GDPR Article 33-34)
CREATE TABLE IF NOT EXISTS gdpr_data_breaches (
    id SERIAL PRIMARY KEY,
    breach_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    discovered_at TIMESTAMP NOT NULL,
    reported_at TIMESTAMP,
    breach_type VARCHAR(50) NOT NULL, -- confidentiality, integrity, availability
    affected_records INTEGER,
    affected_data_subjects INTEGER,
    data_categories TEXT[],
    breach_description TEXT NOT NULL,
    cause TEXT,
    consequences TEXT,
    measures_taken TEXT,
    authority_notified BOOLEAN DEFAULT false,
    subjects_notified BOOLEAN DEFAULT false,
    notification_method VARCHAR(50),
    
    -- GDPR 72-hour reporting requirement
    late_notification BOOLEAN GENERATED ALWAYS AS (
        reported_at IS NOT NULL AND 
        reported_at > discovered_at + INTERVAL '72 hours'
    ) STORED,
    
    -- Indexes
    INDEX idx_data_breaches_discovered (discovered_at),
    INDEX idx_data_breaches_type (breach_type),
    INDEX idx_data_breaches_severity (affected_records DESC)
);

-- Legal holds for litigation/investigation
CREATE TABLE IF NOT EXISTS legal_holds (
    id SERIAL PRIMARY KEY,
    hold_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    matter_name VARCHAR(255) NOT NULL,
    hold_reason TEXT NOT NULL,
    custodian VARCHAR(255),
    data_types TEXT[],
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    
    -- Indexes
    INDEX idx_legal_holds_user_active (user_id, is_active),
    INDEX idx_legal_holds_active (is_active, start_date)
);

-- ===============================================
-- SECURITY FUNCTIONS AND TRIGGERS
-- ===============================================

-- Function to hash and salt passwords
CREATE OR REPLACE FUNCTION hash_password(password TEXT)
RETURNS TEXT AS $$
BEGIN
    -- This would use a proper password hashing library in the application
    -- For now, return a placeholder
    RETURN 'hashed_' || password;
END;
$$ LANGUAGE plpgsql;

-- Function to log audit events
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
BEGIN
    -- Log the operation
    INSERT INTO audit_logs (
        user_id,
        operation,
        table_name,
        record_id,
        timestamp,
        changes
    ) VALUES (
        COALESCE(current_setting('app.current_user_id', true)::INTEGER, 0),
        TG_OP,
        TG_TABLE_NAME,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.id 
            ELSE NEW.id 
        END,
        NOW(),
        CASE 
            WHEN TG_OP = 'UPDATE' THEN 
                jsonb_build_object('old', to_jsonb(OLD), 'new', to_jsonb(NEW))
            WHEN TG_OP = 'DELETE' THEN 
                to_jsonb(OLD)
            ELSE 
                to_jsonb(NEW)
        END
    );
    
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions 
    WHERE expires_at < NOW() OR last_activity < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO audit_logs (operation, table_name, timestamp, changes)
    VALUES ('CLEANUP', 'user_sessions', NOW(), 
            jsonb_build_object('deleted_sessions', deleted_count));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to check data retention compliance
CREATE OR REPLACE FUNCTION check_data_retention()
RETURNS TABLE(
    table_name TEXT,
    expired_records BIGINT,
    oldest_record TIMESTAMP
) AS $$
BEGIN
    -- Check users table (3 years retention)
    RETURN QUERY
    SELECT 'users'::TEXT, 
           COUNT(*)::BIGINT,
           MIN(last_login)
    FROM users 
    WHERE last_login < NOW() - INTERVAL '3 years'
    AND gdpr_erased = false;
    
    -- Check event_views table (90 days retention)
    RETURN QUERY
    SELECT 'event_views'::TEXT,
           COUNT(*)::BIGINT,
           MIN(viewed_at)
    FROM event_views 
    WHERE viewed_at < NOW() - INTERVAL '90 days';
    
    -- Check user_interactions table (90 days retention)
    RETURN QUERY
    SELECT 'user_interactions'::TEXT,
           COUNT(*)::BIGINT,
           MIN(interacted_at)
    FROM user_interactions 
    WHERE interacted_at < NOW() - INTERVAL '90 days';
    
    -- Check search_logs table (7 days retention)
    RETURN QUERY
    SELECT 'search_logs'::TEXT,
           COUNT(*)::BIGINT,
           MIN(searched_at)
    FROM search_logs 
    WHERE searched_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- AUDIT TRIGGERS
-- ===============================================

-- Add audit triggers to sensitive tables
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_events_trigger
    AFTER INSERT OR UPDATE OR DELETE ON events
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_user_roles_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_roles
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_gdpr_requests_trigger
    AFTER INSERT OR UPDATE OR DELETE ON gdpr_requests
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

-- ===============================================
-- SECURITY VIEWS
-- ===============================================

-- View for user permissions (for authorization checks)
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id as user_id,
    u.email,
    r.name as role_name,
    p.name as permission_name,
    p.resource,
    p.action,
    p.permissions
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.is_active = true;

-- View for active sessions
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT 
    s.id,
    s.user_id,
    u.email,
    s.ip_address,
    s.created_at,
    s.last_activity,
    s.expires_at,
    (s.expires_at > NOW()) as is_valid
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = true
ORDER BY s.last_activity DESC;

-- View for GDPR compliance dashboard
CREATE OR REPLACE VIEW v_gdpr_compliance AS
SELECT 
    (SELECT COUNT(*) FROM users WHERE gdpr_erased = false) as active_users,
    (SELECT COUNT(*) FROM users WHERE gdpr_erased = true) as erased_users,
    (SELECT COUNT(*) FROM gdpr_requests WHERE status = 'pending') as pending_requests,
    (SELECT COUNT(*) FROM gdpr_requests WHERE requested_at >= NOW() - INTERVAL '30 days') as recent_requests,
    (SELECT COUNT(*) FROM gdpr_data_breaches WHERE discovered_at >= NOW() - INTERVAL '1 year') as breaches_this_year,
    (SELECT COUNT(*) FROM legal_holds WHERE is_active = true) as active_legal_holds;

-- ===============================================
-- DEFAULT ROLES AND PERMISSIONS
-- ===============================================

-- Insert default roles
INSERT INTO roles (name, description, is_system_role) VALUES
    ('admin', 'System administrator with full access', true),
    ('moderator', 'Content moderator with event management access', true),
    ('user', 'Regular user with basic access', true),
    ('guest', 'Guest user with read-only access', true)
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO permissions (name, description, resource, action) VALUES
    ('events.read', 'Read events', 'events', 'SELECT'),
    ('events.create', 'Create events', 'events', 'INSERT'),
    ('events.update', 'Update events', 'events', 'UPDATE'),
    ('events.delete', 'Delete events', 'events', 'DELETE'),
    ('users.read', 'Read users', 'users', 'SELECT'),
    ('users.create', 'Create users', 'users', 'INSERT'),
    ('users.update', 'Update users', 'users', 'UPDATE'),
    ('users.delete', 'Delete users', 'users', 'DELETE'),
    ('admin.access', 'Access admin panel', 'admin', 'ACCESS'),
    ('gdpr.manage', 'Manage GDPR requests', 'gdpr', 'MANAGE')
ON CONFLICT (name) DO NOTHING;

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE (r.name = 'admin') -- Admin gets all permissions
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'moderator' 
AND p.name IN ('events.read', 'events.create', 'events.update', 'users.read')
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'user' 
AND p.name IN ('events.read', 'users.read')
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'guest' 
AND p.name IN ('events.read')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ===============================================
-- GDPR DATA PROCESSING RECORDS
-- ===============================================

-- Insert default processing activities
INSERT INTO gdpr_processing_activities (
    activity_name,
    purpose,
    legal_basis,
    data_categories,
    data_subjects,
    recipients,
    retention_period,
    technical_measures,
    organizational_measures
) VALUES (
    'User Account Management',
    'Managing user accounts for the Kruzna Karta Hrvatska platform',
    'contract',
    ARRAY['personal_identifiable', 'contact_information'],
    'Users of the Kruzna Karta Hrvatska platform',
    ARRAY['Internal staff', 'Technical support'],
    1095, -- 3 years
    ARRAY['AES-256 encryption', 'TLS 1.3 transport', 'Access controls'],
    ARRAY['Staff training', 'Regular audits', 'Incident response procedures']
), (
    'Event Analytics',
    'Analyzing user behavior to improve event recommendations',
    'legitimate_interests',
    ARRAY['behavioral', 'technical'],
    'Platform users',
    ARRAY['Analytics team', 'Product managers'],
    90, -- 3 months
    ARRAY['Data anonymization', 'Aggregation', 'Access controls'],
    ARRAY['Privacy impact assessment', 'Data minimization practices']
), (
    'Marketing Communications',
    'Sending promotional emails about Croatian events',
    'consent',
    ARRAY['contact_information', 'preferences'],
    'Opted-in users',
    ARRAY['Email service provider'],
    1095, -- 3 years or until consent withdrawn
    ARRAY['Encryption in transit', 'Secure email systems'],
    ARRAY['Consent management', 'Easy unsubscribe process']
)
ON CONFLICT DO NOTHING;

-- ===============================================
-- INDEXES FOR PERFORMANCE
-- ===============================================

-- Additional indexes for security and compliance queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_gdpr_status 
ON users(gdpr_erased, processing_restricted);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login_retention 
ON users(last_login) WHERE gdpr_erased = false;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_sensitive_operations 
ON audit_logs(operation, table_name, timestamp) 
WHERE table_name IN ('users', 'gdpr_requests', 'user_roles');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gdpr_requests_processing_time 
ON gdpr_requests(request_type, requested_at, processed_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_incidents_unresolved 
ON security_incidents(severity, created_at) WHERE resolved = false;

-- ===============================================
-- SECURITY POLICIES (RLS - Row Level Security)
-- ===============================================

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE gdpr_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY user_isolation_policy ON users
FOR ALL TO authenticated_user
USING (id = current_setting('app.current_user_id')::INTEGER);

-- Policy: Users can only see their own GDPR requests
CREATE POLICY gdpr_requests_isolation_policy ON gdpr_requests
FOR ALL TO authenticated_user
USING (user_id = current_setting('app.current_user_id')::INTEGER);

-- Policy: Admins can see all audit logs
CREATE POLICY audit_logs_admin_policy ON audit_logs
FOR SELECT TO admin_role
USING (true);

-- Policy: Users can see their own audit logs
CREATE POLICY audit_logs_user_policy ON audit_logs
FOR SELECT TO authenticated_user
USING (user_id = current_setting('app.current_user_id')::INTEGER);

-- ===============================================
-- COMPLETION MESSAGE
-- ===============================================

-- Log security schema setup
INSERT INTO audit_logs (operation, table_name, timestamp, changes)
VALUES ('SCHEMA_SETUP', 'security_schema', NOW(), 
        jsonb_build_object('message', 'Security hardening and GDPR compliance schema installed'));

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Security and GDPR compliance schema setup complete!';
    RAISE NOTICE 'Features installed:';
    RAISE NOTICE '- Audit logging and security monitoring';
    RAISE NOTICE '- Role-based access control (RBAC)';
    RAISE NOTICE '- GDPR compliance framework';
    RAISE NOTICE '- Data retention and cleanup procedures';
    RAISE NOTICE '- Security incident tracking';
    RAISE NOTICE '- Row-level security policies';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Configure encryption keys in application';
    RAISE NOTICE '2. Set up regular data retention cleanup jobs';
    RAISE NOTICE '3. Train staff on GDPR compliance procedures';
    RAISE NOTICE '4. Test data subject request workflows';
END $$;