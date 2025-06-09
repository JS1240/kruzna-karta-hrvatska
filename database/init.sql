-- Database initialization for Diidemo.hr
-- Create the events table

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    time VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    location VARCHAR(255) NOT NULL,
    description TEXT,
    price VARCHAR(50),
    image VARCHAR(500),
    link VARCHAR(500),
    search_vector tsvector,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
CREATE INDEX IF NOT EXISTS idx_events_location ON events(location);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
CREATE INDEX IF NOT EXISTS idx_events_search ON events USING GIN(search_vector);
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
    ON events FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(search_vector, 'pg_catalog.simple', name, description);

-- Insert sample Croatian events data
INSERT INTO events (name, time, date, location, description, price, image, link) VALUES
('Zagreb Music Festival', '20:00', '2025-06-15', 'Zagreb', 'Annual music festival featuring Croatian and international artists in the heart of Zagreb', '150 HRK', 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=400', 'https://example.com/zagreb-music'),
('Split Summer Concert', '19:30', '2025-06-20', 'Split', 'Open-air concert by the beautiful Adriatic Sea with stunning sunset views', '100 HRK', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400', 'https://example.com/split-concert'),
('Dubrovnik Cultural Evening', '18:00', '2025-06-25', 'Dubrovnik', 'Traditional Croatian cultural performance in the historic Old Town walls', '80 HRK', 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=400', 'https://example.com/dubrovnik-culture'),
('Rijeka Tech Conference', '09:00', '2025-06-18', 'Rijeka', 'Technology conference with leading Croatian and European tech speakers', '200 HRK', 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400', 'https://example.com/rijeka-tech'),
('Zadar Sunset Festival', '17:00', '2025-06-22', 'Zadar', 'Sunset music festival featuring electronic and ambient music by the sea organ', '120 HRK', 'https://images.unsplash.com/photo-1520637836862-4d197d17c0a4?w=400', 'https://example.com/zadar-sunset'),
('Pula Film Screening', '21:00', '2025-06-16', 'Pula', 'Outdoor cinema screening in the famous Roman amphitheater Arena', '60 HRK', 'https://images.unsplash.com/photo-1489599142025-4c2ac1e9de39?w=400', 'https://example.com/pula-cinema'),
('Makarska Beach Party', '22:00', '2025-06-19', 'Makarska', 'Summer beach party with international DJs and cocktails on the riviera', 'Free', 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400', 'https://example.com/makarska-beach'),
('Osijek Food Festival', '12:00', '2025-06-21', 'Osijek', 'Traditional Slavonian cuisine festival with local specialties and wine', '50 HRK', 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400', 'https://example.com/osijek-food'),
('Rovinj Art Gallery Opening', '19:00', '2025-06-17', 'Rovinj', 'Contemporary Croatian art exhibition opening in the beautiful Istrian town', 'Free', 'https://images.unsplash.com/photo-1578321272176-b7bbc0679853?w=400', 'https://example.com/rovinj-art'),
('Karlovac Beer Festival', '16:00', '2025-06-23', 'Karlovac', 'Annual beer festival featuring Croatian craft breweries and live music', '80 HRK', 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400', 'https://example.com/karlovac-beer'),
('Hvar Lavender Festival', '10:00', '2025-06-24', 'Hvar', 'Celebration of lavender harvest with traditional music and local products', '40 HRK', 'https://images.unsplash.com/photo-1464207687429-7505649dae38?w=400', 'https://example.com/hvar-lavender'),
('Šibenik Medieval Fair', '11:00', '2025-06-26', 'Šibenik', 'Medieval fair in the historic center with craftsmen and traditional performances', '30 HRK', 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400', 'https://example.com/sibenik-medieval');

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_events_updated_at 
    BEFORE UPDATE ON events 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();