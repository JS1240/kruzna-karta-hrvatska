import React, { memo } from "react";
import { categoryConfig, getAllCategories } from "@/lib/eventCategories";
import { cn } from "@/lib/utils";

interface CategoryFilterProps {
  activeCategory: string | null;
  onCategoryChange: (category: string | null) => void;
  isMobile: boolean;
}

export const CategoryFilter = memo<CategoryFilterProps>(({ 
  activeCategory, 
  onCategoryChange, 
  isMobile 
}) => {
  const handleCategoryClick = (key: string) => {
    try {
      const isActive = activeCategory === key;
      const newCategory = isActive ? null : key;
      onCategoryChange(newCategory);
    } catch (error) {
      console.error('Category change error:', error, { activeCategory, key });
    }
  };

  return (
    <div className={cn("grid gap-2", isMobile ? "grid-cols-2" : "grid-cols-3")}>
      {getAllCategories().map((key) => {
        const config = categoryConfig[key];
        if (!config) {
          console.warn(`No config found for category: ${key}`);
          return null;
        }
        
        const IconComponent = config.icon;
        const isActive = activeCategory === key;
        
        return (
          <button
            key={key}
            onClick={() => handleCategoryClick(key)}
            className={cn(
              "flex flex-col items-center p-3 rounded-lg border-2 transition-all duration-200 hover:shadow-md group",
              isActive
                ? "border-blue-500 bg-blue-50 shadow-sm"
                : "border-gray-200 hover:border-gray-300 bg-white"
            )}
            title={config.description || config.label}
            aria-label={`Filter by ${config.label}`}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center mb-1 transition-all duration-200",
                isActive ? "scale-110" : "group-hover:scale-105"
              )}
              style={{ 
                backgroundColor: isActive ? config.color : `${config.color}20`,
                border: `2px solid ${config.color}`
              }}
            >
              <IconComponent
                className="h-4 w-4"
                style={{ color: isActive ? "white" : config.color }}
              />
            </div>
            <span className="text-xs text-center leading-tight font-medium text-gray-700">
              {config.label}
            </span>
          </button>
        );
      })}
    </div>
  );
});

CategoryFilter.displayName = "CategoryFilter";