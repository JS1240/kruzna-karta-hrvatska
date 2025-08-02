import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import { Loader2, AlertCircle, MapIcon, Layers } from 'lucide-react';
import { Event, MapBounds, EventCluster, MapInteractionState } from '@/types/event';
import { useEventClustering, useClusteringTransitions } from '@/hooks/useEventClustering';
import { useThrottledMapUpdates, useMarkerPositionBatch } from '@/hooks/useThrottledMapUpdates';
import { ClusterMarker, SelectedClusterMarker } from './ClusterMarker';
import { EventClusterPopup, SingleEventPopup } from './EventClusterPopup';
import clsx from 'clsx';

// Make mapbox-gl available globally
(window as any).mapboxgl = mapboxgl;

interface EventMapProps {
  events: Event[];
  loading?: boolean;
  onEventClick?: (event: Event) => void;
  onMapMove?: (bounds: MapBounds, zoom: number) => void;
  className?: string;
  height?: string;
  showZoomControls?: boolean;
  initialCenter?: [number, number];
  initialZoom?: number;
  enableClustering?: boolean;
  showClusteringControls?: boolean;
}

// Default Croatian coordinates (Zagreb)
const DEFAULT_CENTER: [number, number] = [15.9819, 45.8150];
const DEFAULT_ZOOM = 7;


export const EventMap: React.FC<EventMapProps> = ({
  events,
  loading = false,
  onEventClick,
  onMapMove,
  className,
  height = '600px',
  showZoomControls = true,
  initialCenter = DEFAULT_CENTER,
  initialZoom = DEFAULT_ZOOM,
  enableClustering = true,
  showClusteringControls = true,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  
  // Use throttled map updates for better performance
  const {
    immediateState,
    stableState,
    updateMapState,
    getPerformanceMetrics
  } = useThrottledMapUpdates({
    enablePerformanceMonitoring: process.env.NODE_ENV === 'development'
  });
  
  // Use batched marker position calculations
  const { queueMarkerUpdate, getMarkerPosition } =
    useMarkerPositionBatch(map.current || undefined);
  
  // Clustering state
  const [interactionState, setInteractionState] = useState<MapInteractionState>({
    selectedCluster: null,
    hoveredCluster: null,
    showClusterPopup: false,
  });

  // Filter events that have valid coordinates
  const validEvents = useMemo(() => {
    const filtered = events.filter(event => 
      event.latitude && 
      event.longitude && 
      !isNaN(event.latitude) && 
      !isNaN(event.longitude)
    );
    
    // Log coordination data issues for debugging
    const invalidEvents = events.length - filtered.length;
    if (invalidEvents > 0) {
      console.warn(`EventMap: ${invalidEvents} of ${events.length} events filtered out due to invalid coordinates`);
      console.debug('Sample event with invalid coordinates:', events.find(e => !e.latitude || !e.longitude || isNaN(e.latitude) || isNaN(e.longitude)));
    }
    
    return filtered;
  }, [events]);

  // Use clustering hook with stable state for expensive operations
  const { clusters, config, isProcessing, totalEvents, clusterCount, singleEventCount } = useEventClustering(
    validEvents,
    {
      mapBounds: stableState.bounds || undefined,
      mapSize: stableState.mapSize,
      zoom: stableState.zoom,
      enableClustering
    }
  );

  // Use clustering transitions for UI hints with immediate state for smooth feedback
  const transitions = useClusteringTransitions(immediateState.zoom);


  // Initialize map (only once)
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
    if (!mapboxToken) {
      setMapError('Mapbox access token is required');
      return;
    }

    // Set token
    mapboxgl.accessToken = mapboxToken;

    try {
      // Create map instance
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center: initialCenter,
        zoom: initialZoom,
        attributionControl: false,
      });

      // Add navigation controls
      if (showZoomControls) {
        map.current.addControl(new mapboxgl.NavigationControl(), 'bottom-right');
      }

      // Set up event handlers
      map.current.on('load', () => {
        setMapLoaded(true);
        setMapError(null);
      });

      map.current.on('error', (e) => {
        console.error('Map error:', e);
        setMapError('Failed to load map');
      });

      // Add throttled map move handler for better performance
      const handleMapUpdate = () => {
        if (map.current) {
          const bounds = map.current.getBounds();
          const zoom = map.current.getZoom();
          const mapBounds: MapBounds = {
            north: bounds?.getNorth() || 0,
            south: bounds?.getSouth() || 0,
            east: bounds?.getEast() || 0,
            west: bounds?.getWest() || 0,
          };
          
          // Update map size for clustering calculations
          const container = map.current.getContainer();
          const mapSize = container ? {
            width: container.clientWidth,
            height: container.clientHeight
          } : { width: 800, height: 600 };
          
          // Use throttled updates for better performance
          updateMapState({
            zoom,
            bounds: mapBounds,
            mapSize
          });
          
          // Call external handler with immediate updates
          onMapMove?.(mapBounds, zoom);
        }
      };

      // Add both immediate and final update handlers for smooth experience
      map.current.on('move', handleMapUpdate); // Immediate updates during movement
      map.current.on('zoom', handleMapUpdate); // Immediate updates during zoom
      map.current.on('moveend', handleMapUpdate); // Final update when movement stops
      map.current.on('zoomend', handleMapUpdate); // Final update when zoom stops
      map.current.on('resize', handleMapUpdate); // Handle window resize

    } catch (error) {
      console.error('Failed to initialize map:', error);
      setMapError('Failed to initialize map');
    }

    // Cleanup function
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []); // Run only once on mount

  // Clustering event handlers
  const zoomToCluster = useCallback((cluster: EventCluster) => {
    if (!map.current || !cluster.bounds) return;

    try {
      const bounds = new mapboxgl.LngLatBounds([
        [cluster.bounds.west, cluster.bounds.south],
        [cluster.bounds.east, cluster.bounds.north]
      ]);
      
      map.current.fitBounds(bounds, { 
        padding: 50,
        maxZoom: 16 
      });
    } catch (error) {
      console.error('Failed to zoom to cluster:', error);
    }
  }, []);

  const handleClusterClick = useCallback((cluster: EventCluster) => {
    if (!cluster.isCluster) {
      // Single event - show popup with event details
      setInteractionState(prev => ({
        ...prev,
        selectedCluster: cluster,
        showClusterPopup: true
      }));
      // Also trigger external event click handler if provided
      onEventClick?.(cluster.events[0]);
    } else {
      // Cluster - show popup or zoom to bounds using immediate state for responsive feel
      if (immediateState.zoom < 12) {
        // Zoom to cluster bounds if zoomed out significantly
        zoomToCluster(cluster);
      } else {
        // Show popup if already zoomed in enough
        setInteractionState(prev => ({
          ...prev,
          selectedCluster: cluster,
          showClusterPopup: true
        }));
      }
    }
  }, [immediateState.zoom, onEventClick, zoomToCluster]);

  const handleClusterHover = useCallback((cluster: EventCluster | null) => {
    setInteractionState(prev => ({
      ...prev,
      hoveredCluster: cluster
    }));
  }, []);

  const handleClosePopup = useCallback(() => {
    setInteractionState(prev => ({
      ...prev,
      selectedCluster: null,
      showClusterPopup: false
    }));
  }, []);

  // Clear map click handlers when clustering is enabled
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    try {
      // Remove old event layers and sources if they exist
      if (map.current.getSource('events')) {
        if (map.current.getLayer('event-points')) {
          map.current.removeLayer('event-points');
        }
        map.current.removeSource('events');
      }

      // Add map click handler to close popups
      const handleMapClick = () => {
        if (interactionState.showClusterPopup) {
          handleClosePopup();
        }
      };

      map.current.on('click', handleMapClick);

      return () => {
        if (map.current) {
          map.current.off('click', handleMapClick);
        }
      };

    } catch (error) {
      console.error('Failed to setup clustering map handlers:', error);
      return undefined;
    }
  }, [mapLoaded, interactionState.showClusterPopup, handleClosePopup]);

  // Fit map to show all events
  const fitMapToEvents = () => {
    if (map.current && validEvents.length > 0) {
      try {
        const bounds = new mapboxgl.LngLatBounds();
        validEvents.forEach(event => {
          bounds.extend([event.longitude!, event.latitude!]);
        });
        map.current.fitBounds(bounds, { padding: 50 });
      } catch (error) {
        console.error('Failed to fit map to events:', error);
      }
    }
  };

  if (loading) {
    return (
      <div 
        className={clsx(
          'flex items-center justify-center bg-gray-100 rounded-xl',
          className
        )}
        style={{ height }}
      >
        <div className="flex flex-col items-center space-y-2">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          <p className="text-sm text-gray-600">Loading map...</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div 
        className={clsx(
          'flex items-center justify-center bg-gray-100 rounded-xl',
          className
        )}
        style={{ height }}
      >
        <div className="flex flex-col items-center space-y-2 text-center p-4">
          <AlertCircle className="h-8 w-8 text-red-500" />
          <p className="text-sm text-gray-600">{mapError}</p>
          <p className="text-xs text-gray-500">Please check your configuration.</p>
        </div>
      </div>
    );
  }

  // Show warning if events are loaded but none have coordinates
  if (!loading && events.length > 0 && validEvents.length === 0) {
    return (
      <div 
        className={clsx(
          'flex items-center justify-center bg-amber-50 border border-amber-200 rounded-xl',
          className
        )}
        style={{ height }}
      >
        <div className="flex flex-col items-center space-y-2 text-center p-4">
          <AlertCircle className="h-8 w-8 text-amber-500" />
          <p className="text-sm text-amber-800">Map Unavailable</p>
          <p className="text-xs text-amber-700">
            {events.length} events loaded but none have valid coordinates.
            Events may need geocoding or there may be a data issue.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('relative rounded-xl overflow-hidden', className)}>
      <div 
        ref={mapContainer} 
        style={{ 
          height: height,
          width: '100%',
          minHeight: '400px',
        }} 
      />
      
      {/* Render cluster markers with optimized positioning */}
      {mapLoaded && stableState.bounds && clusters.map((cluster) => {
        if (!map.current) return null;
        
        // Queue position update for batched processing
        queueMarkerUpdate(cluster.id, cluster.center.longitude, cluster.center.latitude);
        const position = getMarkerPosition(cluster.id);
        
        return (
          <div
            key={cluster.id}
            style={{
              position: 'absolute',
              left: `${position.x}px`,
              top: `${position.y}px`,
              pointerEvents: 'auto',
              zIndex: interactionState.selectedCluster?.id === cluster.id ? 1000 : 10,
              transform: 'translateZ(0)', // Enable hardware acceleration
              willChange: 'transform' // Optimize for frequent position changes
            }}
          >
            {interactionState.selectedCluster?.id === cluster.id ? (
              <SelectedClusterMarker
                cluster={cluster}
                onClose={handleClosePopup}
              />
            ) : (
              <ClusterMarker
                cluster={cluster}
                onClick={handleClusterClick}
                onHover={handleClusterHover}
                isSelected={interactionState.hoveredCluster?.id === cluster.id}
              />
            )}
          </div>
        );
      })}

      {/* Event/Cluster popup */}
      {interactionState.showClusterPopup && interactionState.selectedCluster && map.current && (
        (() => {
          const cluster = interactionState.selectedCluster;
          const point = map.current!.project([cluster.center.longitude, cluster.center.latitude]);
          
          return (
            <div
              className="absolute z-50 pointer-events-none"
              style={{
                left: `${point.x}px`,
                top: `${point.y - 20}px`,
                transform: 'translate(-50%, -100%)',
                pointerEvents: 'auto'
              }}
            >
              {cluster.isCluster ? (
                <EventClusterPopup
                  cluster={cluster}
                  onClose={handleClosePopup}
                  onEventClick={onEventClick}
                  onZoomToCluster={zoomToCluster}
                />
              ) : (
                <SingleEventPopup
                  event={cluster.events[0]}
                  onClose={handleClosePopup}
                  onEventClick={onEventClick}
                />
              )}
            </div>
          );
        })()
      )}
      
      {/* Map controls */}
      {validEvents.length > 0 && mapLoaded && (
        <div className="absolute top-4 right-4 space-y-2">
          {/* Fit to events button */}
          <div className="bg-white rounded-lg shadow-lg p-2">
            <button
              onClick={fitMapToEvents}
              className="flex items-center gap-2 px-3 py-1 text-sm text-gray-700 hover:text-primary-600 transition-colors"
            >
              <MapIcon className="w-4 h-4" />
              Fit to events
            </button>
          </div>

          {/* Clustering info panel */}
          {showClusteringControls && enableClustering && (
            <div className="bg-white rounded-lg shadow-lg p-3 text-xs text-gray-600">
              <div className="flex items-center gap-2 mb-2">
                <Layers className="w-3 h-3" />
                <span className="font-medium">Event Clustering</span>
              </div>
              <div className="space-y-1">
                <div>Total: {totalEvents} events</div>
                {config.shouldCluster && (
                  <>
                    <div>Clusters: {clusterCount}</div>
                    <div>Individual: {singleEventCount}</div>
                  </>
                )}
              </div>
              {transitions.shouldShowHint && (
                <div className="mt-2 text-xs text-blue-600">
                  {transitions.message}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Processing indicator */}
      {isProcessing && (
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg px-3 py-2 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="text-sm text-gray-600">Clustering events...</span>
        </div>
      )}

      {/* Performance monitoring panel (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute bottom-4 right-4 bg-black bg-opacity-80 text-white text-xs rounded-lg p-3 max-w-xs">
          <div className="font-semibold mb-2">Performance Metrics</div>
          {(() => {
            const metrics = getPerformanceMetrics();
            return Object.entries(metrics).map(([label, data]) => (
              <div key={label} className="flex justify-between mb-1">
                <span>{label}:</span>
                <span>{data.avg.toFixed(1)}ms (avg)</span>
              </div>
            ));
          })()}
          <div className="border-t border-gray-600 mt-2 pt-2">
            <div className="flex justify-between">
              <span>Events:</span>
              <span>{totalEvents}</span>
            </div>
            <div className="flex justify-between">
              <span>Clusters:</span>
              <span>{clusterCount}</span>
            </div>
            <div className="flex justify-between">
              <span>Zoom:</span>
              <span>{immediateState.zoom.toFixed(1)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventMap;