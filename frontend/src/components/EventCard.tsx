import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Heart, Calendar, MapPin, ExternalLink, Share2, Bookmark } from "lucide-react";
import ShareButton from "./ShareButton";
import { toast } from "@/hooks/use-toast";
import { handleImageError, getFallbackImage } from "@/utils/imageUtils";
import { SlideInCard } from "@/components/transitions";
import { LoadingTransition, EventSkeletonCard } from "@/components/loading";
import { SwipeActions, useTouchButton, detectTouchDevice, getTouchOptimizedClasses } from "@/components/mobile";

interface EventCardProps {
  id: string;
  title: string;
  image: string;
  date: string;
  location: string;
  category?: string;
  price?: string;
  description?: string;
  isFavorite?: boolean;
  onFavoriteToggle?: (id: string) => void;
  className?: string;
  // Loading transition props
  isLoading?: boolean;
  showAnimation?: boolean;
  animationDelay?: number;
}

const EventCard: React.FC<EventCardProps> = ({
  id,
  title,
  image,
  date,
  location,
  category,
  price,
  description = '',
  isFavorite = false,
  onFavoriteToggle,
  className = '',
  isLoading = false,
  showAnimation = true,
  animationDelay = 0,
}) => {
  const navigate = useNavigate();
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Touch device detection and styling
  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  const handleClick = () => {
    navigate(`/events/${id}`);
  };

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onFavoriteToggle) {
      onFavoriteToggle(id);
      toast({
        title: isFavorite ? "Removed from favorites" : "Added to favorites",
        description: isFavorite 
          ? `${title} has been removed from your favorites`
          : `${title} has been added to your favorites`,
      });
    }
  };

  const handleShareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  // Touch-specific handlers
  const handleSwipeShare = () => {
    // Share functionality
    if (navigator.share) {
      navigator.share({
        title,
        text: description,
        url: `${window.location.origin}/events/${id}`,
      });
    } else {
      // Fallback to clipboard
      navigator.clipboard.writeText(`${window.location.origin}/events/${id}`);
      toast({
        title: "Link copied",
        description: "Event link copied to clipboard",
      });
    }
  };

  const handleSwipeFavorite = () => {
    if (onFavoriteToggle) {
      onFavoriteToggle(id);
      toast({
        title: isFavorite ? "Removed from favorites" : "Added to favorites",
        description: isFavorite 
          ? `${title} has been removed from your favorites`
          : `${title} has been added to your favorites`,
      });
    }
  };

  // Define swipe actions for mobile
  const leftSwipeActions = [
    {
      id: 'share',
      label: 'Share',
      icon: Share2,
      color: 'blue' as const,
      onAction: handleSwipeShare,
    },
  ];

  const rightSwipeActions = onFavoriteToggle ? [
    {
      id: 'favorite',
      label: isFavorite ? 'Remove from favorites' : 'Add to favorites',
      icon: Heart,
      color: 'red' as const,
      onAction: handleSwipeFavorite,
    },
  ] : [];

  // Touch button for card tap
  const { handlers: cardTouchHandlers } = useTouchButton(handleClick, {
    hapticFeedback: true,
  });

  const handleImageLoadError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    setImageError(true);
    handleImageError(e, undefined, location, category);
  };

  const getImageSrc = () => {
    if (imageError || !image) {
      return getFallbackImage(location, category);
    }
    return image;
  };

  const getCategoryColor = (cat?: string) => {
    switch (cat?.toLowerCase()) {
      case 'concert': return 'bg-pink-100 text-pink-800';
      case 'festival': return 'bg-purple-100 text-purple-800';
      case 'party': return 'bg-orange-100 text-orange-800';
      case 'conference': return 'bg-blue-100 text-blue-800';
      case 'workout': return 'bg-green-100 text-green-800';
      case 'meetup': return 'bg-teal-100 text-teal-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Create the card content
  const cardContent = (
    <SwipeActions
      leftActions={leftSwipeActions}
      rightActions={rightSwipeActions}
      threshold={60}
      className={className}
    >
      <div
        className={`group relative bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden cursor-pointer transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${touchClasses.interactive}`}
        onClick={handleClick}
        tabIndex={0}
        role="button"
        aria-label={`View details for ${title}`}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") handleClick();
        }}
        {...cardTouchHandlers}
      >
      {/* Image Container */}
      <div className="relative h-48 overflow-hidden">
        <img
          src={getImageSrc()}
          alt={title}
          className={`w-full h-full object-cover transition-all duration-300 group-hover:scale-105 ${
            isImageLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onLoad={() => setIsImageLoaded(true)}
          onError={handleImageLoadError}
          loading="lazy"
        />
        {!isImageLoaded && (
          <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
            <div className="w-12 h-12 border-4 border-gray-300 border-t-navy-blue rounded-full animate-spin"></div>
          </div>
        )}
        
        {/* Image quality indicator for scraped images */}
        {!imageError && image && !image.startsWith('/event-images/') && (
          <div className="absolute bottom-2 left-2">
            <Badge variant="accent-cream" className="bg-accent-cream/90 text-xs text-brand-black border-accent-gold">
              Live
            </Badge>
          </div>
        )}
        
        {/* Overlay Actions */}
        <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div onClick={handleShareClick}>
            <ShareButton
              title={title}
              description={description}
              url={`${window.location.origin}/events/${id}`}
              variant="ghost"
              size="icon"
              className="bg-white/90 hover:bg-white backdrop-blur-sm shadow-sm h-8 w-8"
            />
          </div>
          {onFavoriteToggle && (
            <Button
              variant="ghost"
              size="icon"
              className="bg-white/90 hover:bg-white backdrop-blur-sm shadow-sm h-8 w-8"
              onClick={handleFavoriteClick}
            >
              <Heart 
                className={`h-4 w-4 transition-colors ${
                  isFavorite 
                    ? 'fill-red-500 text-red-500' 
                    : 'text-gray-600 hover:text-red-500'
                }`} 
              />
            </Button>
          )}
        </div>

        {/* Category Badge */}
        {category && (
          <div className="absolute top-3 left-3">
            <Badge className={`text-xs ${getCategoryColor(category)}`}>
              {category}
            </Badge>
          </div>
        )}

        {/* Price Badge */}
        {price && (
          <div className="absolute bottom-3 right-3">
            <Badge variant="accent-gold" className="bg-accent-gold/95 text-brand-black font-semibold border-none">
              {price}
            </Badge>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-bold text-lg text-navy-blue mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
          {title}
        </h3>
        
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-navy-blue flex-shrink-0" />
            <span className="truncate">{date}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-navy-blue flex-shrink-0" />
            <span className="truncate">{location}</span>
          </div>
        </div>

        {description && (
          <p className="text-sm text-gray-500 mt-3 line-clamp-2">
            {description}
          </p>
        )}

        {/* View Details Button */}
        <div className="mt-4 flex items-center justify-between">
          <span className="text-sm text-navy-blue font-medium group-hover:text-blue-600 transition-colors">
            View Details
          </span>
          <ExternalLink className="h-4 w-4 text-navy-blue group-hover:text-blue-600 transition-colors" />
        </div>
      </div>
    </div>
    </SwipeActions>
  );

  // Create skeleton for loading state
  const skeleton = (
    <EventSkeletonCard
      showImage={true}
      showBadge={!!category}
      showPrice={!!price}
      showDescription={!!description}
      className={className}
    />
  );

  // Wrap with loading transition
  const contentWithLoadingTransition = (
    <LoadingTransition
      isLoading={isLoading}
      skeleton={skeleton}
      duration={0.5}
      delay={150}
      crossfade={true}
    >
      {cardContent}
    </LoadingTransition>
  );

  // Wrap with scroll animation if enabled
  if (showAnimation) {
    return (
      <SlideInCard
        direction="up"
        distance={30}
        duration={0.5}
        delay={animationDelay}
        threshold={0.2}
        rootMargin="50px"
        easing="cubic-bezier(0.25, 0.46, 0.45, 0.94)"
      >
        {contentWithLoadingTransition}
      </SlideInCard>
    );
  }

  return contentWithLoadingTransition;
};

export default EventCard;

// Add CSS classes for line-clamp (add to your global CSS)
// .line-clamp-2 {
//   display: -webkit-box;
//   -webkit-line-clamp: 2;
//   -webkit-box-orient: vertical;
//   overflow: hidden;
// }
