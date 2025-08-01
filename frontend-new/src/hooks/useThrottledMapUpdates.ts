/**
 * Hook for throttled map state updates to improve performance during pan/zoom operations
 * Separates immediate updates (marker positions) from expensive updates (clustering)
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { rafThrottle, advancedDebounce, performanceMonitor } from '@/lib/utils';
import { MapBounds } from '@/types/event';

interface MapState {
  zoom: number;
  bounds: MapBounds | null;
  mapSize: { width: number; height: number };
}

interface ThrottledMapUpdatesOptions {
  // Throttle immediate updates (marker positions) - default 16ms for 60fps
  immediateThrottleMs?: number;
  // Debounce expensive updates (clustering) - default 250ms
  expensiveDebounceMs?: number;
  // Enable performance monitoring
  enablePerformanceMonitoring?: boolean;
}

interface ThrottledMapUpdatesReturn {
  // Immediate state - updates frequently for smooth animations
  immediateState: MapState;
  // Stable state - updates less frequently for expensive operations
  stableState: MapState;
  // Update functions
  updateMapState: (state: Partial<MapState>) => void;
  // Performance metrics
  getPerformanceMetrics: () => Record<string, { avg: number; count: number; last: number }>;
  // Force immediate update of stable state
  forceStableUpdate: () => void;
}

export const useThrottledMapUpdates = (
  options: ThrottledMapUpdatesOptions = {}
): ThrottledMapUpdatesReturn => {
  const {
    expensiveDebounceMs = 250,
    enablePerformanceMonitoring = false
  } = options;

  // Immediate state for smooth animations (marker positions)
  const [immediateState, setImmediateState] = useState<MapState>({
    zoom: 7,
    bounds: null,
    mapSize: { width: 800, height: 600 }
  });

  // Stable state for expensive operations (clustering)
  const [stableState, setStableState] = useState<MapState>({
    zoom: 7,
    bounds: null,
    mapSize: { width: 800, height: 600 }
  });

  // Refs to track latest state for debounced updates
  const latestStateRef = useRef<MapState>(immediateState);
  const performanceEnabled = useRef(enablePerformanceMonitoring);

  // Throttled immediate update for smooth marker positioning
  const throttledImmediateUpdate = useCallback((newState: Partial<MapState>) => {
    rafThrottle(() => {
      const endTiming = performanceEnabled.current 
        ? performanceMonitor.startTiming('immediate-update')
        : () => 0;

      setImmediateState(prevState => {
        const updatedState = { ...prevState, ...newState };
        latestStateRef.current = updatedState;
        return updatedState;
      });

      endTiming();
    })();
  }, []);

  // Debounced stable update for expensive operations
  const debouncedStableUpdate = useCallback(
    advancedDebounce(() => {
      const endTiming = performanceEnabled.current 
        ? performanceMonitor.startTiming('stable-update')
        : () => 0;

      setStableState(latestStateRef.current);
      endTiming();
    }, expensiveDebounceMs),
    [expensiveDebounceMs]
  );

  // Main update function
  const updateMapState = useCallback((newState: Partial<MapState>) => {
    // Always update immediate state for smooth animations
    throttledImmediateUpdate(newState);
    
    // Debounce stable state updates for expensive operations
    debouncedStableUpdate();
  }, [throttledImmediateUpdate, debouncedStableUpdate]);

  // Force immediate update of stable state (useful for initial load or manual refresh)
  const forceStableUpdate = useCallback(() => {
    setStableState(latestStateRef.current);
  }, []);

  // Get performance metrics
  const getPerformanceMetrics = useCallback(() => {
    if (!performanceEnabled.current) {
      return {};
    }
    return performanceMonitor.getMetrics();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (performanceEnabled.current) {
        performanceMonitor.clear();
      }
    };
  }, []);

  return {
    immediateState,
    stableState,
    updateMapState,
    getPerformanceMetrics,
    forceStableUpdate
  };
};

/**
 * Hook for batched marker position calculations to improve rendering performance
 */
export const useMarkerPositionBatch = (mapInstance: mapboxgl.Map | null) => {
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map());
  const batchUpdateRef = useRef<Map<string, [number, number]>>(new Map());
  
  // RAF-throttled batch position calculation
  const processBatch = useCallback(
    rafThrottle(() => {
      if (!mapInstance || batchUpdateRef.current.size === 0) return;

      const endTiming = performanceMonitor.startTiming('batch-projection');
      const newPositions = new Map<string, { x: number; y: number }>();

      // Process all queued position updates in a single batch
      batchUpdateRef.current.forEach(([lng, lat], id) => {
        try {
          const point = mapInstance.project([lng, lat]);
          newPositions.set(id, { x: point.x, y: point.y });
        } catch (error) {
          console.warn(`Failed to project marker ${id}:`, error);
        }
      });

      setPositions(newPositions);
      batchUpdateRef.current.clear();
      endTiming();
    }),
    [mapInstance]
  );

  // Queue a marker for position update
  const queueMarkerUpdate = useCallback((id: string, longitude: number, latitude: number) => {
    batchUpdateRef.current.set(id, [longitude, latitude]);
    processBatch();
  }, [processBatch]);

  // Get position for a specific marker
  const getMarkerPosition = useCallback((id: string) => {
    return positions.get(id) || { x: 0, y: 0 };
  }, [positions]);

  return {
    queueMarkerUpdate,
    getMarkerPosition,
    positions
  };
};