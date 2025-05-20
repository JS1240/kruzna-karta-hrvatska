import React from "react";

interface LogoProps {
  className?: string;
}

const Logo = ({ className = "" }: LogoProps) => {
  return (
    <div className={`font-sreda text-lg font-bold text-navy-blue flex items-center ${className}`}>
      <img src="/logo.png" alt="Doživi.hr logo" className="h-7 w-7 mr-2" />
      Doživi.hr
    </div>
  );
};

export default Logo;
