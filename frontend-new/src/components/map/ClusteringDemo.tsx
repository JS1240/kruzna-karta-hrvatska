/**
 * ClusteringDemo component for testing and demonstrating event clustering
 * Shows clustering behavior at different zoom levels with sample data
 */

import React, { useState, useCallback } from 'react';
import { EventMap } from './EventMap';
import { Event } from '@/types/event';

// Sample events with overlapping coordinates to test clustering
const sampleEvents: Event[] = [
  // Zagreb cluster
  {
    id: 1,
    title: 'Zagreb Music Festival',
    date: '2025-08-15',
    time: '20:00',
    latitude: 45.8150,
    longitude: 15.9819,
    location: 'Zagreb',
    source: 'demo',
    event_status: 'active',
    is_featured: true,
    is_recurring: false,
    approval_status: 'approved',
    platform_commission_rate: 0.05,
    is_user_generated: false,
    timezone: 'Europe/Zagreb',
    view_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    price: '€25'
  },
  {
    id: 2,
    title: 'Zagreb Art Exhibition',
    date: '2025-08-16',
    time: '18:00',
    latitude: 45.8155, // Very close to first event
    longitude: 15.9825,
    location: 'Zagreb',
    source: 'demo',
    event_status: 'active',
    is_featured: false,
    is_recurring: false,
    approval_status: 'approved',
    platform_commission_rate: 0.05,
    is_user_generated: false,
    timezone: 'Europe/Zagreb',
    view_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    price: '€15'
  },
  {
    id: 3,
    title: 'Zagreb Tech Conference',
    date: '2025-08-17',
    time: '09:00',
    latitude: 45.8145, // Very close to first event
    longitude: 15.9815,
    location: 'Zagreb',
    source: 'demo',
    event_status: 'active',
    is_featured: false,
    is_recurring: false,
    approval_status: 'approved',
    platform_commission_rate: 0.05,
    is_user_generated: false,
    timezone: 'Europe/Zagreb',
    view_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    price: '€50'
  },
  
  // Split cluster
  {
    id: 4,
    title: 'Split Summer Festival',
    date: '2025-08-20',
    time: '21:00',
    latitude: 43.5147,
    longitude: 16.4435,
    location: 'Split',
    source: 'demo',
    event_status: 'active',
    is_featured: true,
    is_recurring: false,
    approval_status: 'approved',
    platform_commission_rate: 0.05,
    is_user_generated: false,
    timezone: 'Europe/Zagreb',
    view_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    price: '€30'
  },
  {
    id: 5,
    title: 'Split Food Market',
    date: '2025-08-21',
    time: '10:00',
    latitude: 43.5150, // Close to Split event
    longitude: 16.4440,
    location: 'Split',
    source: 'demo',
    event_status: 'active',
    is_featured: false,
    is_recurring: false,
    approval_status: 'approved',
    platform_commission_rate: 0.05,
    is_user_generated: false,
    timezone: 'Europe/Zagreb',
    view_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    price: 'Free'
  },

  // Individual events (will not cluster)
  {
    id: 6,
    title: 'Dubrovnik Concert',
    date: '2025-08-25',
    time: '19:30',
    latitude: 42.6507,
    longitude: 18.0944,
    location: 'Dubrovnik',
    source: 'demo',
    event_status: 'active',
    is_featured: false,
    is_recurring: false,
    approval_status: 'approved',
    platform_commission_rate: 0.05,
    is_user_generated: false,
    timezone: 'Europe/Zagreb',
    view_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    price: '€40'
  },
  {
    id: 7,
    title: 'Rijeka Port Festival',
    date: '2025-08-28',
    time: '16:00',
    latitude: 45.3371,
    longitude: 14.4087,
    location: 'Rijeka',
    source: 'demo',
    event_status: 'active',
    is_featured: false,
    is_recurring: false,
    approval_status: 'approved',
    platform_commission_rate: 0.05,
    is_user_generated: false,
    timezone: 'Europe/Zagreb',
    view_count: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    price: '€20'
  }
];

export const ClusteringDemo: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [mapInfo, setMapInfo] = useState({
    zoom: 7,
    eventCount: sampleEvents.length
  });

  const handleEventClick = useCallback((event: Event) => {
    setSelectedEvent(event);
    console.log('Event clicked:', event.title);
  }, []);

  const handleMapMove = useCallback((bounds: any, zoom: number) => {
    setMapInfo(prev => ({ ...prev, zoom: Math.round(zoom * 10) / 10 }));
  }, []);

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow-lg p-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Event Clustering Demo
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          This demo shows how events with overlapping coordinates are clustered based on zoom level.
          Zoom in to see individual events, zoom out to see clusters.
        </p>
        
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <strong>Current Zoom:</strong> {mapInfo.zoom}
          </div>
          <div>
            <strong>Total Events:</strong> {mapInfo.eventCount}
          </div>
        </div>

        {selectedEvent && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-900">Selected Event:</h3>
            <p className="text-blue-800">{selectedEvent.title}</p>
            <p className="text-sm text-blue-600">
              {selectedEvent.date} at {selectedEvent.time} • {selectedEvent.location}
            </p>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <EventMap
          events={sampleEvents}
          onEventClick={handleEventClick}
          onMapMove={handleMapMove}
          height="500px"
          enableClustering={true}
          showClusteringControls={true}
          initialZoom={7}
        />
      </div>

      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-2">Test Instructions:</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• <strong>Low zoom (3-8):</strong> Events cluster aggressively by city</li>
          <li>• <strong>Medium zoom (8-14):</strong> Nearby events cluster together</li>
          <li>• <strong>High zoom (15+):</strong> Individual events with micro-positioning</li>
          <li>• <strong>Click clusters:</strong> Zoom in or show event list</li>
          <li>• <strong>Click events:</strong> Show event details</li>
        </ul>
      </div>
    </div>
  );
};

export default ClusteringDemo;