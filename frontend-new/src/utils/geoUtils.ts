/**
 * Geographic utility functions for map operations
 * Handles coordinate calculations, distance measurements, and spatial operations
 */

export interface Point {
  x: number;
  y: number;
}

export interface GeoPoint {
  latitude: number;
  longitude: number;
}

export interface PixelPoint {
  x: number;
  y: number;
}

/**
 * Calculate the distance between two geographic points using Haversine formula
 * @param point1 First geographic point
 * @param point2 Second geographic point
 * @returns Distance in kilometers
 */
export const calculateDistance = (point1: GeoPoint, point2: GeoPoint): number => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = toRadians(point2.latitude - point1.latitude);
  const dLon = toRadians(point2.longitude - point1.longitude);
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(point1.latitude)) * Math.cos(toRadians(point2.latitude)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * Convert degrees to radians
 */
const toRadians = (degrees: number): number => {
  return degrees * (Math.PI / 180);
};

/**
 * Calculate pixel distance between two screen points
 * @param point1 First pixel point
 * @param point2 Second pixel point
 * @returns Distance in pixels
 */
export const calculatePixelDistance = (point1: PixelPoint, point2: PixelPoint): number => {
  const dx = point2.x - point1.x;
  const dy = point2.y - point1.y;
  return Math.sqrt(dx * dx + dy * dy);
};

/**
 * Convert geographic coordinates to pixel coordinates using Mercator projection
 * @param geoPoint Geographic coordinates
 * @param mapBounds Map bounds in geographic coordinates
 * @param mapSize Map size in pixels
 * @returns Pixel coordinates
 */
export const geoToPixel = (
  geoPoint: GeoPoint,
  mapBounds: { 
    north: number; 
    south: number; 
    east: number; 
    west: number; 
  },
  mapSize: { width: number; height: number }
): PixelPoint => {
  const x = ((geoPoint.longitude - mapBounds.west) / (mapBounds.east - mapBounds.west)) * mapSize.width;
  const y = ((mapBounds.north - geoPoint.latitude) / (mapBounds.north - mapBounds.south)) * mapSize.height;
  
  return { x, y };
};

/**
 * Get zoom-dependent clustering distance threshold
 * @param zoom Current map zoom level
 * @returns Clustering distance threshold in pixels
 */
export const getClusteringThreshold = (zoom: number): number => {
  // High zoom (>14): 20px threshold (less clustering)
  // Medium zoom (8-14): 30-50px threshold
  // Low zoom (<8): 60px threshold (more aggressive clustering)
  
  if (zoom > 14) return 20;
  if (zoom > 8) return 30 + (14 - zoom) * 3; // 30-48px range
  return 60;
};

/**
 * Check if clustering should be disabled at current zoom level
 * @param zoom Current map zoom level
 * @returns True if events should be shown individually
 */
export const shouldDisableClustering = (zoom: number): boolean => {
  // Disable clustering when zoomed in beyond 70-80% (roughly zoom level 15+)
  return zoom >= 15;
};

/**
 * Generate a small random offset to prevent exact overlaps
 * @param index Event index for consistent positioning
 * @param maxOffset Maximum offset in pixels
 * @returns Pixel offset
 */
export const getMicroOffset = (index: number, maxOffset: number = 8): PixelPoint => {
  // Use index to generate consistent but distributed offsets
  const angle = (index * 137.508) % 360; // Golden angle for good distribution
  const distance = (index % 3) * (maxOffset / 3); // 0, 8/3, 16/3 pixel distances
  
  return {
    x: Math.cos(toRadians(angle)) * distance,
    y: Math.sin(toRadians(angle)) * distance
  };
};

/**
 * Calculate the center point of a group of geographic coordinates
 * @param points Array of geographic points
 * @returns Center point
 */
export const calculateCentroid = (points: GeoPoint[]): GeoPoint => {
  if (points.length === 0) {
    throw new Error('Cannot calculate centroid of empty point array');
  }
  
  const sum = points.reduce(
    (acc, point) => ({
      latitude: acc.latitude + point.latitude,
      longitude: acc.longitude + point.longitude
    }),
    { latitude: 0, longitude: 0 }
  );
  
  return {
    latitude: sum.latitude / points.length,
    longitude: sum.longitude / points.length
  };
};

/**
 * Calculate bounding box for a group of geographic points
 * @param points Array of geographic points
 * @returns Bounding box with padding
 */
export const calculateBounds = (
  points: GeoPoint[], 
  padding: number = 0.001
): { north: number; south: number; east: number; west: number } => {
  if (points.length === 0) {
    throw new Error('Cannot calculate bounds of empty point array');
  }
  
  let north = points[0].latitude;
  let south = points[0].latitude;
  let east = points[0].longitude;
  let west = points[0].longitude;
  
  points.forEach(point => {
    north = Math.max(north, point.latitude);
    south = Math.min(south, point.latitude);
    east = Math.max(east, point.longitude);
    west = Math.min(west, point.longitude);
  });
  
  return {
    north: north + padding,
    south: south - padding,
    east: east + padding,
    west: west - padding
  };
};

/**
 * Check if a point is within specified bounds
 * @param point Geographic point to check
 * @param bounds Bounding box
 * @returns True if point is within bounds
 */
export const isPointInBounds = (
  point: GeoPoint,
  bounds: { north: number; south: number; east: number; west: number }
): boolean => {
  return (
    point.latitude >= bounds.south &&
    point.latitude <= bounds.north &&
    point.longitude >= bounds.west &&
    point.longitude <= bounds.east
  );
};

/**
 * Validate geographic coordinates
 * @param point Geographic point to validate
 * @returns True if coordinates are valid
 */
export const isValidGeoPoint = (point: Partial<GeoPoint>): point is GeoPoint => {
  return (
    typeof point.latitude === 'number' &&
    typeof point.longitude === 'number' &&
    !isNaN(point.latitude) &&
    !isNaN(point.longitude) &&
    point.latitude >= -90 &&
    point.latitude <= 90 &&
    point.longitude >= -180 &&
    point.longitude <= 180
  );
};