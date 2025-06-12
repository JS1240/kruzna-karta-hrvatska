import React, { useState } from "react";
import Header from "@/components/Header";
import EventMap from "@/components/EventMap";
import FeaturedEvents from "@/components/FeaturedEvents";
import LatestNews from "@/components/LatestNews";
import AboutCroatia from "@/components/AboutCroatia";
import Footer from "@/components/Footer";
import PageTransition from "@/components/PageTransition";
import { useLanguage } from "@/contexts/LanguageContext";
import { SearchIcon, CalendarIcon, MapPinIcon, HeartIcon } from "lucide-react";
import EventCarousel from "@/components/EventCarousel";

const Index = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const { t } = useLanguage();

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream dark:bg-gray-900 transition-colors duration-300">
        <Header />

        <main className="flex-grow container mx-auto px-4 py-8">
          {/* Demo Notice */}
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg transition-colors duration-300">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-blue-800 dark:text-blue-200 font-medium">
                {t("demo.notice")}
              </span>
            </div>
            <p className="text-blue-700 dark:text-blue-300 text-sm mt-1">
              {t("demo.description")}
            </p>
          </div>
          <section className="mb-12">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="md:w-1/2">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-navy-blue dark:text-white mb-4 font-sreda transition-colors duration-300">
                  {t("home.title")}
                </h1>
                <p className="text-lg text-gray-700 dark:text-gray-300 mb-6 font-josefin transition-colors duration-300">
                  {t("home.subtitle")}
                </p>

                <div className="relative">
                  <input
                    type="text"
                    placeholder={t("home.search.placeholder")}
                    className="w-full py-3 px-4 pr-12 bg-white dark:bg-gray-800 border border-light-blue dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-navy-blue dark:focus:ring-blue-400 text-gray-900 dark:text-gray-100 transition-colors duration-300"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <SearchIcon className="text-medium-blue" size={20} />
                  </div>
                </div>

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
                </div>
              </div>

              <div className="md:w-1/2">
                <EventCarousel
                  events={[
                    {
                      id: "1",
                      title: "Zagreb Summer Festival",
                      image: "/event-images/concert.jpg",
                      date: "June 10, 2025",
                      location: "Zagreb",
                    },
                    {
                      id: "2",
                      title: "Dubrovnik Night Run",
                      image: "/event-images/workout.jpg",
                      date: "June 12, 2025",
                      location: "Dubrovnik",
                    },
                    {
                      id: "3",
                      title: "Split Tech Meetup",
                      image: "/event-images/meetup.jpg",
                      date: "June 15, 2025",
                      location: "Split",
                    },
                    {
                      id: "4",
                      title: "Pula Party Weekend",
                      image: "/event-images/party.jpg",
                      date: "June 20, 2025",
                      location: "Pula",
                    },
                    {
                      id: "5",
                      title: "Rijeka Business Conference",
                      image: "/event-images/conference.jpg",
                      date: "June 25, 2025",
                      location: "Rijeka",
                    },
                  ]}
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
