/**
 * TouchCarousel Component
 * 
 * Touch-optimized carousel with swipe gestures, momentum scrolling,
 * snap-to-slide, and comprehensive accessibility features.
 */

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useSwipe } from '@/hooks/useTouch';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { 
  detectTouchDevice, 
  getTouchOptimizedClasses, 
  calculateMomentumScroll,
  smoothScrollTo 
} from '@/utils/touchUtils';
import { cn } from '@/lib/utils';

export interface TouchCarouselProps {
  children: React.ReactNode[];
  autoPlay?: boolean;
  autoPlayInterval?: number;
  infiniteLoop?: boolean;
  showIndicators?: boolean;
  showArrows?: boolean;
  slideWidth?: string | number;
  slidesToShow?: number;
  slidesToScroll?: number;
  gap?: number;
  snapToSlide?: boolean;
  momentumScroll?: boolean;
  className?: string;
  slideClassName?: string;
  indicatorClassName?: string;
  arrowClassName?: string;
  onSlideChange?: (index: number) => void;
  onSlideClick?: (index: number) => void;
  centerMode?: boolean;
  variableWidth?: boolean;
}

/**
 * Touch Carousel Component
 */
export const TouchCarousel: React.FC<TouchCarouselProps> = ({
  children,
  autoPlay = false,
  autoPlayInterval = 5000,
  infiniteLoop = false,
  showIndicators = true,
  showArrows = true,
  slideWidth = 'auto',
  slidesToShow = 1,
  slidesToScroll = 1,
  gap = 16,
  snapToSlide = true,
  momentumScroll = true,
  className = '',
  slideClassName = '',
  indicatorClassName = '',
  arrowClassName = '',
  onSlideChange,
  onSlideClick,
  centerMode = false,
  variableWidth = false,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const autoPlayRef = useRef<NodeJS.Timeout | null>(null);

  const {
    prefersReducedMotion,
    shouldDisableAnimation,
    getClassName,
    cssCustomProperties,
  } = useReducedMotion();

  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  // Calculate total slides
  const totalSlides = children.length;
  const maxIndex = infiniteLoop ? totalSlides : Math.max(0, totalSlides - slidesToShow);

  // Handle swipe gestures
  const { handlers: swipeHandlers } = useSwipe(
    (gesture) => {
      if (gesture.direction === 'left') {
        goToNext();
      } else if (gesture.direction === 'right') {
        goToPrevious();
      }
    },
    {
      threshold: 30,
      hapticFeedback: true,
      preventScroll: true,
    }
  );

  // Navigation functions
  const goToSlide = useCallback((index: number, smooth: boolean = true) => {
    let targetIndex = index;
    
    if (infiniteLoop) {
      targetIndex = ((index % totalSlides) + totalSlides) % totalSlides;
    } else {
      targetIndex = Math.max(0, Math.min(index, maxIndex));
    }

    setCurrentIndex(targetIndex);
    
    if (trackRef.current) {
      const slideWidth = trackRef.current.scrollWidth / totalSlides;
      const scrollPosition = targetIndex * slideWidth;
      
      if (smooth && !shouldDisableAnimation) {
        smoothScrollTo(trackRef.current, {
          left: scrollPosition,
          behavior: 'smooth',
        });
      } else {
        trackRef.current.scrollLeft = scrollPosition;
      }
    }

    onSlideChange?.(targetIndex);
  }, [totalSlides, maxIndex, infiniteLoop, shouldDisableAnimation, onSlideChange]);

  const goToNext = useCallback(() => {
    const nextIndex = infiniteLoop 
      ? (currentIndex + slidesToScroll) % totalSlides
      : Math.min(currentIndex + slidesToScroll, maxIndex);
    goToSlide(nextIndex);
  }, [currentIndex, slidesToScroll, totalSlides, maxIndex, infiniteLoop, goToSlide]);

  const goToPrevious = useCallback(() => {
    const prevIndex = infiniteLoop
      ? ((currentIndex - slidesToScroll) + totalSlides) % totalSlides
      : Math.max(currentIndex - slidesToScroll, 0);
    goToSlide(prevIndex);
  }, [currentIndex, slidesToScroll, totalSlides, infiniteLoop, goToSlide]);

  // Auto-play functionality
  useEffect(() => {
    if (autoPlay && !isDragging && !shouldDisableAnimation) {
      autoPlayRef.current = setInterval(() => {
        goToNext();
      }, autoPlayInterval);

      return () => {
        if (autoPlayRef.current) {
          clearInterval(autoPlayRef.current);
        }
      };
    }
  }, [autoPlay, autoPlayInterval, isDragging, shouldDisableAnimation, goToNext]);

  // Handle track scroll for snap-to-slide
  const handleScroll = useCallback(() => {
    if (!snapToSlide || !trackRef.current || isDragging) return;

    const track = trackRef.current;
    const slideWidth = track.scrollWidth / totalSlides;
    const scrollPosition = track.scrollLeft;
    const nearestIndex = Math.round(scrollPosition / slideWidth);

    if (nearestIndex !== currentIndex) {
      setCurrentIndex(nearestIndex);
      onSlideChange?.(nearestIndex);
    }
  }, [snapToSlide, totalSlides, currentIndex, isDragging, onSlideChange]);

  // Scroll event listener
  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;

    track.addEventListener('scroll', handleScroll, { passive: true });
    return () => track.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  // Touch interaction handlers
  const handleTouchStart = useCallback(() => {
    setIsDragging(true);
    setIsScrolling(true);
    
    // Pause auto-play during interaction
    if (autoPlayRef.current) {
      clearInterval(autoPlayRef.current);
    }
  }, []);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
    setTimeout(() => setIsScrolling(false), 100);
  }, []);

  // Slide click handler
  const handleSlideClick = useCallback((index: number) => {
    if (!isScrolling) {
      onSlideClick?.(index);
    }
  }, [isScrolling, onSlideClick]);

  // Calculate slide styles
  const slideStyles = useMemo(() => {
    if (variableWidth) {
      return {
        flexShrink: 0,
        width: slideWidth,
        marginRight: `${gap}px`,
      };
    }

    const baseWidth = `calc(${100 / slidesToShow}% - ${gap * (slidesToShow - 1) / slidesToShow}px)`;
    
    return {
      flexShrink: 0,
      width: baseWidth,
      marginRight: `${gap}px`,
    };
  }, [slideWidth, slidesToShow, gap, variableWidth]);

  // Component classes
  const containerClasses = getClassName(
    'relative w-full overflow-hidden',
    // Motion classes
    'transition-opacity duration-300',
    // Reduced motion classes
    ''
  );

  const trackClasses = getClassName(
    'flex overflow-x-auto scrollbar-hide',
    // Motion classes
    snapToSlide ? 'scroll-smooth snap-x snap-mandatory' : '',
    // Reduced motion classes
    ''
  );

  const slideClasses = getClassName(
    'snap-start',
    // Motion classes
    'transition-transform duration-200 hover:scale-[1.02]',
    // Reduced motion classes
    ''
  );

  return (
    <div 
      className={cn(containerClasses, className)}
      style={cssCustomProperties}
      aria-label="Carousel"
      role="region"
    >
      {/* Main track */}
      <div
        ref={containerRef}
        className="relative"
        {...swipeHandlers}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <div
          ref={trackRef}
          className={cn(trackClasses)}
          style={{
            scrollSnapType: snapToSlide ? 'x mandatory' : 'none',
            scrollBehavior: shouldDisableAnimation ? 'auto' : 'smooth',
          }}
        >
          {children.map((child, index) => (
            <div
              key={index}
              className={cn(slideClasses, slideClassName)}
              style={slideStyles}
              onClick={() => handleSlideClick(index)}
              aria-label={`Slide ${index + 1} of ${totalSlides}`}
            >
              {child}
            </div>
          ))}
        </div>
      </div>

      {/* Navigation arrows */}
      {showArrows && totalSlides > slidesToShow && (
        <>
          <button
            onClick={goToPrevious}
            disabled={!infiniteLoop && currentIndex === 0}
            className={cn(
              'absolute left-2 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white shadow-lg rounded-full p-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed z-10',
              touchClasses.touchTarget,
              touchClasses.interactive,
              arrowClassName
            )}
            aria-label="Previous slide"
          >
            <ChevronLeft className="h-6 w-6 text-brand-primary" />
          </button>

          <button
            onClick={goToNext}
            disabled={!infiniteLoop && currentIndex >= maxIndex}
            className={cn(
              'absolute right-2 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white shadow-lg rounded-full p-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed z-10',
              touchClasses.touchTarget,
              touchClasses.interactive,
              arrowClassName
            )}
            aria-label="Next slide"
          >
            <ChevronRight className="h-6 w-6 text-brand-primary" />
          </button>
        </>
      )}

      {/* Indicators */}
      {showIndicators && totalSlides > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          {Array.from({ length: Math.ceil(totalSlides / slidesToShow) }).map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index * slidesToShow)}
              className={cn(
                'w-2 h-2 rounded-full transition-all duration-200',
                touchClasses.interactive,
                index === Math.floor(currentIndex / slidesToShow)
                  ? 'bg-brand-primary w-6'
                  : 'bg-gray-300 hover:bg-gray-400',
                indicatorClassName
              )}
              aria-label={`Go to slide group ${index + 1}`}
            />
          ))}
        </div>
      )}

      {/* Screen reader announcements */}
      <div 
        aria-live="polite" 
        aria-atomic="true" 
        className="sr-only"
      >
        Slide {currentIndex + 1} of {totalSlides}
      </div>
    </div>
  );
};

/**
 * Touch Card Carousel - Specialized for event cards
 */
export interface TouchCardCarouselProps extends Omit<TouchCarouselProps, 'children'> {
  cards: React.ReactNode[];
  cardWidth?: number;
  maxCards?: number;
}

export const TouchCardCarousel: React.FC<TouchCardCarouselProps> = ({
  cards,
  cardWidth = 300,
  maxCards = 5,
  ...props
}) => {
  const device = detectTouchDevice();
  
  // Responsive slides to show
  const slidesToShow = useMemo(() => {
    if (device.isMobile) return 1.2;
    if (device.isTablet) return 2.5;
    return Math.min(3.5, maxCards);
  }, [device, maxCards]);

  return (
    <TouchCarousel
      slidesToShow={slidesToShow}
      slidesToScroll={1}
      gap={16}
      showArrows={!device.isMobile}
      showIndicators={device.isMobile}
      snapToSlide={true}
      momentumScroll={true}
      slideWidth={`${cardWidth}px`}
      variableWidth={false}
      {...props}
    >
      {cards}
    </TouchCarousel>
  );
};

/**
 * Touch Image Gallery - Specialized for image viewing
 */
export interface TouchImageGalleryProps extends Omit<TouchCarouselProps, 'children'> {
  images: Array<{
    src: string;
    alt: string;
    caption?: string;
  }>;
  thumbnails?: boolean;
}

export const TouchImageGallery: React.FC<TouchImageGalleryProps> = ({
  images,
  thumbnails = true,
  ...props
}) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  return (
    <div className="space-y-4">
      <TouchCarousel
        slidesToShow={1}
        slidesToScroll={1}
        infiniteLoop={true}
        showArrows={true}
        showIndicators={!thumbnails}
        onSlideChange={setSelectedIndex}
        {...props}
      >
        {images.map((image, index) => (
          <div key={index} className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={image.src}
              alt={image.alt}
              className="w-full h-full object-cover"
              loading={index === 0 ? 'eager' : 'lazy'}
            />
            {image.caption && (
              <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white p-4">
                <p className="text-sm">{image.caption}</p>
              </div>
            )}
          </div>
        ))}
      </TouchCarousel>

      {thumbnails && images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {images.map((image, index) => (
            <button
              key={index}
              onClick={() => setSelectedIndex(index)}
              className={cn(
                'flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-all duration-200',
                index === selectedIndex
                  ? 'border-brand-primary'
                  : 'border-transparent hover:border-gray-300'
              )}
            >
              <img
                src={image.src}
                alt={`Thumbnail ${index + 1}`}
                className="w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default TouchCarousel;