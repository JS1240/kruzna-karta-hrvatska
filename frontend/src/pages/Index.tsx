import React, { useState } from "react";
import Header from "@/components/Header";
import EventMap from "@/components/EventMap";
import FeaturedEvents from "@/components/FeaturedEvents";
import LatestNews from "@/components/LatestNews";
import AboutCroatia from "@/components/AboutCroatia";
import Footer from "@/components/Footer";
import PageTransition from "@/components/PageTransition";
import EnhancedSearch from "@/components/EnhancedSearch";
import { useLanguage } from "@/contexts/LanguageContext";
import { CalendarIcon, MapPinIcon, HeartIcon, RefreshCw } from "lucide-react";
import EventCarousel from "@/components/EventCarousel";
import { useHeroEvents } from "@/hooks/useHeroEvents";

const Index = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const { t } = useLanguage();
  const { events: heroEvents, loading: eventsLoading, error: eventsError, refetch } = useHeroEvents(5);

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream dark:bg-gray-900 transition-colors duration-300">
        <Header />

        <main className="flex-grow container mx-auto px-4 py-8">
          <section className="mb-12">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="md:w-1/2">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-navy-blue dark:text-white mb-4 font-sreda transition-colors duration-300">
                  {t("home.title")}
                </h1>
                <p className="text-lg text-gray-700 dark:text-gray-300 mb-6 font-josefin transition-colors duration-300">
                  {t("home.subtitle")}
                </p>

                <EnhancedSearch
                  value={searchTerm}
                  onChange={setSearchTerm}
                  placeholder={t("home.search.placeholder")}
                  onSuggestionSelect={(suggestion) => {
                    console.log('Selected suggestion:', suggestion);
                  }}
                />

                <div className="mt-6 flex flex-wrap gap-4">
                  <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 transition-colors duration-300">
                    <CalendarIcon
                      className="text-navy-blue dark:text-blue-400"
                      size={16}
                    />
                    <span>{t("home.features.updated")}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 transition-colors duration-300">
                    <MapPinIcon
                      className="text-navy-blue dark:text-blue-400"
                      size={16}
                    />
                    <span>{t("home.features.cities")}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 transition-colors duration-300">
                    <HeartIcon
                      className="text-navy-blue dark:text-blue-400"
                      size={16}
                    />
                    <span>{t("home.features.curated")}</span>
                  </div>
                  {eventsError && (
                    <button
                      onClick={refetch}
                      className="flex items-center gap-2 text-sm text-navy-blue dark:text-blue-400 hover:underline transition-colors duration-300"
                    >
                      <RefreshCw size={16} />
                      <span>Refresh Events</span>
                    </button>
                  )}
                </div>
              </div>

              <div className="md:w-1/2">
                <EventCarousel
                  events={heroEvents}
                  loading={eventsLoading}
                  error={eventsError}
                  speed={40}
                />
              </div>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-3xl font-bold mb-6 font-sreda text-navy-blue dark:text-white transition-colors duration-300">
              {t("home.map.title")}
            </h2>

            <EventMap className="h-[600px]" />
          </section>

          <FeaturedEvents />

          <LatestNews />

          <AboutCroatia />
        </main>

        <Footer />
      </div>
    </PageTransition>
  );
};

export default Index;
