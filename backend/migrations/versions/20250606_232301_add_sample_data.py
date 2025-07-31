"""Add sample data for categories, venues, and events

Revision ID: 20250606_232301
Revises: 20250606_232129
Create Date: 2025-06-06T23:23:01.408626

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250606_232301'
down_revision = '20250606_232129'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert sample event categories
    op.execute("""
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
    """)
    
    # Insert sample venues across Croatia
    op.execute("""
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
    """)
    
    # Insert sample Croatian events data with enhanced schema
    op.execute("""
        INSERT INTO events (title, time, date, location, description, price, image, link, category_id, venue_id, source, latitude, longitude, organizer, tags, slug, is_featured) VALUES
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
    """)


def downgrade() -> None:
    # Remove sample data in reverse order due to foreign key constraints
    op.execute("DELETE FROM events WHERE source = 'manual' AND organizer IN ('Zagreb Events Ltd.', 'Split Tourism Board', 'Dubrovnik Summer Festival', 'Croatian Tech Association', 'Zadar Cultural Center', 'Pula Film Festival', 'Makarska Events', 'Osijek Gastronomy Association', 'Rovinj Art Society', 'Karlovac Brewery Association', 'Hvar Lavender Producers', 'Šibenik Historical Society')")
    op.execute("DELETE FROM venues WHERE city IN ('Zagreb', 'Split', 'Dubrovnik', 'Pula', 'Zadar', 'Rijeka', 'Osijek', 'Rovinj', 'Karlovac', 'Hvar', 'Šibenik', 'Makarska')")
    op.execute("DELETE FROM event_categories WHERE slug IN ('music', 'technology', 'culture', 'food-drink', 'sports', 'arts', 'entertainment', 'festival', 'business', 'education')")
