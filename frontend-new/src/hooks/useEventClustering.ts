/**
 * React hook for real-time event clustering
 * Manages clustering state based on map zoom and bounds changes
 */

import { useMemo, useCallback, useRef, useEffect } from 'react';
import { Event, MapBounds } from '@/types/event';
import { performanceMonitor } from '@/lib/utils';
import { 
  clusterEvents, 
  getClusterConfig, 
  type EventCluster, 
  type ClusteringOptions 
} from '@/utils/mapClustering';

interface UseEventClusteringOptions {
  mapBounds?: MapBounds;
  mapSize?: { width: number; height: number };
  zoom: number;
  minClusterSize?: number;
  maxClusterDistance?: number;
  enableClustering?: boolean;
}

interface UseEventClusteringReturn {
  clusters: EventCluster[];
  config: ReturnType<typeof getClusterConfig>;
  isProcessing: boolean;
  totalEvents: number;
  clusterCount: number;
  singleEventCount: number;
  recluster: () => void;
}

/**
 * Hook for managing event clustering with real-time updates
 * @param events Array of events to cluster
 * @param options Clustering configuration
 * @returns Clustered events and clustering utilities
 */
export const useEventClustering = (
  events: Event[],
  options: UseEventClusteringOptions
): UseEventClusteringReturn => {
  const {
    mapBounds,
    mapSize = { width: 800, height: 600 },
    zoom,
    minClusterSize = 2,
    maxClusterDistance,
    enableClustering = true
  } = options;

  // Ref to track processing state
  const isProcessingRef = useRef(false);
  const lastProcessedRef = useRef<string>('');

  // Get zoom-dependent configuration
  const config = useMemo(() => getClusterConfig(zoom), [zoom]);

  // Create a stable key for clustering input to prevent unnecessary recalculations
  const clusteringKey = useMemo(() => {
    const eventsKey = events.map(e => `${e.id}-${e.latitude}-${e.longitude}`).join('|');
    const boundsKey = mapBounds ? `${mapBounds.north}-${mapBounds.south}-${mapBounds.east}-${mapBounds.west}` : 'no-bounds';
    const sizeKey = `${mapSize.width}x${mapSize.height}`;
    
    return `${eventsKey}-${boundsKey}-${sizeKey}-${zoom}-${enableClustering}`;
  }, [events, mapBounds, mapSize, zoom, enableClustering]);

  // Main clustering computation with performance monitoring
  const clusters = useMemo(() => {
    const endTiming = performanceMonitor.startTiming('clustering');
    
    try {
      // Skip clustering if disabled or missing required data
      if (!enableClustering || !mapBounds || events.length === 0) {
        const fallbackClusters = events.map(event => ({
          id: `single-${event.id}`,
          events: [event],
          center: {
            latitude: event.latitude || 0,
            longitude: event.longitude || 0
          },
          pixelCenter: { x: 0, y: 0 },
          count: 1,
          category: 'other',
          isCluster: false
        } as EventCluster));
        
        endTiming();
        return fallbackClusters;
      }

      // Mark as processing
      isProcessingRef.current = true;

      const clusteringOptions: ClusteringOptions = {
        zoom,
        mapBounds,
        mapSize,
        minClusterSize,
        maxClusterDistance
      };

      try {
        const result = clusterEvents(events, clusteringOptions);
        lastProcessedRef.current = clusteringKey;
        return result;
      } catch (error) {
        console.error('Clustering failed:', error);
        // Fallback to individual events
        return events.map(event => ({
          id: `fallback-${event.id}`,
          events: [event],
          center: {
            latitude: event.latitude || 0,
            longitude: event.longitude || 0
          },
          pixelCenter: { x: 0, y: 0 },
          count: 1,
          category: 'other',
          isCluster: false
        } as EventCluster));
      } finally {
        isProcessingRef.current = false;
      }
    } finally {
      endTiming();
    }
  }, [clusteringKey, enableClustering, mapBounds, events, zoom, mapSize, minClusterSize, maxClusterDistance]);

  // Calculate clustering statistics
  const statistics = useMemo(() => {
    const clusterCount = clusters.filter(c => c.isCluster).length;
    const singleEventCount = clusters.filter(c => !c.isCluster).length;
    const totalEvents = clusters.reduce((sum, c) => sum + c.count, 0);

    return {
      totalEvents,
      clusterCount,
      singleEventCount
    };
  }, [clusters]);

  // Force reclustering function
  const recluster = useCallback(() => {
    // This will trigger a re-render by changing the clustering key
    lastProcessedRef.current = '';
  }, []);

  // Debug logging in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Event clustering update:', {
        totalEvents: statistics.totalEvents,
        clusters: statistics.clusterCount,
        singles: statistics.singleEventCount,
        zoom,
        config
      });
    }
  }, [statistics, zoom, config]);

  return {
    clusters,
    config,
    isProcessing: isProcessingRef.current,
    totalEvents: statistics.totalEvents,
    clusterCount: statistics.clusterCount,
    singleEventCount: statistics.singleEventCount,
    recluster
  };
};

/**
 * Simplified hook for just getting cluster configuration
 * @param zoom Current map zoom level
 * @returns Clustering configuration for the zoom level
 */
export const useClusterConfig = (zoom: number) => {
  return useMemo(() => getClusterConfig(zoom), [zoom]);
};

/**
 * Hook for detecting when clustering behavior should change
 * Useful for showing UI hints or notifications
 * @param zoom Current zoom level
 * @returns Information about clustering state changes
 */
export const useClusteringTransitions = (zoom: number) => {
  const config = useClusterConfig(zoom);
  
  return useMemo(() => ({
    isTransitionZone: zoom >= 13 && zoom <= 16, // Near the clustering threshold
    justDisabledClustering: zoom === 15, // Exact threshold
    shouldShowHint: zoom >= 14 && zoom < 16, // Show UI hints
    message: zoom >= 15 
      ? 'Events are now shown individually with precise positioning'
      : zoom >= 12 
      ? 'Zoom in more to see individual events'
      : 'Events are grouped by location - click clusters to explore'
  }), [zoom, config]);
};