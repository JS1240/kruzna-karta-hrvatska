import React from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import EventMap from "@/components/EventMap";
import PageTransition from "@/components/PageTransition";

const MapPage = () => {
  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream dark:bg-gray-900 transition-colors duration-300">
        <Header />
        <main className="flex-grow">
          <EventMap />
        </main>
        <Footer />
      </div>
    </PageTransition>
  );
};

export default MapPage;
