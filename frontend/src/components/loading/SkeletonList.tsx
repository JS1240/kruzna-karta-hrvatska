/**
 * SkeletonList Component
 * 
 * List skeletons with staggered reveals and motion preference awareness.
 * Provides realistic loading states for various list layouts.
 */

import React from 'react';
import { StaggerContainer, StaggerItem } from '@/components/transitions';
import { SkeletonCard } from './SkeletonCard';
import type { SkeletonCardProps } from './SkeletonCard';

export interface SkeletonListProps {
  count?: number;
  variant?: SkeletonCardProps['variant'];
  staggerDelay?: number;
  className?: string;
  itemClassName?: string;
  style?: React.CSSProperties;
  columns?: number;
  gap?: string;
  showStagger?: boolean;
  skeletonProps?: Partial<SkeletonCardProps>;
}

/**
 * SkeletonList component with staggered animations
 */
export const SkeletonList: React.FC<SkeletonListProps> = ({
  count = 6,
  variant = 'event',
  staggerDelay = 80,
  className = '',
  itemClassName = '',
  style = {},
  columns = 1,
  gap = '1rem',
  showStagger = true,
  skeletonProps = {},
}) => {
  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap,
    ...style,
  };

  const listStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap,
    ...style,
  };

  const containerStyle = columns > 1 ? gridStyle : listStyle;

  if (!showStagger) {
    return (
      <div
        className={`skeleton-list ${className}`.trim()}
        style={containerStyle}
        role="feed"
        aria-label={`Loading ${count} items`}
      >
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className={itemClassName}>
            <SkeletonCard variant={variant} {...skeletonProps} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <StaggerContainer
      className={`skeleton-list ${className}`.trim()}
      style={containerStyle}
      staggerDelay={staggerDelay}
      animation="slideUp"
      duration={0.4}
      role="feed"
      aria-label={`Loading ${count} items`}
    >
      {Array.from({ length: count }).map((_, index) => (
        <StaggerItem key={index} id={`skeleton-${index}`} className={itemClassName}>
          <SkeletonCard variant={variant} {...skeletonProps} />
        </StaggerItem>
      ))}
    </StaggerContainer>
  );
};

/**
 * Preset skeleton lists
 */

// Event list skeleton
export const EventSkeletonList: React.FC<Omit<SkeletonListProps, 'variant'>> = (props) => (
  <SkeletonList
    variant="event"
    count={6}
    staggerDelay={100}
    {...props}
  />
);

// Featured events skeleton
export const FeaturedSkeletonList: React.FC<Omit<SkeletonListProps, 'variant'>> = (props) => (
  <SkeletonList
    variant="featured"
    count={3}
    staggerDelay={150}
    columns={1}
    {...props}
  />
);

// Grid skeleton
export const GridSkeletonList: React.FC<SkeletonListProps> = ({
  columns = 3,
  count = 9,
  staggerDelay = 60,
  ...props
}) => (
  <SkeletonList
    variant="grid"
    columns={columns}
    count={count}
    staggerDelay={staggerDelay}
    {...props}
  />
);

// List view skeleton
export const ListViewSkeleton: React.FC<Omit<SkeletonListProps, 'variant'>> = (props) => (
  <SkeletonList
    variant="list"
    count={8}
    staggerDelay={50}
    columns={1}
    {...props}
  />
);

// Card grid skeleton
export const CardGridSkeleton: React.FC<SkeletonListProps> = ({
  columns = 2,
  count = 6,
  staggerDelay = 80,
  ...props
}) => (
  <SkeletonList
    variant="event"
    columns={columns}
    count={count}
    staggerDelay={staggerDelay}
    {...props}
  />
);

// Hero section skeletons
export const HeroSkeletonList: React.FC<Omit<SkeletonListProps, 'variant'>> = (props) => (
  <SkeletonList
    variant="hero"
    count={1}
    showStagger={false}
    {...props}
  />
);

/**
 * Responsive skeleton list
 */
export interface ResponsiveSkeletonListProps extends Omit<SkeletonListProps, 'columns'> {
  breakpoints?: {
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

export const ResponsiveSkeletonList: React.FC<ResponsiveSkeletonListProps> = ({
  breakpoints = { sm: 1, md: 2, lg: 3, xl: 4 },
  className = '',
  ...props
}) => {
  const responsiveClasses = `
    grid grid-cols-${breakpoints.sm || 1}
    sm:grid-cols-${breakpoints.sm || 1}
    md:grid-cols-${breakpoints.md || 2}
    lg:grid-cols-${breakpoints.lg || 3}
    xl:grid-cols-${breakpoints.xl || 4}
  `.replace(/\s+/g, ' ').trim();

  return (
    <StaggerContainer
      className={`skeleton-list ${responsiveClasses} ${className}`.trim()}
      staggerDelay={props.staggerDelay || 80}
      animation="slideUp"
      duration={0.4}
      role="feed"
      aria-label={`Loading ${props.count || 6} items`}
    >
      {Array.from({ length: props.count || 6 }).map((_, index) => (
        <StaggerItem key={index} id={`skeleton-${index}`} className={props.itemClassName}>
          <SkeletonCard variant={props.variant} {...props.skeletonProps} />
        </StaggerItem>
      ))}
    </StaggerContainer>
  );
};

/**
 * Masonry skeleton list
 */
export const MasonrySkeletonList: React.FC<SkeletonListProps> = ({
  count = 8,
  staggerDelay = 100,
  className = '',
  itemClassName = '',
  ...props
}) => {
  // Generate random heights for masonry effect
  const heights = React.useMemo(() => {
    return Array.from({ length: count }).map(() => {
      const baseHeight = 250;
      const variation = Math.random() * 150;
      return Math.floor(baseHeight + variation);
    });
  }, [count]);

  return (
    <StaggerContainer
      className={`skeleton-masonry columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4 ${className}`.trim()}
      staggerDelay={staggerDelay}
      animation="slideUp"
      duration={0.6}
      role="feed"
      aria-label={`Loading ${count} items`}
    >
      {Array.from({ length: count }).map((_, index) => (
        <StaggerItem
          key={index}
          id={`masonry-skeleton-${index}`}
          className={`break-inside-avoid mb-4 ${itemClassName}`.trim()}
        >
          <div style={{ height: heights[index] }}>
            <SkeletonCard
              variant="grid"
              showImage={true}
              showDescription={true}
              lines={Math.floor(Math.random() * 3) + 1}
              {...props.skeletonProps}
            />
          </div>
        </StaggerItem>
      ))}
    </StaggerContainer>
  );
};

/**
 * Skeleton table rows
 */
export interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  staggerDelay?: number;
  className?: string;
}

export const SkeletonTable: React.FC<SkeletonTableProps> = ({
  rows = 5,
  columns = 4,
  showHeader = true,
  staggerDelay = 60,
  className = '',
}) => {
  return (
    <div className={`skeleton-table w-full ${className}`.trim()} role="table" aria-label="Loading table">
      {/* Header skeleton */}
      {showHeader && (
        <div className="grid gap-4 p-4 bg-gray-50 border-b border-gray-200" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, index) => (
            <div key={index} className="h-4 bg-gray-300 rounded animate-pulse" />
          ))}
        </div>
      )}

      {/* Rows skeleton */}
      <StaggerContainer staggerDelay={staggerDelay} animation="slideUp" duration={0.3}>
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <StaggerItem key={rowIndex} id={`table-row-${rowIndex}`}>
            <div 
              className="grid gap-4 p-4 border-b border-gray-100"
              style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
            >
              {Array.from({ length: columns }).map((_, colIndex) => (
                <div key={colIndex} className="h-4 bg-gray-200 rounded animate-pulse" />
              ))}
            </div>
          </StaggerItem>
        ))}
      </StaggerContainer>
    </div>
  );
};

export default SkeletonList;