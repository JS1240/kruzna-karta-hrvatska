/**
 * SkeletonCard Component
 * 
 * Specialized skeleton loaders for different card types.
 * Provides branded, accessible loading placeholders.
 */

import React from 'react';
import { useReducedMotion } from '@/hooks/useReducedMotion';

export interface SkeletonCardProps {
  variant?: 'event' | 'featured' | 'list' | 'grid' | 'hero';
  showImage?: boolean;
  showBadge?: boolean;
  showPrice?: boolean;
  showDescription?: boolean;
  lines?: number;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Base skeleton shimmer animation
 */
const SkeletonShimmer: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { getClassName } = useReducedMotion();

  const shimmerClasses = getClassName(
    'skeleton-shimmer bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded',
    // Motion classes
    'animate-pulse motion-safe:bg-gradient-to-r motion-safe:from-gray-200 motion-safe:via-gray-100 motion-safe:to-gray-200',
    // Reduced motion classes
    'bg-gray-200'
  );

  return <div className={`${shimmerClasses} ${className}`.trim()} />;
};

/**
 * Event card skeleton
 */
const EventCardSkeleton: React.FC<SkeletonCardProps> = ({
  showImage = true,
  showBadge = true,
  showPrice = true,
  showDescription = true,
  lines = 3,
  className = '',
  style = {},
}) => {
  return (
    <div
      className={`skeleton-card bg-white rounded-lg border border-gray-200 p-4 space-y-4 ${className}`.trim()}
      style={style}
      role="article"
      aria-label="Loading event"
    >
      {/* Image skeleton */}
      {showImage && (
        <div className="relative">
          <SkeletonShimmer className="w-full h-48" />
          
          {/* Badge skeleton */}
          {showBadge && (
            <div className="absolute top-3 left-3">
              <SkeletonShimmer className="w-20 h-6" />
            </div>
          )}
          
          {/* Price skeleton */}
          {showPrice && (
            <div className="absolute bottom-3 right-3">
              <SkeletonShimmer className="w-16 h-7 rounded-full" />
            </div>
          )}
        </div>
      )}

      {/* Content skeleton */}
      <div className="space-y-3">
        {/* Title skeleton */}
        <div className="space-y-2">
          <SkeletonShimmer className="w-3/4 h-6" />
          <SkeletonShimmer className="w-1/2 h-6" />
        </div>

        {/* Description skeleton */}
        {showDescription && (
          <div className="space-y-2">
            {Array.from({ length: lines }).map((_, index) => (
              <SkeletonShimmer
                key={index}
                className={`h-4 ${
                  index === lines - 1 ? 'w-2/3' : 'w-full'
                }`}
              />
            ))}
          </div>
        )}

        {/* Footer skeleton */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center space-x-2">
            <SkeletonShimmer className="w-4 h-4 rounded-full" />
            <SkeletonShimmer className="w-24 h-4" />
          </div>
          <SkeletonShimmer className="w-20 h-4" />
        </div>
      </div>
    </div>
  );
};

/**
 * Featured event card skeleton
 */
const FeaturedCardSkeleton: React.FC<SkeletonCardProps> = ({
  showImage = true,
  showDescription = true,
  lines = 4,
  className = '',
  style = {},
}) => {
  return (
    <div
      className={`skeleton-featured-card bg-white rounded-xl shadow-lg overflow-hidden ${className}`.trim()}
      style={style}
      role="article"
      aria-label="Loading featured event"
    >
      {/* Large image skeleton */}
      {showImage && (
        <div className="relative">
          <SkeletonShimmer className="w-full h-64" />
          
          {/* Overlay content skeleton */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-6">
            <div className="space-y-3">
              <SkeletonShimmer className="w-2/3 h-8 bg-gray-300" />
              <SkeletonShimmer className="w-1/3 h-6 bg-gray-300" />
            </div>
          </div>
        </div>
      )}

      {/* Content skeleton */}
      <div className="p-6 space-y-4">
        {showDescription && (
          <div className="space-y-2">
            {Array.from({ length: lines }).map((_, index) => (
              <SkeletonShimmer
                key={index}
                className={`h-4 ${
                  index === lines - 1 ? 'w-1/2' : 'w-full'
                }`}
              />
            ))}
          </div>
        )}

        {/* CTA skeleton */}
        <div className="flex items-center justify-between pt-4">
          <SkeletonShimmer className="w-32 h-10 rounded-md" />
          <div className="flex items-center space-x-4">
            <SkeletonShimmer className="w-6 h-6 rounded-full" />
            <SkeletonShimmer className="w-6 h-6 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * List item skeleton
 */
const ListCardSkeleton: React.FC<SkeletonCardProps> = ({
  showImage = true,
  showPrice = true,
  className = '',
  style = {},
}) => {
  return (
    <div
      className={`skeleton-list-card flex items-center space-x-4 p-4 bg-white rounded-lg border border-gray-200 ${className}`.trim()}
      style={style}
      role="article"
      aria-label="Loading event"
    >
      {/* Thumbnail skeleton */}
      {showImage && (
        <SkeletonShimmer className="w-16 h-16 rounded-lg flex-shrink-0" />
      )}

      {/* Content skeleton */}
      <div className="flex-1 space-y-2">
        <SkeletonShimmer className="w-3/4 h-5" />
        <SkeletonShimmer className="w-1/2 h-4" />
        <div className="flex items-center space-x-2">
          <SkeletonShimmer className="w-4 h-4 rounded-full" />
          <SkeletonShimmer className="w-20 h-4" />
        </div>
      </div>

      {/* Price skeleton */}
      {showPrice && (
        <div className="flex-shrink-0">
          <SkeletonShimmer className="w-16 h-6 rounded-full" />
        </div>
      )}
    </div>
  );
};

/**
 * Grid item skeleton
 */
const GridCardSkeleton: React.FC<SkeletonCardProps> = ({
  showImage = true,
  showDescription = false,
  lines = 2,
  className = '',
  style = {},
}) => {
  return (
    <div
      className={`skeleton-grid-card bg-white rounded-lg border border-gray-200 overflow-hidden ${className}`.trim()}
      style={style}
      role="article"
      aria-label="Loading event"
    >
      {/* Image skeleton */}
      {showImage && <SkeletonShimmer className="w-full h-40" />}

      {/* Content skeleton */}
      <div className="p-4 space-y-3">
        <SkeletonShimmer className="w-full h-5" />
        <SkeletonShimmer className="w-2/3 h-4" />
        
        {showDescription && (
          <div className="space-y-2">
            {Array.from({ length: lines }).map((_, index) => (
              <SkeletonShimmer
                key={index}
                className={`h-3 ${
                  index === lines - 1 ? 'w-1/2' : 'w-full'
                }`}
              />
            ))}
          </div>
        )}

        {/* Footer skeleton */}
        <div className="flex items-center justify-between pt-2">
          <SkeletonShimmer className="w-16 h-4" />
          <SkeletonShimmer className="w-12 h-6 rounded-full" />
        </div>
      </div>
    </div>
  );
};

/**
 * Hero section skeleton
 */
const HeroCardSkeleton: React.FC<SkeletonCardProps> = ({
  className = '',
  style = {},
}) => {
  return (
    <div
      className={`skeleton-hero-card relative w-full h-96 rounded-2xl overflow-hidden ${className}`.trim()}
      style={style}
      role="banner"
      aria-label="Loading hero content"
    >
      {/* Background skeleton */}
      <SkeletonShimmer className="absolute inset-0" />

      {/* Content overlay skeleton */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end">
        <div className="p-8 space-y-4 w-full">
          <SkeletonShimmer className="w-1/2 h-12 bg-gray-300" />
          <SkeletonShimmer className="w-3/4 h-6 bg-gray-300" />
          <SkeletonShimmer className="w-1/3 h-6 bg-gray-300" />
          
          <div className="flex items-center space-x-4 pt-4">
            <SkeletonShimmer className="w-32 h-12 rounded-md bg-gray-300" />
            <SkeletonShimmer className="w-24 h-10 rounded-md bg-gray-300" />
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Main SkeletonCard component
 */
export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  variant = 'event',
  ...props
}) => {
  switch (variant) {
    case 'featured':
      return <FeaturedCardSkeleton {...props} />;
    case 'list':
      return <ListCardSkeleton {...props} />;
    case 'grid':
      return <GridCardSkeleton {...props} />;
    case 'hero':
      return <HeroCardSkeleton {...props} />;
    case 'event':
    default:
      return <EventCardSkeleton {...props} />;
  }
};

/**
 * Preset skeleton components
 */
export const EventSkeletonCard: React.FC<Omit<SkeletonCardProps, 'variant'>> = (props) => (
  <SkeletonCard variant="event" {...props} />
);

export const FeaturedSkeletonCard: React.FC<Omit<SkeletonCardProps, 'variant'>> = (props) => (
  <SkeletonCard variant="featured" {...props} />
);

export const ListSkeletonCard: React.FC<Omit<SkeletonCardProps, 'variant'>> = (props) => (
  <SkeletonCard variant="list" {...props} />
);

export const GridSkeletonCard: React.FC<Omit<SkeletonCardProps, 'variant'>> = (props) => (
  <SkeletonCard variant="grid" {...props} />
);

export const HeroSkeletonCard: React.FC<Omit<SkeletonCardProps, 'variant'>> = (props) => (
  <SkeletonCard variant="hero" {...props} />
);

export default SkeletonCard;