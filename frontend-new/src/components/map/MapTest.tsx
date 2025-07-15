import React, { useRef, useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';

const MapTest: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('Initializing...');

  useEffect(() => {
    // Set access token
    const token = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
    console.log('Mapbox token:', token ? 'Token exists' : 'No token found');
    
    if (!token) {
      setError('Mapbox token not found');
      return;
    }

    mapboxgl.accessToken = token;
    setStatus('Token set, creating map...');

    if (!mapContainer.current) {
      setError('Map container not found');
      return;
    }

    try {
      // Create simple map
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center: [15.9819, 45.8150], // Zagreb coordinates
        zoom: 8,
      });

      map.current.on('load', () => {
        setStatus('Map loaded successfully!');
        setError(null);
      });

      map.current.on('error', (e) => {
        console.error('Mapbox error:', e);
        setError(`Map error: ${e.error?.message || 'Unknown error'}`);
      });

    } catch (err) {
      console.error('Error creating map:', err);
      setError(`Initialization error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }

    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold mb-4">Map Test Component</h3>
      
      <div className="mb-4 p-4 bg-gray-100 rounded">
        <p><strong>Status:</strong> {status}</p>
        {error && <p className="text-red-600"><strong>Error:</strong> {error}</p>}
      </div>

      <div
        ref={mapContainer}
        className="w-full h-96 border border-gray-300 rounded"
        style={{ minHeight: '400px' }}
      />
    </div>
  );
};

export default MapTest;