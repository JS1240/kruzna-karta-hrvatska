// Geocoding utilities for converting location names to coordinates
import { debugError } from "./debug";

export interface Coordinates {
  lat: number;
  lng: number;
}

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
 * Get coordinates for a location string
 */
export function getCoordinatesForLocation(
  location: string,
): Coordinates | null {
  if (!location) return null;

  const normalizedLocation = location.toLowerCase().trim();

  // Direct match
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

  console.warn(`Could not find coordinates for location: ${location}`);
  return null;
}

/**
 * Add jitter to coordinates to avoid overlapping markers
 */
export function addCoordinateJitter(
  coords: Coordinates,
  index: number = 0,
): Coordinates {
  const jitterAmount = 0.01; // ~1km
  const angle = (index * 45) % 360; // Spread markers in a circle
  const jitterLat = Math.cos((angle * Math.PI) / 180) * jitterAmount;
  const jitterLng = Math.sin((angle * Math.PI) / 180) * jitterAmount;

  return {
    lat: coords.lat + jitterLat,
    lng: coords.lng + jitterLng,
  };
}

/**
 * Mapbox Geocoding API (fallback for unknown locations)
 */
export async function geocodeLocation(
  location: string,
): Promise<Coordinates | null> {
  const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
  if (!mapboxToken) {
    console.warn("Mapbox token not available for geocoding");
    return null;
  }

  try {
    const query = encodeURIComponent(`${location}, Croatia`);
    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${query}.json?access_token=${mapboxToken}&country=hr&limit=1`,
    );

    if (!response.ok) {
      throw new Error(`Geocoding failed: ${response.status}`);
    }

    const data = await response.json();

    if (data.features && data.features.length > 0) {
      const [lng, lat] = data.features[0].center;
      return { lat, lng };
    }

    return null;
  } catch (error) {
    debugError("Geocoding error:", error);
    return null;
  }
}
