import React, { ReactNode, useEffect, useState } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

const PageTransition: React.FC<PageTransitionProps> = ({ children, className = "" }) => {
  const [isVisible, setIsVisible] = useState(false);
  const { 
    prefersReducedMotion, 
    getTransitionProps, 
    getClassName 
  } = useReducedMotion();

  useEffect(() => {
    // For reduced motion, show immediately
    // For normal motion, use small delay for smooth transition
    const delay = prefersReducedMotion ? 0 : 100;
    
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [prefersReducedMotion]);

  // Get motion-safe transition properties
  const transitionProps = getTransitionProps(0.5);
  
  // Generate motion-aware class names
  const motionClasses = getClassName(
    "transform",
    // Motion classes - applied when motion is preferred
    isVisible 
      ? "opacity-100 translate-y-0 motion-safe:transition-all motion-safe:duration-500 motion-safe:ease-out" 
      : "opacity-0 translate-y-4 motion-safe:transition-all motion-safe:duration-500 motion-safe:ease-out",
    // Reduced motion classes - applied when motion is reduced
    isVisible 
      ? "opacity-100" 
      : "opacity-0"
  );

  return (
    <div
      className={`${motionClasses} ${className}`}
      style={transitionProps.style}
      data-motion-preference={prefersReducedMotion ? 'reduce' : 'no-preference'}
    >
      {children}
    </div>
  );
};

export default PageTransition;
