import React, { useState, useEffect } from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLanguage } from "@/contexts/LanguageContext";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const BackToTopButton: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const { t } = useLanguage();
  const { 
    prefersReducedMotion, 
    getClassName, 
    getTransitionProps,
    cssCustomProperties 
  } = useReducedMotion();

  useEffect(() => {
    const onScroll = () => {
      setVisible(window.scrollY > 300);
    };
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollToTop = () => {
    // Respect motion preferences for scroll behavior
    const scrollBehavior = prefersReducedMotion ? "instant" : "smooth";
    window.scrollTo({ top: 0, behavior: scrollBehavior });
  };

  // Get motion-safe transition properties
  const transitionProps = getTransitionProps(0.3);

  // Generate motion-aware class names
  const buttonClasses = getClassName(
    "fixed bottom-8 right-8 z-50 rounded-full bg-red-500 p-3 text-white shadow-lg",
    // Motion classes - applied when motion is preferred
    "transition-all duration-300 ease-out hover:scale-110 hover:shadow-xl hover:bg-red-600",
    // Reduced motion classes - applied when motion is reduced
    "hover:bg-red-600 focus:ring-2 focus:ring-red-300 focus:ring-offset-2"
  );

  const iconClasses = getClassName(
    "h-5 w-5",
    // Motion classes
    "transition-transform duration-200 hover:translate-y-[-1px]",
    // Reduced motion classes
    "" // No additional classes for reduced motion
  );

  return (
    <button
      aria-label={t("common.back_to_top")}
      onClick={scrollToTop}
      className={cn(
        buttonClasses,
        visible ? "opacity-100" : "pointer-events-none opacity-0"
      )}
      style={{ ...transitionProps.style, ...cssCustomProperties }}
      data-motion-preference={prefersReducedMotion ? 'reduce' : 'no-preference'}
    >
      <ArrowUp className={iconClasses} />
    </button>
  );
};

export default BackToTopButton;
