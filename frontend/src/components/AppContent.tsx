import React from "react";
import { Routes, Route } from "react-router-dom";
import { usePageLoader } from "@/hooks/usePageLoader";
import PageLoader from "./PageLoader";
import Index from "../pages/Index";
import About from "../pages/About";
import Venues from "../pages/Venues";
import Favorites from "../pages/Favorites";
import Popular from "../pages/Popular";
import MapPage from "../pages/MapPage";
import Admin from "../pages/Admin";
import NotFound from "../pages/NotFound";

const AppContent = () => {
  const isLoading = usePageLoader();

  return (
    <>
      {isLoading && <PageLoader />}
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/about" element={<About />} />
        <Route path="/venues" element={<Venues />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="/popular" element={<Popular />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/admin" element={<Admin />} />
        {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
};

export default AppContent;
