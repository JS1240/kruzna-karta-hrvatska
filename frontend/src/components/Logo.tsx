import React, { useState } from "react";
import { useTheme } from "./ThemeProvider";

interface LogoProps {
  className?: string;
}

const Logo = ({ className = "" }: LogoProps) => {
  const { resolvedTheme } = useTheme();
  const [isLoading, setIsLoading] = useState(false);

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  const logoSrc =
    resolvedTheme === "dark"
      ? "/diidemo-logo-dark-simple.svg"
      : "/diidemo-logo-latest.svg";

  return (
    <div className={`flex items-center ${className}`}>
      <img
        src={logoSrc}
        alt="Diidemo.hr logo"
        className={`h-12 w-auto transition-all duration-300 ${isLoading ? "opacity-0" : "opacity-100"}`}
        onLoad={handleImageLoad}
      />
    </div>
  );
};

export default Logo;
