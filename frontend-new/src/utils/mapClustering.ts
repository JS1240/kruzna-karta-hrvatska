/**
 * Map clustering algorithms for grouping nearby events
 * Implements distance-based clustering with zoom-aware thresholds
 */

import { Event } from '@/types/event';
import { 
  calculatePixelDistance, 
  geoToPixel, 
  getClusteringThreshold, 
  shouldDisableClustering,
  calculateCentroid,
  getMicroOffset,
  isValidGeoPoint,
  type GeoPoint,
  type PixelPoint 
} from './geoUtils';

export interface EventCluster {
  id: string;
  events: Event[];
  center: GeoPoint;
  pixelCenter: PixelPoint;
  count: number;
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  category?: string; // Dominant category
  isCluster: boolean;
}

export interface ClusteringOptions {
  zoom: number;
  mapBounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  mapSize: {
    width: number;
    height: number;
  };
  minClusterSize?: number;
  maxClusterDistance?: number;
}

/**
 * Main clustering function that groups nearby events based on zoom level
 * @param events Array of events to cluster
 * @param options Clustering configuration options
 * @returns Array of clusters (may contain single-event clusters)
 */
export const clusterEvents = (
  events: Event[],
  options: ClusteringOptions
): EventCluster[] => {
  // Filter events with valid coordinates
  const validEvents = events.filter(event => 
    isValidGeoPoint({ latitude: event.latitude, longitude: event.longitude })
  );

  if (validEvents.length === 0) {
    return [];
  }

  // If clustering should be disabled at this zoom level, return individual events with micro-offsets
  if (shouldDisableClustering(options.zoom)) {
    return createIndividualClusters(validEvents, options);
  }

  // Perform distance-based clustering
  return performDistanceClustering(validEvents, options);
};

/**
 * Create individual clusters for each event with micro-positioning to prevent overlaps
 */
const createIndividualClusters = (
  events: Event[],
  options: ClusteringOptions
): EventCluster[] => {
  const clusters: EventCluster[] = [];
  const processedPositions = new Map<string, number>();

  events.forEach((event) => {
    const geoPoint: GeoPoint = {
      latitude: event.latitude!,
      longitude: event.longitude!
    };

    const pixelCenter = geoToPixel(geoPoint, options.mapBounds, options.mapSize);
    
    // Check for overlapping positions and apply micro-offset if needed
    const positionKey = `${Math.round(pixelCenter.x)}-${Math.round(pixelCenter.y)}`;
    const existingCount = processedPositions.get(positionKey) || 0;
    
    if (existingCount > 0) {
      const offset = getMicroOffset(existingCount);
      pixelCenter.x += offset.x;
      pixelCenter.y += offset.y;
    }
    
    processedPositions.set(positionKey, existingCount + 1);

    clusters.push({
      id: `single-${event.id}`,
      events: [event],
      center: geoPoint,
      pixelCenter,
      count: 1,
      category: inferEventCategory(event),
      isCluster: false
    });
  });

  return clusters;
};

/**
 * Perform distance-based clustering using a simple agglomerative approach
 */
const performDistanceClustering = (
  events: Event[],
  options: ClusteringOptions
): EventCluster[] => {
  const threshold = options.maxClusterDistance || getClusteringThreshold(options.zoom);
  const minSize = options.minClusterSize || 2;
  
  // Convert events to working clusters
  let clusters: EventCluster[] = events.map((event) => {
    const geoPoint: GeoPoint = {
      latitude: event.latitude!,
      longitude: event.longitude!
    };

    return {
      id: `temp-${event.id}`,
      events: [event],
      center: geoPoint,
      pixelCenter: geoToPixel(geoPoint, options.mapBounds, options.mapSize),
      count: 1,
      category: inferEventCategory(event),
      isCluster: false
    };
  });

  let merged = true;
  let iteration = 0;
  const maxIterations = 10; // Prevent infinite loops

  // Iteratively merge nearby clusters
  while (merged && iteration < maxIterations) {
    merged = false;
    iteration++;

    for (let i = 0; i < clusters.length - 1; i++) {
      for (let j = i + 1; j < clusters.length; j++) {
        const cluster1 = clusters[i];
        const cluster2 = clusters[j];

        const distance = calculatePixelDistance(
          cluster1.pixelCenter,
          cluster2.pixelCenter
        );

        if (distance <= threshold) {
          // Merge clusters
          const mergedEvents = [...cluster1.events, ...cluster2.events];
          const mergedCenter = calculateCentroid(
            mergedEvents.map(e => ({ latitude: e.latitude!, longitude: e.longitude! }))
          );

          const newCluster: EventCluster = {
            id: `cluster-${i}-${j}-${iteration}`,
            events: mergedEvents,
            center: mergedCenter,
            pixelCenter: geoToPixel(mergedCenter, options.mapBounds, options.mapSize),
            count: mergedEvents.length,
            category: getDominantCategory(mergedEvents),
            isCluster: mergedEvents.length >= minSize,
            bounds: calculateClusterBounds(mergedEvents)
          };

          // Replace cluster1 with merged cluster and remove cluster2
          clusters[i] = newCluster;
          clusters.splice(j, 1);
          merged = true;
          break;
        }
      }
      if (merged) break;
    }
  }

  // Final pass: ensure single-event clusters are marked correctly
  return clusters.map(cluster => ({
    ...cluster,
    id: cluster.isCluster ? `cluster-${cluster.count}-${Date.now()}` : `single-${cluster.events[0].id}`,
    isCluster: cluster.count >= minSize
  }));
};

/**
 * Infer event category from title and description
 */
const inferEventCategory = (event: Event): string => {
  const text = `${event.title} ${event.description || ''}`.toLowerCase();
  
  if (text.includes('concert') || text.includes('music') || text.includes('band')) return 'concert';
  if (text.includes('festival') || text.includes('fest')) return 'festival';
  if (text.includes('party') || text.includes('zabava')) return 'party';
  if (text.includes('conference') || text.includes('konferencija')) return 'conference';
  if (text.includes('theater') || text.includes('theatre')) return 'theater';
  if (text.includes('culture') || text.includes('kultura') || text.includes('art')) return 'culture';
  if (text.includes('workout') || text.includes('fitness')) return 'workout';
  if (text.includes('sport') || text.includes('football')) return 'sports';
  if (text.includes('meetup') || text.includes('meeting')) return 'meetup';
  
  return 'other';
};

/**
 * Get the dominant category from a group of events
 */
const getDominantCategory = (events: Event[]): string => {
  const categoryCounts = new Map<string, number>();
  
  events.forEach(event => {
    const category = inferEventCategory(event);
    categoryCounts.set(category, (categoryCounts.get(category) || 0) + 1);
  });

  let dominantCategory = 'other';
  let maxCount = 0;

  categoryCounts.forEach((count, category) => {
    if (count > maxCount) {
      maxCount = count;
      dominantCategory = category;
    }
  });

  // If no clear dominant category (tied), return 'mixed'
  const totalCategories = Array.from(categoryCounts.values()).filter(count => count === maxCount).length;
  return totalCategories > 1 ? 'mixed' : dominantCategory;
};

/**
 * Calculate bounds for a cluster of events
 */
const calculateClusterBounds = (events: Event[]) => {
  const points = events.map(e => ({ latitude: e.latitude!, longitude: e.longitude! }));
  
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

  return { north, south, east, west };
};

/**
 * Get cluster configuration for different zoom levels
 */
export const getClusterConfig = (zoom: number) => {
  return {
    shouldCluster: !shouldDisableClustering(zoom),
    threshold: getClusteringThreshold(zoom),
    minClusterSize: 2,
    showIndividualEvents: zoom >= 15,
    showEventCounts: zoom < 12,
    maxDisplayRadius: zoom > 10 ? 25 : zoom > 6 ? 35 : 45
  };
};