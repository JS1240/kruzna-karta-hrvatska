
import React from "react";

interface LogoProps {
  className?: string;
}

const Logo = ({ className = "" }: LogoProps) => {
  return (
    <div className={`font-sreda text-lg font-bold text-navy-blue flex items-center ${className}`}>
      <span className="text-xl mr-1">🇭🇷</span> Croatia Travel
    </div>
  );
};

export default Logo;
