import React from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import EventMap from "@/components/EventMap";

const MapPage = () => {
  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />

      <main className="flex-grow">
        <EventMap />
      </main>

      <Footer />
    </div>
  );
};

export default MapPage;
