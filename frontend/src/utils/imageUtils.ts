// Image utility functions for hero carousel and event images

interface ImagePreloadResult {
  success: boolean;
  url: string;
  error?: string;
}

// Preload an image and return a promise
export const preloadImage = (url: string): Promise<ImagePreloadResult> => {
  return new Promise((resolve) => {
    const img = new Image();
    
    img.onload = () => {
      resolve({ success: true, url });
    };
    
    img.onerror = () => {
      resolve({ 
        success: false, 
        url, 
        error: 'Failed to load image' 
      });
    };
    
    // Set a timeout for slow loading images
    const timeout = setTimeout(() => {
      resolve({ 
        success: false, 
        url, 
        error: 'Image load timeout' 
      });
    }, 5000);
    
    img.onload = () => {
      clearTimeout(timeout);
      resolve({ success: true, url });
    };
    
    img.src = url;
  });
};

// Preload multiple images
export const preloadImages = async (urls: string[]): Promise<ImagePreloadResult[]> => {
  const promises = urls.map(url => preloadImage(url));
  return Promise.all(promises);
};

// Get fallback image based on event location or category
export const getFallbackImage = (location?: string, category?: string): string => {
  // Location-based fallbacks (using existing images)
  if (location) {
    const loc = location.toLowerCase();
    if (loc.includes('zagreb')) return '/event-images/conference.jpg';
    if (loc.includes('split')) return '/event-images/meetup.jpg';
    if (loc.includes('dubrovnik')) return '/event-images/party.jpg';
    if (loc.includes('rijeka')) return '/event-images/conference.jpg';
    if (loc.includes('pula')) return '/event-images/party.jpg';
    if (loc.includes('zadar')) return '/event-images/concert.jpg';
  }
  
  // Category-based fallbacks
  if (category) {
    const cat = category.toLowerCase();
    if (cat.includes('music') || cat.includes('concert')) return '/event-images/concert.jpg';
    if (cat.includes('sport') || cat.includes('fitness')) return '/event-images/workout.jpg';
    if (cat.includes('business') || cat.includes('conference')) return '/event-images/conference.jpg';
    if (cat.includes('party') || cat.includes('festival')) return '/event-images/party.jpg';
    if (cat.includes('tech') || cat.includes('meetup')) return '/event-images/meetup.jpg';
  }
  
  // Default fallback
  return '/event-images/concert.jpg';
};

// Check if URL is a valid image URL
export const isValidImageUrl = (url: string): boolean => {
  if (!url || typeof url !== 'string') return false;
  
  // Check for common image extensions
  const imageExtensions = /\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$/i;
  
  // Check for valid URL format
  try {
    new URL(url);
    return imageExtensions.test(url) || url.includes('image') || url.includes('photo');
  } catch {
    return false;
  }
};

// Optimize image URL for different screen sizes
export const getOptimizedImageUrl = (url: string, size: 'small' | 'medium' | 'large' = 'medium'): string => {
  if (!url) return getFallbackImage();
  
  // If it's already a local fallback image, return as-is
  if (url.startsWith('/event-images/')) return url;
  
  // For external URLs, we could add query parameters for optimization
  // This depends on the image service being used
  
  // For now, return the original URL
  // In the future, you could implement:
  // - Cloudinary optimization: `${url}?w=400&h=300&c=fill`
  // - ImageKit optimization: `${url}?tr=w-400,h-300,c-maintain_ratio`
  
  return url;
};

// Create a CSS-compatible background image URL
export const createBackgroundImageUrl = (url: string): string => {
  if (!url) return `url(${getFallbackImage()})`;
  return `url("${url}")`;
};

// Handle image loading errors by providing fallback
export const handleImageError = (
  event: React.SyntheticEvent<HTMLImageElement>, 
  fallbackUrl?: string,
  location?: string,
  category?: string
): void => {
  const img = event.currentTarget;
  const fallback = fallbackUrl || getFallbackImage(location, category);
  
  // Prevent infinite error loops
  if (img.src !== fallback) {
    img.src = fallback;
  }
};

// Generate a placeholder data URL for loading states
export const generatePlaceholderImage = (width: number = 400, height: number = 300, color: string = '#f3f4f6'): string => {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';
  
  // Fill with background color
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, width, height);
  
  // Add loading text
  ctx.fillStyle = '#9ca3af';
  ctx.font = '16px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('Loading...', width / 2, height / 2);
  
  return canvas.toDataURL();
};

// Image loading state management
export interface ImageLoadState {
  loading: boolean;
  error: boolean;
  loaded: boolean;
}