/**
 * ClusterMarker component for displaying event clusters on the map
 * Shows event count, category-based styling, and hover effects
 */

import React from 'react';
import { EventCluster } from '@/utils/mapClustering';
import clsx from 'clsx';

interface ClusterMarkerProps {
  cluster: EventCluster;
  onClick?: (cluster: EventCluster) => void;
  onHover?: (cluster: EventCluster | null) => void;
  isSelected?: boolean;
  className?: string;
}

// Category configuration for colors (matching EventMap)
const categoryConfig = {
  concert: { color: '#e74c3c', bgColor: 'bg-red-500', borderColor: 'border-red-600' },
  music: { color: '#e74c3c', bgColor: 'bg-red-500', borderColor: 'border-red-600' },
  festival: { color: '#f39c12', bgColor: 'bg-orange-500', borderColor: 'border-orange-600' },
  party: { color: '#9b59b6', bgColor: 'bg-purple-500', borderColor: 'border-purple-600' },
  conference: { color: '#3498db', bgColor: 'bg-blue-500', borderColor: 'border-blue-600' },
  theater: { color: '#2ecc71', bgColor: 'bg-green-500', borderColor: 'border-green-600' },
  culture: { color: '#e67e22', bgColor: 'bg-orange-600', borderColor: 'border-orange-700' },
  workout: { color: '#1abc9c', bgColor: 'bg-teal-500', borderColor: 'border-teal-600' },
  sports: { color: '#e74c3c', bgColor: 'bg-red-600', borderColor: 'border-red-700' },
  meetup: { color: '#34495e', bgColor: 'bg-slate-600', borderColor: 'border-slate-700' },
  mixed: { color: '#95a5a6', bgColor: 'bg-gray-500', borderColor: 'border-gray-600' },
  other: { color: '#95a5a6', bgColor: 'bg-gray-500', borderColor: 'border-gray-600' },
};

/**
 * Get cluster size class based on event count
 */
const getClusterSizeClass = (count: number): string => {
  if (count >= 20) return 'w-14 h-14 text-lg';
  if (count >= 10) return 'w-12 h-12 text-base';
  if (count >= 5) return 'w-10 h-10 text-sm';
  return 'w-8 h-8 text-xs';
};

/**
 * Format event count for display
 */
const formatEventCount = (count: number): string => {
  if (count >= 100) return '99+';
  return count.toString();
};

/**
 * Get cluster title for accessibility
 */
const getClusterTitle = (cluster: EventCluster): string => {
  if (!cluster.isCluster) {
    return cluster.events[0].title;
  }
  
  const { count, category } = cluster;
  const categoryName = category && category !== 'other' && category !== 'mixed' 
    ? category.charAt(0).toUpperCase() + category.slice(1) 
    : '';
  
  return `${count} events${categoryName ? ` (${categoryName})` : ''} in this area`;
};

export const ClusterMarker: React.FC<ClusterMarkerProps> = ({
  cluster,
  onClick,
  onHover,
  isSelected = false,
  className
}) => {
  const { isCluster, count, category = 'other' } = cluster;
  const config = categoryConfig[category as keyof typeof categoryConfig] || categoryConfig.other;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClick?.(cluster);
  };

  const handleMouseEnter = () => {
    onHover?.(cluster);
  };

  const handleMouseLeave = () => {
    onHover?.(null);
  };

  // Single event marker (simplified circle)
  if (!isCluster) {
    const event = cluster.events[0];
    
    return (
      <div
        className={clsx(
          'absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer',
          'transition-all duration-200 ease-in-out',
          'hover:scale-125 active:scale-110',
          isSelected && 'scale-125 z-20',
          className
        )}
        onClick={handleClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        title={`Click to view: ${event.title}`}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onClick?.(cluster);
          }
        }}
      >
        <div
          className={clsx(
            'w-5 h-5 rounded-full border-2 border-white shadow-lg',
            'hover:shadow-xl hover:border-gray-100',
            'active:shadow-md transition-shadow duration-150',
            isSelected && 'ring-2 ring-blue-400 ring-opacity-60 animate-pulse'
          )}
          style={{ backgroundColor: config.color }}
        />
        
        {/* Subtle pulse animation on hover */}
        <div
          className={clsx(
            'absolute inset-0 rounded-full opacity-0 transition-opacity duration-200',
            'hover:opacity-20 animate-ping'
          )}
          style={{ backgroundColor: config.color, animationDuration: '1.5s' }}
        />
      </div>
    );
  }

  // Cluster marker with event count
  return (
    <div
      className={clsx(
        'absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer',
        'transition-all duration-200 ease-in-out',
        'hover:scale-110 active:scale-95',
        isSelected && 'scale-125 z-20',
        className
      )}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      title={`Click to view: ${getClusterTitle(cluster)}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.(cluster);
        }
      }}
    >
      {/* Cluster circle with count */}
      <div
        className={clsx(
          'rounded-full border-3 border-white shadow-lg',
          'flex items-center justify-center',
          'font-semibold text-white',
          'hover:shadow-xl hover:border-gray-100',
          'active:shadow-md transition-shadow duration-150',
          config.bgColor,
          getClusterSizeClass(count),
          isSelected && 'ring-2 ring-blue-400 ring-opacity-60 animate-pulse'
        )}
      >
        {formatEventCount(count)}
      </div>
      
      {/* Enhanced pulse animation for large clusters */}
      {count >= 10 && (
        <div
          className={clsx(
            'absolute inset-0 rounded-full animate-ping opacity-30',
            config.bgColor
          )}
          style={{ animationDuration: '2s' }}
        />
      )}
      
      {/* Hover pulse for better feedback */}
      <div
        className={clsx(
          'absolute inset-0 rounded-full opacity-0 transition-opacity duration-200',
          'hover:opacity-20 animate-ping',
          config.bgColor
        )}
        style={{ animationDuration: '1.5s' }}
      />
    </div>
  );
};

/**
 * Marker for selected cluster with enhanced styling
 */
export const SelectedClusterMarker: React.FC<{
  cluster: EventCluster;
  onClose?: () => void;
}> = ({ cluster, onClose }) => {
  const config = categoryConfig[cluster.category as keyof typeof categoryConfig] || categoryConfig.other;
  
  return (
    <div className="absolute transform -translate-x-1/2 -translate-y-1/2 z-30">
      {/* Enhanced cluster marker */}
      <div
        className={clsx(
          'rounded-full border-4 border-white shadow-2xl',
          'flex items-center justify-center',
          'font-bold text-white scale-125',
          config.bgColor,
          getClusterSizeClass(cluster.count)
        )}
      >
        {formatEventCount(cluster.count)}
      </div>
      
      {/* Selection ring */}
      <div
        className="absolute inset-0 rounded-full ring-4 ring-blue-400 ring-opacity-60 animate-pulse"
        style={{ animationDuration: '1.5s' }}
      />
      
      {/* Close button for clusters */}
      {cluster.isCluster && onClose && (
        <button
          className={clsx(
            'absolute -top-2 -right-2 w-6 h-6',
            'bg-white rounded-full shadow-md',
            'flex items-center justify-center',
            'text-gray-600 hover:text-gray-800',
            'hover:bg-gray-50 transition-colors',
            'border border-gray-200'
          )}
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          title="Close cluster"
        >
          ×
        </button>
      )}
    </div>
  );
};

export default ClusterMarker;