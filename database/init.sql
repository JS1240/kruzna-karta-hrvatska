-- Database initialization for Diidemo.hr Croatian Events Platform
-- Enhanced schema for scraped events with DBeaver compatibility

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create event categories table
CREATE TABLE IF NOT EXISTS event_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6', -- Hex color for UI
    icon VARCHAR(50), -- Icon name for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create venues table for better location management
CREATE TABLE IF NOT EXISTS venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) DEFAULT 'Croatia',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    capacity INTEGER,
    venue_type VARCHAR(50), -- club, arena, outdoor, theater, etc.
    website VARCHAR(500),
    phone VARCHAR(50),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, city) -- Prevent duplicate venues in same city
);

-- Create events table with enhanced schema
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    
    -- Core event information (as requested)
    name VARCHAR(500) NOT NULL, -- Increased length for longer event names
    time VARCHAR(50) NOT NULL, -- Could be "19:00", "19:00-23:00", "TBA", etc.
    date DATE NOT NULL,
    price VARCHAR(100), -- "50 HRK", "Free", "50-100 HRK", "From 25 EUR"
    description TEXT,
    link VARCHAR(1000), -- Increased for long URLs
    image VARCHAR(1000), -- Increased for long image URLs
    location VARCHAR(500) NOT NULL, -- City, venue, or full address
    
    -- Enhanced fields for better functionality
    category_id INTEGER REFERENCES event_categories(id),
    venue_id INTEGER REFERENCES venues(id),
    
    -- Geographic data for mapping
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Event metadata
    source VARCHAR(50) NOT NULL DEFAULT 'manual', -- entrio, croatia, manual, api
    external_id VARCHAR(255), -- ID from source website
    event_status VARCHAR(20) DEFAULT 'active', -- active, cancelled, postponed, sold_out
    is_featured BOOLEAN DEFAULT FALSE,
    is_recurring BOOLEAN DEFAULT FALSE,
    
    -- Additional event details
    organizer VARCHAR(255),
    age_restriction VARCHAR(50), -- "18+", "All ages", "21+"
    ticket_types JSONB, -- Store complex ticket information
    tags TEXT[], -- Array of tags for filtering
    
    -- SEO and search
    slug VARCHAR(600) UNIQUE, -- URL-friendly version of name
    search_vector tsvector, -- Full-text search
    
    -- Date/time management
    end_date DATE, -- For multi-day events
    end_time VARCHAR(50),
    timezone VARCHAR(50) DEFAULT 'Europe/Zagreb',
    
    -- Tracking and management
    view_count INTEGER DEFAULT 0,
    last_scraped_at TIMESTAMP,
    scrape_hash VARCHAR(64), -- Hash of content for duplicate detection
    
    -- Standard timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT events_date_check CHECK (date >= CURRENT_DATE - INTERVAL '1 year'),
    CONSTRAINT events_end_date_check CHECK (end_date IS NULL OR end_date >= date),
    CONSTRAINT events_status_check CHECK (event_status IN ('active', 'cancelled', 'postponed', 'sold_out', 'draft')),
    CONSTRAINT events_source_check CHECK (source IN ('entrio', 'croatia', 'manual', 'api', 'facebook', 'eventbrite'))
);

-- Create comprehensive indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
CREATE INDEX IF NOT EXISTS idx_events_location ON events(location);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category_id);
CREATE INDEX IF NOT EXISTS idx_events_venue ON events(venue_id);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(event_status);
CREATE INDEX IF NOT EXISTS idx_events_featured ON events(is_featured) WHERE is_featured = TRUE;
CREATE INDEX IF NOT EXISTS idx_events_date_status ON events(date, event_status);
CREATE INDEX IF NOT EXISTS idx_events_location_gin ON events USING gin(to_tsvector('simple', location));
CREATE INDEX IF NOT EXISTS idx_events_search ON events USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_events_tags ON events USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_events_coordinates ON events(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_scrape_hash ON events(scrape_hash) WHERE scrape_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_external_id ON events(source, external_id) WHERE external_id IS NOT NULL;

-- Indexes for venues table
CREATE INDEX IF NOT EXISTS idx_venues_city ON venues(city);
CREATE INDEX IF NOT EXISTS idx_venues_coordinates ON venues(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_venues_name ON venues(name);

-- Indexes for categories table
CREATE INDEX IF NOT EXISTS idx_categories_slug ON event_categories(slug);

-- Insert sample event categories
INSERT INTO event_categories (name, slug, description, color, icon) VALUES
('Music', 'music', 'Concerts, festivals, and musical performances', '#E11D48', 'music'),
('Technology', 'technology', 'Tech conferences, workshops, and meetups', '#3B82F6', 'laptop'),
('Culture', 'culture', 'Cultural events, exhibitions, and traditional performances', '#7C3AED', 'palette'),
('Food & Drink', 'food-drink', 'Food festivals, wine tastings, and culinary events', '#F59E0B', 'utensils'),
('Sports', 'sports', 'Sporting events, tournaments, and activities', '#10B981', 'trophy'),
('Arts', 'arts', 'Art galleries, exhibitions, and creative workshops', '#EC4899', 'brush'),
('Entertainment', 'entertainment', 'Movies, theater, comedy shows, and general entertainment', '#8B5CF6', 'theater'),
('Festival', 'festival', 'Large-scale festivals and celebrations', '#F97316', 'calendar'),
('Business', 'business', 'Networking events, business conferences, and seminars', '#6B7280', 'briefcase'),
('Education', 'education', 'Workshops, courses, and educational events', '#14B8A6', 'book')
ON CONFLICT (slug) DO NOTHING;

-- Insert sample venues across Croatia
INSERT INTO venues (name, address, city, latitude, longitude, capacity, venue_type, website) VALUES
('Dom Sportova', 'Trg Krešimira Ćosića 11', 'Zagreb', 45.8150, 15.9819, 5500, 'arena', 'https://www.dom-sportova.hr'),
('Arena Zagreb', 'Lanište 1A', 'Zagreb', 45.8003, 15.9375, 15500, 'arena', 'https://www.arena-zagreb.hr'),
('Vatroslav Lisinski Concert Hall', 'Trg Stjepana Radića 4', 'Zagreb', 45.8144, 15.9686, 1841, 'theater', 'https://www.lisinski.hr'),
('Spaladium Arena', 'Zrinsko Frankopanska 211', 'Split', 43.5081, 16.4619, 10000, 'arena', 'https://www.spaladium-arena.hr'),
('Riva Promenade', 'Obala Hrvatskog narodnog preporoda', 'Split', 43.5081, 16.4402, 50000, 'outdoor', NULL),
('Dubrovnik Summer Festival Venues', 'Placa Stradun', 'Dubrovnik', 42.6414, 18.1111, 2000, 'outdoor', 'https://www.dubrovnik-festival.hr'),
('Pula Arena', 'Flavijevska ul.', 'Pula', 44.8737, 13.8493, 5000, 'arena', 'https://www.pulainfo.hr'),
('Zadar Sea Organ', 'Obala kralja Petra Krešimira IV', 'Zadar', 44.1194, 15.2314, 1000, 'outdoor', NULL),
('HNK Rijeka', 'Uljarska 1', 'Rijeka', 45.3271, 14.4422, 800, 'theater', 'https://www.hnk-rijeka.hr'),
('Gradska Vijećnica Osijek', 'Europska avenija 24', 'Osijek', 45.5550, 18.6955, 500, 'theater', NULL),
('Rovinj Heritage Museum', 'Trg Maršala Tita 11', 'Rovinj', 45.0815, 13.6387, 300, 'museum', NULL),
('Karlovac City Square', 'Trg Josipa Jurja Strossmayera', 'Karlovac', 45.4870, 15.5478, 2000, 'outdoor', NULL),
('Hvar Lavender Fields', 'Velo Grablje', 'Hvar', 43.1729, 16.6413, 1000, 'outdoor', NULL),
('Šibenik Cathedral Square', 'Trg Republike Hrvatske', 'Šibenik', 43.7350, 15.8952, 1500, 'outdoor', NULL),
('Makarska Riviera Beach', 'Obala kralja Tomislava', 'Makarska', 43.2971, 17.0175, 10000, 'outdoor', NULL)
ON CONFLICT (name, city) DO NOTHING;

-- Insert sample Croatian events data with enhanced schema
INSERT INTO events (name, time, date, location, description, price, image, link, category_id, venue_id, source, latitude, longitude, organizer, tags, slug, is_featured) VALUES
('Zagreb Music Festival', '20:00', '2025-06-15', 'Zagreb', 'Annual music festival featuring Croatian and international artists in the heart of Zagreb', '150 HRK', 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=400', 'https://example.com/zagreb-music', 1, 2, 'manual', 45.8003, 15.9375, 'Zagreb Events Ltd.', ARRAY['music', 'festival', 'international'], 'zagreb-music-festival-2025', true),
('Split Summer Concert', '19:30', '2025-06-20', 'Split', 'Open-air concert by the beautiful Adriatic Sea with stunning sunset views', '100 HRK', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400', 'https://example.com/split-concert', 1, 5, 'manual', 43.5081, 16.4402, 'Split Tourism Board', ARRAY['music', 'outdoor', 'sunset'], 'split-summer-concert-2025', false),
('Dubrovnik Cultural Evening', '18:00', '2025-06-25', 'Dubrovnik', 'Traditional Croatian cultural performance in the historic Old Town walls', '80 HRK', 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=400', 'https://example.com/dubrovnik-culture', 3, 6, 'manual', 42.6414, 18.1111, 'Dubrovnik Summer Festival', ARRAY['culture', 'traditional', 'heritage'], 'dubrovnik-cultural-evening-2025', true),
('Rijeka Tech Conference', '09:00', '2025-06-18', 'Rijeka', 'Technology conference with leading Croatian and European tech speakers', '200 HRK', 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400', 'https://example.com/rijeka-tech', 2, 9, 'manual', 45.3271, 14.4422, 'Croatian Tech Association', ARRAY['technology', 'conference', 'networking'], 'rijeka-tech-conference-2025', false),
('Zadar Sunset Festival', '17:00', '2025-06-22', 'Zadar', 'Sunset music festival featuring electronic and ambient music by the sea organ', '120 HRK', 'https://images.unsplash.com/photo-1520637836862-4d197d17c0a4?w=400', 'https://example.com/zadar-sunset', 1, 8, 'manual', 44.1194, 15.2314, 'Zadar Cultural Center', ARRAY['music', 'electronic', 'sunset', 'sea-organ'], 'zadar-sunset-festival-2025', true),
('Pula Film Screening', '21:00', '2025-06-16', 'Pula', 'Outdoor cinema screening in the famous Roman amphitheater Arena', '60 HRK', 'https://images.unsplash.com/photo-1489599142025-4c2ac1e9de39?w=400', 'https://example.com/pula-cinema', 7, 7, 'manual', 44.8737, 13.8493, 'Pula Film Festival', ARRAY['film', 'cinema', 'historical'], 'pula-film-screening-2025', false),
('Makarska Beach Party', '22:00', '2025-06-19', 'Makarska', 'Summer beach party with international DJs and cocktails on the riviera', 'Free', 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400', 'https://example.com/makarska-beach', 7, 15, 'manual', 43.2971, 17.0175, 'Makarska Events', ARRAY['party', 'beach', 'dj', 'summer'], 'makarska-beach-party-2025', false),
('Osijek Food Festival', '12:00', '2025-06-21', 'Osijek', 'Traditional Slavonian cuisine festival with local specialties and wine', '50 HRK', 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400', 'https://example.com/osijek-food', 4, 10, 'manual', 45.5550, 18.6955, 'Osijek Gastronomy Association', ARRAY['food', 'wine', 'traditional', 'slavonian'], 'osijek-food-festival-2025', false),
('Rovinj Art Gallery Opening', '19:00', '2025-06-17', 'Rovinj', 'Contemporary Croatian art exhibition opening in the beautiful Istrian town', 'Free', 'https://images.unsplash.com/photo-1578321272176-b7bbc0679853?w=400', 'https://example.com/rovinj-art', 6, 11, 'manual', 45.0815, 13.6387, 'Rovinj Art Society', ARRAY['art', 'exhibition', 'contemporary'], 'rovinj-art-gallery-opening-2025', false),
('Karlovac Beer Festival', '16:00', '2025-06-23', 'Karlovac', 'Annual beer festival featuring Croatian craft breweries and live music', '80 HRK', 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400', 'https://example.com/karlovac-beer', 4, 12, 'manual', 45.4870, 15.5478, 'Karlovac Brewery Association', ARRAY['beer', 'craft', 'music', 'festival'], 'karlovac-beer-festival-2025', false),
('Hvar Lavender Festival', '10:00', '2025-06-24', 'Hvar', 'Celebration of lavender harvest with traditional music and local products', '40 HRK', 'https://images.unsplash.com/photo-1464207687429-7505649dae38?w=400', 'https://example.com/hvar-lavender', 8, 13, 'manual', 43.1729, 16.6413, 'Hvar Lavender Producers', ARRAY['lavender', 'harvest', 'traditional', 'nature'], 'hvar-lavender-festival-2025', false),
('Šibenik Medieval Fair', '11:00', '2025-06-26', 'Šibenik', 'Medieval fair in the historic center with craftsmen and traditional performances', '30 HRK', 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400', 'https://example.com/sibenik-medieval', 3, 14, 'manual', 43.7350, 15.8952, 'Šibenik Historical Society', ARRAY['medieval', 'crafts', 'historical', 'performance'], 'sibenik-medieval-fair-2025', false);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a function to update the search vector for full-text search
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.name, '') || ' ' ||
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.location, '') || ' ' ||
        COALESCE(NEW.organizer, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_events_updated_at 
    BEFORE UPDATE ON events 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger to automatically update search vector
CREATE TRIGGER update_events_search_vector 
    BEFORE INSERT OR UPDATE ON events 
    FOR EACH ROW 
    EXECUTE FUNCTION update_search_vector();

-- Create trigger to automatically update venues updated_at
CREATE TRIGGER update_venues_updated_at 
    BEFORE UPDATE ON venues 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();