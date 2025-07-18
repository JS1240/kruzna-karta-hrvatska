import React, { useState } from 'react';
import { MapPin, RefreshCw, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface GeocodingPanelProps {
  className?: string;
}

export const GeocodingPanel: React.FC<GeocodingPanelProps> = ({ className }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const queryClient = useQueryClient();

  // Get geocoding status
  const { data: status, isLoading, error } = useQuery({
    queryKey: ['geocoding-status'],
    queryFn: () => apiClient.getGeocodingStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Geocode events mutation
  const geocodeMutation = useMutation({
    mutationFn: (limit: number) => apiClient.geocodeEvents(limit),
    onSuccess: (data) => {
      // Refresh the status after successful geocoding
      queryClient.invalidateQueries({ queryKey: ['geocoding-status'] });
      queryClient.invalidateQueries({ queryKey: ['events'] });
      console.log('Geocoding completed:', data);
    },
    onError: (error) => {
      console.error('Geocoding failed:', error);
    },
  });

  const handleGeocode = (limit: number) => {
    geocodeMutation.mutate(limit);
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
          <span className="text-sm text-gray-600">Loading geocoding status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-red-200 p-4 ${className}`}>
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600" />
          <span className="text-sm text-red-600">Error loading geocoding status</span>
        </div>
      </div>
    );
  }

  if (!status) return null;

  const needsGeocoding = status.events_need_geocoding > 0;
  const hasGoodCoverage = status.geocoding_percentage >= 80;

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">Event Geocoding</h3>
          {hasGoodCoverage ? (
            <CheckCircle className="w-4 h-4 text-green-600" />
          ) : (
            <AlertCircle className="w-4 h-4 text-orange-600" />
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">
            {status.geocoding_percentage}% geocoded
          </span>
          <RefreshCw 
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
          />
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          {/* Status Summary */}
          <div className="grid grid-cols-2 gap-4 mb-4 mt-4">
            <div className="text-center p-3 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-gray-900">{status.events_with_coordinates}</div>
              <div className="text-sm text-gray-600">With Coordinates</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-orange-600">{status.events_need_geocoding}</div>
              <div className="text-sm text-gray-600">Need Geocoding</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Geocoding Progress</span>
              <span>{status.geocoding_percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all ${
                  hasGoodCoverage ? 'bg-green-600' : 'bg-orange-600'
                }`}
                style={{ width: `${status.geocoding_percentage}%` }}
              />
            </div>
          </div>

          {/* Action Buttons */}
          {needsGeocoding && (
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                {status.events_need_geocoding} events need geocoding to appear on the map.
              </p>
              
              <div className="flex gap-2">
                <button
                  onClick={() => handleGeocode(25)}
                  disabled={geocodeMutation.isPending}
                  className="btn btn-primary text-sm px-3 py-2 flex-1 disabled:opacity-50"
                >
                  {geocodeMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-1" />
                      Geocoding...
                    </>
                  ) : (
                    'Geocode 25 Events'
                  )}
                </button>
                
                <button
                  onClick={() => handleGeocode(50)}
                  disabled={geocodeMutation.isPending}
                  className="btn btn-secondary text-sm px-3 py-2 flex-1 disabled:opacity-50"
                >
                  Geocode 50 Events
                </button>
              </div>
              
              {status.events_need_geocoding > 50 && (
                <button
                  onClick={() => handleGeocode(status.events_need_geocoding)}
                  disabled={geocodeMutation.isPending}
                  className="btn btn-outline text-sm px-3 py-2 w-full disabled:opacity-50"
                >
                  Geocode All ({status.events_need_geocoding} events)
                </button>
              )}
            </div>
          )}

          {!needsGeocoding && (
            <div className="text-center p-3 bg-green-50 rounded">
              <CheckCircle className="w-6 h-6 text-green-600 mx-auto mb-1" />
              <p className="text-sm text-green-800">All events have coordinates!</p>
            </div>
          )}

          {/* Last geocoding result */}
          {geocodeMutation.data && (
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <p className="text-sm text-blue-800">
                ✅ Successfully geocoded {geocodeMutation.data.geocoded_count} of {geocodeMutation.data.total_checked} events
              </p>
            </div>
          )}

          {geocodeMutation.error && (
            <div className="mt-4 p-3 bg-red-50 rounded">
              <p className="text-sm text-red-800">
                ❌ Geocoding failed: {geocodeMutation.error.message}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GeocodingPanel;