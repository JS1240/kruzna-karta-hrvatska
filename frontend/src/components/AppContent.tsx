import React from "react";
import { Routes, Route } from "react-router-dom";
import { usePageLoader } from "../hooks/usePageLoader";
import PageLoader from "./PageLoader";
import Index from "../pages/Index";
import About from "../pages/About";
import Venues from "../pages/Venues";
import Favorites from "../pages/Favorites";
import Popular from "../pages/Popular";
import Admin from "../pages/Admin";
import CreateEvent from "../pages/CreateEvent";
import OrganizerDashboard from "../pages/OrganizerDashboard";
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
        <Route path="/admin" element={<Admin />} />
        <Route path="/create-event" element={<CreateEvent />} />
        <Route path="/organizer/dashboard" element={<OrganizerDashboard />} />
        {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
};

export default AppContent;
