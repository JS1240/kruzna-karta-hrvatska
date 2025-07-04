import React from "react";
import { MapPin } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const PageLoader = () => {
  const { t } = useLanguage();
  const { 
    prefersReducedMotion, 
    getClassName, 
    cssCustomProperties 
  } = useReducedMotion();

  // Generate motion-aware class names
  const containerClasses = getClassName(
    "fixed inset-0 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md z-50 flex items-center justify-center transition-colors",
    // Motion classes - applied when motion is preferred
    "animate-in fade-in duration-300",
    // Reduced motion classes - applied when motion is reduced
    "opacity-100"
  );

  const spinnerClasses = getClassName(
    "w-16 h-16 border-4 border-red-200 border-t-red-500 rounded-full",
    // Motion classes
    "motion-enhanced-spin", // Uses Tailwind custom utility
    // Reduced motion classes
    "border-red-300 border-t-red-500" // Static appearance for reduced motion
  );

  const iconClasses = getClassName(
    "w-6 h-6 text-red-500",
    // Motion classes
    "animate-pulse",
    // Reduced motion classes
    "opacity-90" // Subtle static emphasis
  );

  const titleClasses = getClassName(
    "text-lg font-semibold text-gray-700 dark:text-gray-200 transition-colors",
    // Motion classes
    "animate-pulse",
    // Reduced motion classes
    "opacity-100"
  );

  const progressBarClasses = getClassName(
    "h-full bg-gradient-to-r from-red-400 via-red-500 to-red-600 rounded-full transform origin-left w-3/4",
    // Motion classes
    "animate-pulse transition-all duration-1000 ease-out",
    // Reduced motion classes
    "opacity-90"
  );

  return (
    <div 
      className={containerClasses}
      style={cssCustomProperties}
      data-motion-preference={prefersReducedMotion ? 'reduce' : 'no-preference'}
    >
      <div className="text-center">
        {/* Animated Logo */}
        <div className="mb-6 flex justify-center">
          <div className="relative">
            {/* Outer spinning circle */}
            <div className={spinnerClasses}></div>
            {/* Inner pin */}
            <div className="absolute inset-0 flex items-center justify-center">
              <MapPin className={iconClasses} />
            </div>
          </div>
        </div>

        {/* Loading text */}
        <div className="space-y-2">
          <h3 className={titleClasses}>
            {t("loading.title")}
          </h3>
          
          {/* Loading dots - motion-aware implementation */}
          <div className="flex justify-center space-x-1">
            {[0, 150, 300].map((delay, index) => (
              <div
                key={index}
                className={getClassName(
                  "w-2 h-2 bg-red-500 rounded-full",
                  // Motion classes with staggered animation
                  !prefersReducedMotion ? "animate-bounce" : "",
                  // Reduced motion classes - static dots with subtle opacity variation
                  prefersReducedMotion ? `opacity-${60 + index * 15}` : ""
                )}
                style={!prefersReducedMotion ? { animationDelay: `${delay}ms` } : undefined}
              />
            ))}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6 w-48 mx-auto">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden transition-colors">
            <div className={progressBarClasses}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PageLoader;
