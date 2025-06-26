// Geocoding utilities for converting location names to coordinates
import { logger } from "./logger";

export interface Coordinates {
  lat: number;
  lng: number;
}

// Croatian venues and their specific coordinates
const CROATIAN_VENUE_COORDINATES: Record<string, Coordinates> = {
  // Major event venues and stadiums
  "poljud stadium": { lat: 43.5133, lng: 16.4439 }, // Split
  "stadion poljud": { lat: 43.5133, lng: 16.4439 }, // Split
  "arena pula": { lat: 44.8737, lng: 13.8467 }, // Pula
  "pula arena": { lat: 44.8737, lng: 13.8467 }, // Pula
  "amfiteatar pula": { lat: 44.8737, lng: 13.8467 }, // Pula
  "malo rimsko kazalište pula": { lat: 44.8688, lng: 13.8467 }, // Pula
  "small roman theatre pula": { lat: 44.8688, lng: 13.8467 }, // Pula
  
  // Zagreb venues
  "dom sportova": { lat: 45.7967, lng: 15.9697 }, // Zagreb
  "arena zagreb": { lat: 45.7967, lng: 15.9697 }, // Zagreb
  "maksimir stadium": { lat: 45.8219, lng: 16.0119 }, // Zagreb
  "stadion maksimir": { lat: 45.8219, lng: 16.0119 }, // Zagreb
  "hnk zagreb": { lat: 45.8081, lng: 15.9678 }, // Zagreb
  "croatian national theatre": { lat: 45.8081, lng: 15.9678 }, // Zagreb
  "hrvatsko narodno kazalište": { lat: 45.8081, lng: 15.9678 }, // Zagreb
  "tvornica kulture": { lat: 45.8003, lng: 15.9897 }, // Zagreb
  "jarun lake": { lat: 45.7833, lng: 15.9167 }, // Zagreb
  "jezero jarun": { lat: 45.7833, lng: 15.9167 }, // Zagreb
  
  // Split venues
  "diocletian's palace": { lat: 43.5082, lng: 16.4404 }, // Split
  "dioklecijanova palača": { lat: 43.5082, lng: 16.4404 }, // Split
  "riva split": { lat: 43.5081, lng: 16.4401 }, // Split
  "bacvice beach": { lat: 43.5048, lng: 16.4531 }, // Split
  "plaža bačvice": { lat: 43.5048, lng: 16.4531 }, // Split
  
  // VisitSplit specific venues
  "trg peristil": { lat: 43.5082, lng: 16.4406 }, // Split - Peristyle Square
  "peristil": { lat: 43.5082, lng: 16.4406 }, // Split - Peristyle Square
  "peristyle": { lat: 43.5082, lng: 16.4406 }, // Split - Peristyle Square
  "stara gradska vijećnica": { lat: 43.5085, lng: 16.4398 }, // Split - Old City Hall
  "old city hall split": { lat: 43.5085, lng: 16.4398 }, // Split - Old City Hall
  "bedem cornaro": { lat: 43.5095, lng: 16.4385 }, // Split - Cornaro Bastion
  "cornaro bastion": { lat: 43.5095, lng: 16.4385 }, // Split - Cornaro Bastion
  "pjaca": { lat: 43.5081, lng: 16.4401 }, // Split - People's Square (Pjaca)
  "narodni trg": { lat: 43.5081, lng: 16.4401 }, // Split - People's Square
  "vestibul": { lat: 43.5083, lng: 16.4405 }, // Split - Vestibule
  "zlatna vrata": { lat: 43.5088, lng: 16.4405 }, // Split - Golden Gate
  "golden gate": { lat: 43.5088, lng: 16.4405 }, // Split - Golden Gate
  "srebrna vrata": { lat: 43.5080, lng: 16.4395 }, // Split - Silver Gate
  "silver gate": { lat: 43.5080, lng: 16.4395 }, // Split - Silver Gate
  "željezna vrata": { lat: 43.5075, lng: 16.4403 }, // Split - Iron Gate
  "iron gate": { lat: 43.5075, lng: 16.4403 }, // Split - Iron Gate
  "meštrović galerija": { lat: 43.5119, lng: 16.4356 }, // Split - Meštrović Gallery
  "mestrovic gallery": { lat: 43.5119, lng: 16.4356 }, // Split - Meštrović Gallery
  "marjan": { lat: 43.5157, lng: 16.4264 }, // Split - Marjan Hill
  "marjan hill": { lat: 43.5157, lng: 16.4264 }, // Split - Marjan Hill
  "stinice": { lat: 43.5025, lng: 16.4180 }, // Split - Stinice area
  "stinice industrijska zona": { lat: 43.5025, lng: 16.4180 }, // Split - Stinice industrial zone
  "hrvatski dom split": { lat: 43.5095, lng: 16.4412 }, // Split - Croatian Home
  "croatian home split": { lat: 43.5095, lng: 16.4412 }, // Split - Croatian Home
  "koncertna dvorana ive tijardovića": { lat: 43.5095, lng: 16.4412 }, // Split - Ivo Tijardović Concert Hall
  "ivo tijardovic concert hall": { lat: 43.5095, lng: 16.4412 }, // Split - Ivo Tijardović Concert Hall
  "culture hub croatia": { lat: 43.5089, lng: 16.4389 }, // Split - Culture HUB Croatia
  "plančićeva": { lat: 43.5089, lng: 16.4389 }, // Split - Plančićeva street area
  "tončićeva": { lat: 43.5095, lng: 16.4412 }, // Split - Tončićeva street area
  
  // Dubrovnik venues
  "lovrijenac fortress": { lat: 42.6414, lng: 18.1064 }, // Dubrovnik
  "tvrđava lovrijenac": { lat: 42.6414, lng: 18.1064 }, // Dubrovnik
  "rector's palace": { lat: 42.6414, lng: 18.1108 }, // Dubrovnik
  "knežev dvor": { lat: 42.6414, lng: 18.1108 }, // Dubrovnik
  
  // Pula venues
  "kastel pula": { lat: 44.8675, lng: 13.8481 }, // Pula
  "pula castle": { lat: 44.8675, lng: 13.8481 }, // Pula
  "fort bourguignon": { lat: 44.8644, lng: 13.8514 }, // Pula
  
  // Rijeka venues
  "hnk ivan zajc": { lat: 45.3294, lng: 14.4422 }, // Rijeka
  "croatian national theatre rijeka": { lat: 45.3294, lng: 14.4422 }, // Rijeka
  "rijeka city stadium": { lat: 45.3439, lng: 14.4058 }, // Rijeka
  "stadion rujevica": { lat: 45.3439, lng: 14.4058 }, // Rijeka
  
  // Zadar venues
  "zadar city galleria": { lat: 44.1194, lng: 15.2314 }, // Zadar
  "forum zadar": { lat: 44.1167, lng: 15.2289 }, // Zadar
  
  // Osijek venues
  "gradski vrt": { lat: 45.5597, lng: 18.6972 }, // Osijek
  "city garden osijek": { lat: 45.5597, lng: 18.6972 }, // Osijek
  "hnk osijek": { lat: 45.5550, lng: 18.6955 }, // Osijek
  
  // Opatija venues
  "amadria park hotel royal": { lat: 45.3378, lng: 14.3088 }, // Opatija
  "villa angiolina": { lat: 45.3352, lng: 14.3092 }, // Opatija
  "park angiolina": { lat: 45.3352, lng: 14.3092 }, // Opatija
  "hotel milenij": { lat: 45.3411, lng: 14.3047 }, // Opatija
  
  // Makarska venues
  "ljetno kino makarska": { lat: 43.2969, lng: 17.0178 }, // Makarska
  "summer cinema makarska": { lat: 43.2969, lng: 17.0178 }, // Makarska
  
  // Hvar venues
  "hvar town square": { lat: 43.1729, lng: 16.4414 }, // Hvar
  "trg svetog stjepana": { lat: 43.1729, lng: 16.4414 }, // Hvar
  
  // Sinj venues
  "hipodrom sinj": { lat: 43.7036, lng: 16.6422 }, // Sinj
  "sinj hippodrome": { lat: 43.7036, lng: 16.6422 }, // Sinj
  
  // Music venues and clubs
  "aquarius zagreb": { lat: 45.7833, lng: 15.9167 }, // Zagreb - Jarun
  "the garden brewery": { lat: 45.8156, lng: 15.9678 }, // Zagreb
  "vintage industrial bar": { lat: 45.8056, lng: 15.9625 }, // Zagreb
  "club culture bar": { lat: 43.5081, lng: 16.4401 }, // Split
  "central club": { lat: 43.5081, lng: 16.4401 }, // Split
  "carpe diem beach": { lat: 43.1729, lng: 16.4414 }, // Hvar
  
  // Universities and conference centers
  "university of zagreb": { lat: 45.8150, lng: 15.9819 }, // Zagreb
  "sveučilište u zagrebu": { lat: 45.8150, lng: 15.9819 }, // Zagreb
  "university of split": { lat: 43.5081, lng: 16.4401 }, // Split
  "sveučilište u splitu": { lat: 43.5081, lng: 16.4401 }, // Split
  "zagreb convention centre": { lat: 45.7889, lng: 15.9758 }, // Zagreb
  "zagrebački velesajam": { lat: 45.7889, lng: 15.9758 }, // Zagreb
};

// Croatian cities and their approximate coordinates
const CROATIAN_CITY_COORDINATES: Record<string, Coordinates> = {
  // Major cities
  zagreb: { lat: 45.815, lng: 15.9819 },
  split: { lat: 43.5081, lng: 16.4401 },
  rijeka: { lat: 45.3271, lng: 14.4426 },
  osijek: { lat: 45.555, lng: 18.6955 },
  zadar: { lat: 44.1194, lng: 15.2314 },
  pula: { lat: 44.8666, lng: 13.8496 },
  dubrovnik: { lat: 42.6507, lng: 18.0944 },
  sisak: { lat: 45.4658, lng: 16.3799 },
  "slavonski brod": { lat: 45.16, lng: 18.0158 },
  karlovac: { lat: 45.487, lng: 15.5477 },

  // Coastal cities
  rovinj: { lat: 45.0804, lng: 13.6386 },
  poreč: { lat: 45.2269, lng: 13.5956 },
  umag: { lat: 45.4328, lng: 13.5202 },
  opatija: { lat: 45.3382, lng: 14.3053 },
  crikvenica: { lat: 45.1789, lng: 14.6914 },
  krk: { lat: 45.0267, lng: 14.5736 },
  makarska: { lat: 43.2969, lng: 17.0178 },
  trogir: { lat: 43.515, lng: 16.2515 },
  omiš: { lat: 43.4447, lng: 16.6882 },
  hvar: { lat: 43.1729, lng: 16.4414 },
  korčula: { lat: 42.9603, lng: 17.135 },
  biograd: { lat: 44.0119, lng: 15.4497 },
  pag: { lat: 44.4397, lng: 15.0586 },
  nin: { lat: 44.2408, lng: 15.1761 },
  novalja: { lat: 44.5586, lng: 14.8856 },

  // Inland cities
  "velika gorica": { lat: 45.7125, lng: 16.0756 },
  samobor: { lat: 45.8028, lng: 15.7178 },
  zaprešić: { lat: 45.8563, lng: 15.8081 },
  metković: { lat: 43.0536, lng: 17.6486 },
  ploče: { lat: 43.0578, lng: 17.4317 },
  gospić: { lat: 44.5467, lng: 15.3744 },
  senj: { lat: 44.9897, lng: 14.9064 },
  otočac: { lat: 44.8703, lng: 15.2381 },

  // Counties and regions (approximate centers)
  istria: { lat: 45.1364, lng: 13.9361 },
  dalmatia: { lat: 43.5, lng: 16.5 },
  slavonia: { lat: 45.4, lng: 18.0 },
  lika: { lat: 44.7, lng: 15.6 },
  zagorje: { lat: 46.0, lng: 15.8 },
  međimurje: { lat: 46.4, lng: 16.4 },

  // Default fallback
  croatia: { lat: 45.1, lng: 15.2 },
  hrvatska: { lat: 45.1, lng: 15.2 },
};

// County centers
const COUNTY_COORDINATES: Record<string, Coordinates> = {
  "split-dalmatia": { lat: 43.5081, lng: 16.4401 },
  zagreb: { lat: 45.815, lng: 15.9819 },
  "dubrovnik-neretva": { lat: 42.6507, lng: 18.0944 },
  "primorje-gorski kotar": { lat: 45.3271, lng: 14.4426 },
  zadar: { lat: 44.1194, lng: 15.2314 },
  istria: { lat: 44.8666, lng: 13.8496 },
  "lika-senj": { lat: 44.5586, lng: 14.8856 },
};

/**
 * Extract city name from location string
 */
function extractCityName(location: string): string {
  if (!location) return "";

  const normalizedLocation = location.toLowerCase().trim();

  // Handle specific patterns for Split
  if (normalizedLocation.includes('split') || 
      normalizedLocation.startsWith('split') ||
      normalizedLocation === 'split 3') {
    return "split";
  }

  // Handle "Location, Croatia" patterns
  if (normalizedLocation.includes(', croatia')) {
    const cityPart = normalizedLocation.split(', croatia')[0].trim();
    return cityPart;
  }

  // Common patterns to extract city names
  const patterns = [
    /^([^,]+),/, // "City, Something" -> "City"
    /,\s*([^,]+)$/, // "Something, City" -> "City"
    /^([^-]+)-/, // "City-Something" -> "City"
    /([a-zA-ZšđčćžŠĐČĆŽ\s]+)/, // Any Croatian city name
  ];

  for (const pattern of patterns) {
    const match = location.match(pattern);
    if (match && match[1]) {
      return match[1].trim().toLowerCase();
    }
  }

  return location.toLowerCase().trim();
}

/**
 * Get coordinates for a location string (legacy sync version)
 */
export function getCoordinatesForLocation(
  location: string,
): Coordinates | null {
  if (!location) return null;

  const normalizedLocation = location.toLowerCase().trim();

  // First check for specific venues (most precise)
  if (CROATIAN_VENUE_COORDINATES[normalizedLocation]) {
    return CROATIAN_VENUE_COORDINATES[normalizedLocation];
  }

  // Check for partial venue matches
  for (const [venueName, coords] of Object.entries(CROATIAN_VENUE_COORDINATES)) {
    if (normalizedLocation.includes(venueName) || venueName.includes(normalizedLocation)) {
      return coords;
    }
  }

  // Then check for direct city match
  if (CROATIAN_CITY_COORDINATES[normalizedLocation]) {
    return CROATIAN_CITY_COORDINATES[normalizedLocation];
  }

  // Extract city name and try again
  const cityName = extractCityName(location);
  if (cityName && CROATIAN_CITY_COORDINATES[cityName]) {
    return CROATIAN_CITY_COORDINATES[cityName];
  }

  // Try county match
  for (const [county, coords] of Object.entries(COUNTY_COORDINATES)) {
    if (
      normalizedLocation.includes(county) ||
      normalizedLocation.includes(county.replace("-", " "))
    ) {
      return coords;
    }
  }

  // Fuzzy matching for common variations
  const fuzzyMatches: Record<string, string> = {
    spalato: "split",
    ragusa: "dubrovnik",
    fiume: "rijeka",
    pola: "pula",
    zara: "zadar",
  };

  for (const [variation, canonical] of Object.entries(fuzzyMatches)) {
    if (normalizedLocation.includes(variation)) {
      return CROATIAN_CITY_COORDINATES[canonical];
    }
  }

  logger.warn(`Could not find coordinates for location: ${location}`);
  return null;
}

/**
 * Enhanced async geocoding with real-time fallbacks
 */
export async function getCoordinatesForLocationAsync(
  location: string,
  context?: string,
): Promise<GeocodeResult | null> {
  return await advancedGeocode(location, context);
}

/**
 * Venue clustering and smart positioning for multiple events
 */
interface VenueCluster {
  baseCoordinates: Coordinates;
  events: Array<{id: string; title: string; date: string}>;
  radius: number;
  positions: Coordinates[];
}

/**
 * Calculate distance between two coordinates in kilometers
 */
function calculateDistance(coord1: Coordinates, coord2: Coordinates): number {
  const R = 6371; // Earth's radius in km
  const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
  const dLng = (coord2.lng - coord1.lng) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) *
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

/**
 * Create venue clusters for events at the same or nearby locations
 */
export function createVenueClusters(
  events: Array<{id: string; title: string; date: string; coordinates: Coordinates}>,
  maxClusterDistance: number = 0.1, // 100 meters
): VenueCluster[] {
  const clusters: VenueCluster[] = [];
  const processedEvents = new Set<string>();

  for (const event of events) {
    if (processedEvents.has(event.id)) continue;

    // Find nearby events
    const nearbyEvents = events.filter(otherEvent => {
      if (otherEvent.id === event.id || processedEvents.has(otherEvent.id)) {
        return false;
      }
      const distance = calculateDistance(event.coordinates, otherEvent.coordinates);
      return distance <= maxClusterDistance;
    });

    // Create cluster
    const clusterEvents = [event, ...nearbyEvents];
    const cluster: VenueCluster = {
      baseCoordinates: event.coordinates,
      events: clusterEvents.map(e => ({id: e.id, title: e.title, date: e.date})),
      radius: Math.min(0.005 + (clusterEvents.length - 1) * 0.002, 0.02), // Dynamic radius
      positions: [],
    };

    // Generate optimal positions for events in cluster
    cluster.positions = generateClusterPositions(
      event.coordinates,
      clusterEvents.length,
      cluster.radius
    );

    clusters.push(cluster);

    // Mark events as processed
    clusterEvents.forEach(e => processedEvents.add(e.id));
  }

  return clusters;
}

/**
 * Generate optimal positions for events in a cluster
 */
function generateClusterPositions(
  center: Coordinates,
  count: number,
  radius: number,
): Coordinates[] {
  if (count === 1) {
    return [center];
  }

  const positions: Coordinates[] = [];
  
  if (count === 2) {
    // Simple offset for 2 events
    positions.push(
      { lat: center.lat + radius/2, lng: center.lng - radius/2 },
      { lat: center.lat - radius/2, lng: center.lng + radius/2 }
    );
  } else {
    // Circular arrangement for 3+ events
    for (let i = 0; i < count; i++) {
      const angle = (i * 2 * Math.PI) / count;
      positions.push({
        lat: center.lat + radius * Math.cos(angle),
        lng: center.lng + radius * Math.sin(angle),
      });
    }
  }

  return positions;
}

/**
 * Add smart jitter to coordinates to avoid overlapping markers
 */
export function addCoordinateJitter(
  coords: Coordinates,
  index: number = 0,
): Coordinates {
  const jitterAmount = 0.005; // Reduced jitter for better clustering
  const angle = (index * 45) % 360; // Spread markers in a circle
  const jitterLat = Math.cos((angle * Math.PI) / 180) * jitterAmount;
  const jitterLng = Math.sin((angle * Math.PI) / 180) * jitterAmount;

  return {
    lat: coords.lat + jitterLat,
    lng: coords.lng + jitterLng,
  };
}

/**
 * Intelligent coordinate positioning with clustering
 */
export function getOptimalEventPositions(
  events: Array<{id: string; title: string; date: string; location: string}>,
): Map<string, {coordinates: Coordinates; clusterId?: string; accuracy: string}> {
  const eventCoordinates = new Map<string, {coordinates: Coordinates; clusterId?: string; accuracy: string}>();
  const eventsWithCoords: Array<{id: string; title: string; date: string; coordinates: Coordinates}> = [];

  // First pass: get coordinates for all events
  for (const event of events) {
    const coords = getCoordinatesForLocation(event.location);
    if (coords) {
      eventsWithCoords.push({
        id: event.id,
        title: event.title,
        date: event.date,
        coordinates: coords,
      });
    }
  }

  // Create clusters for nearby events
  const clusters = createVenueClusters(eventsWithCoords);

  // Assign optimized positions
  for (const cluster of clusters) {
    cluster.events.forEach((event, index) => {
      const position = cluster.positions[index] || cluster.baseCoordinates;
      eventCoordinates.set(event.id, {
        coordinates: position,
        clusterId: clusters.length > 1 ? `cluster-${clusters.indexOf(cluster)}` : undefined,
        accuracy: cluster.events.length > 1 ? 'clustered' : 'precise',
      });
    });
  }

  return eventCoordinates;
}

/**
 * Enhanced coordinate validation and accuracy scoring
 */
interface GeocodeResult extends Coordinates {
  accuracy: 'venue' | 'address' | 'neighborhood' | 'city' | 'region';
  confidence: number;
  source: 'database' | 'mapbox' | 'fallback';
  place_name?: string;
}

/**
 * Croatian geographic bounds for validation
 */
const CROATIA_BOUNDS = {
  north: 46.55,  // Northernmost point
  south: 42.38,  // Southernmost point  
  east: 19.43,   // Easternmost point
  west: 13.50,   // Westernmost point
};

/**
 * Validate if coordinates are within Croatian bounds
 */
function isWithinCroatiaBounds(coords: Coordinates): boolean {
  return coords.lat >= CROATIA_BOUNDS.south &&
         coords.lat <= CROATIA_BOUNDS.north &&
         coords.lng >= CROATIA_BOUNDS.west &&
         coords.lng <= CROATIA_BOUNDS.east;
}

/**
 * Enhanced Mapbox Geocoding API with accuracy scoring
 */
export async function geocodeLocation(
  location: string,
): Promise<GeocodeResult | null> {
  const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
  if (!mapboxToken) {
    logger.warn("Mapbox token not available for geocoding");
    return null;
  }

  try {
    // Clean and prepare query
    const cleanLocation = location.trim();
    const query = encodeURIComponent(`${cleanLocation}, Croatia`);
    
    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${query}.json?` +
      `access_token=${mapboxToken}&country=hr&limit=3&types=poi,address,place`,
    );

    if (!response.ok) {
      throw new Error(`Geocoding failed: ${response.status}`);
    }

    const data = await response.json();

    if (data.features && data.features.length > 0) {
      // Get the best result
      const feature = data.features[0];
      const [lng, lat] = feature.center;
      
      // Validate coordinates are in Croatia
      const coords = { lat, lng };
      if (!isWithinCroatiaBounds(coords)) {
        logger.warn(`Coordinates outside Croatia bounds: ${lat}, ${lng} for ${location}`);
        return null;
      }

      // Determine accuracy based on place type
      const placeTypes = feature.place_type || [];
      let accuracy: GeocodeResult['accuracy'] = 'city';
      let confidence = 0.5;

      if (placeTypes.includes('poi')) {
        accuracy = 'venue';
        confidence = 0.9;
      } else if (placeTypes.includes('address')) {
        accuracy = 'address';
        confidence = 0.8;
      } else if (placeTypes.includes('neighborhood')) {
        accuracy = 'neighborhood';
        confidence = 0.6;
      } else if (placeTypes.includes('place')) {
        accuracy = 'city';
        confidence = 0.5;
      }

      // Boost confidence for well-known Croatian venues
      const placeName = feature.place_name?.toLowerCase() || '';
      if (placeName.includes('stadium') || placeName.includes('arena') || 
          placeName.includes('theatre') || placeName.includes('hotel')) {
        confidence = Math.min(confidence + 0.1, 1.0);
      }

      return {
        lat,
        lng,
        accuracy,
        confidence,
        source: 'mapbox',
        place_name: feature.place_name,
      };
    }

    return null;
  } catch (error) {
    logger.error("Geocoding error:", error);
    return null;
  }
}

/**
 * Advanced geocoding with multiple fallback strategies
 */
export async function advancedGeocode(
  location: string,
  context?: string,
): Promise<GeocodeResult | null> {
  if (!location) return null;

  const normalizedLocation = location.toLowerCase().trim();

  // 1. Try venue database first (highest accuracy)
  if (CROATIAN_VENUE_COORDINATES[normalizedLocation]) {
    const coords = CROATIAN_VENUE_COORDINATES[normalizedLocation];
    return {
      ...coords,
      accuracy: 'venue',
      confidence: 0.95,
      source: 'database',
    };
  }

  // 2. Try partial venue matches
  for (const [venueName, coords] of Object.entries(CROATIAN_VENUE_COORDINATES)) {
    if (normalizedLocation.includes(venueName) || venueName.includes(normalizedLocation)) {
      return {
        ...coords,
        accuracy: 'venue',
        confidence: 0.85,
        source: 'database',
      };
    }
  }

  // 3. Try city database
  if (CROATIAN_CITY_COORDINATES[normalizedLocation]) {
    const coords = CROATIAN_CITY_COORDINATES[normalizedLocation];
    return {
      ...coords,
      accuracy: 'city',
      confidence: 0.7,
      source: 'database',
    };
  }

  // 4. Try city extraction and lookup
  const cityName = extractCityName(location);
  if (cityName && CROATIAN_CITY_COORDINATES[cityName]) {
    const coords = CROATIAN_CITY_COORDINATES[cityName];
    return {
      ...coords,
      accuracy: 'city',
      confidence: 0.6,
      source: 'database',
    };
  }

  // 5. Try Mapbox API for unknown venues
  const mapboxResult = await geocodeLocation(location);
  if (mapboxResult) {
    logger.info(`Mapbox geocoded: ${location} → ${mapboxResult.place_name}`);
    return mapboxResult;
  }

  // 6. Final fallback with context
  if (context) {
    const contextResult = await geocodeLocation(`${location} ${context}`);
    if (contextResult) {
      return {
        ...contextResult,
        confidence: Math.max(contextResult.confidence - 0.2, 0.1),
      };
    }
  }

  logger.warn(`Could not geocode location: ${location}`);
  return null;
}
