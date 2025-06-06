import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

export const usePageLoader = () => {
  const [isLoading, setIsLoading] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // Start loading when route changes
    setIsLoading(true);

    // Simulate loading time (you can adjust this or make it dynamic)
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 600); // 600ms loading time for smooth UX

    return () => clearTimeout(timer);
  }, [location.pathname]);

  return isLoading;
};
