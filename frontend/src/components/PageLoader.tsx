import React from "react";
import { MapPin } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

const PageLoader = () => {
  const { t } = useLanguage();

  return (
    <div className="fixed inset-0 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md z-50 flex items-center justify-center animate-in fade-in duration-300 transition-colors">
      <div className="text-center">
        {/* Animated Logo */}
        <div className="mb-6 flex justify-center">
          <div className="relative">
            {/* Outer spinning circle */}
            <div className="w-16 h-16 border-4 border-red-200 border-t-red-500 rounded-full animate-spin"></div>
            {/* Inner pulsing pin */}
            <div className="absolute inset-0 flex items-center justify-center">
              <MapPin className="w-6 h-6 text-red-500 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Loading text */}
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200 animate-pulse transition-colors">
            {t("loading.title")}
          </h3>
          <div className="flex justify-center space-x-1">
            <div
              className="w-2 h-2 bg-red-500 rounded-full animate-bounce"
              style={{ animationDelay: "0ms" }}
            ></div>
            <div
              className="w-2 h-2 bg-red-500 rounded-full animate-bounce"
              style={{ animationDelay: "150ms" }}
            ></div>
            <div
              className="w-2 h-2 bg-red-500 rounded-full animate-bounce"
              style={{ animationDelay: "300ms" }}
            ></div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6 w-48 mx-auto">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden transition-colors">
            <div className="h-full bg-gradient-to-r from-red-400 via-red-500 to-red-600 rounded-full animate-pulse transform origin-left transition-all duration-1000 ease-out w-3/4"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PageLoader;
