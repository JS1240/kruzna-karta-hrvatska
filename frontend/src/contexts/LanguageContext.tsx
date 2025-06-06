import React, { createContext, useContext, useState, ReactNode } from "react";

export type Language = "en" | "hr";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(
  undefined,
);

// Translation strings
const translations = {
  en: {
    // Navigation
    "nav.home": "Home",
    "nav.about": "About",
    "nav.venues": "Venues",
    "nav.popular": "Popular",
    "nav.map": "Map",
    "nav.admin": "Admin",

    // Homepage
    "home.title": "Discover Events Near You",
    "home.subtitle":
      "Find concerts, festivals, conferences, and parties all across Croatia with Diidemo.hr - your ultimate events discovery platform.",
    "home.search.placeholder": "Search events, venues or cities...",
    "home.features.updated": "Updated Daily",
    "home.features.cities": "All Croatian Cities",
    "home.features.curated": "Curated Selection",
    "home.map.title": "Find Events on the Map",

    // Demo
    "demo.notice": "Demo Mode",
    "demo.description":
      "Showing 8 sample Croatian events. Diidemo.hr backend API is running with mock data.",
    "demo.map.title": "Interactive Map Demo",
    "demo.map.description":
      "Croatian events map would appear here with a valid Mapbox token",
    "demo.map.button": "🗺️ View Full Interactive Map",
    "demo.map.events":
      "Events: Zagreb, Split, Dubrovnik, Rijeka, Zadar, Pula, Makarska, Osijek",

    // Loading
    "loading.title": "Loading Diidemo.hr",

    // Event Map
    "map.search.label": "Search Events",
    "map.search.placeholder": "Search by name or description...",
    "map.categories.label": "Event Categories",
    "map.location.label": "Location",
    "map.location.county": "Select County",
    "map.location.city": "Select City",
    "map.date.label": "Date Range",
    "map.date.today": "Today",
    "map.date.tomorrow": "Tomorrow",
    "map.date.weekend": "Weekend",
    "map.date.month": "This Month",
    "map.date.custom": "Pick custom dates",
    "map.price.label": "Price Range (EUR)",
    "map.clear.filters": "Clear All Filters",
    "map.showing.events": "Showing {count} of {total} events",
    "map.legend.title": "Event Types",
    "map.loading": "Loading events...",
    "map.retry": "Retry",

    // Categories
    "category.concerts": "Concerts",
    "category.music": "Music",
    "category.sports": "Sports & Fitness",
    "category.meetups": "Meetups",
    "category.conferences": "Conferences",
    "category.parties": "Parties",
    "category.festivals": "Festivals",
    "category.theater": "Theater",
    "category.culture": "Culture",
    "category.other": "Other",

    // Admin Panel
    "admin.title": "Admin Panel",
    "admin.subtitle": "Manage event scraping and database operations",
    "admin.config.title": "Scraping Configuration",
    "admin.config.maxpages": "Max Pages to Scrape",
    "admin.config.playwright": "Use Playwright (for dynamic content)",
    "admin.config.status": "Check Status",
    "admin.entrio.title": "Entrio.hr",
    "admin.entrio.description": "Croatia's leading event ticketing platform",
    "admin.croatia.title": "Croatia.hr",
    "admin.croatia.description": "Official Croatian tourism events portal",
    "admin.quick.test": "Quick Test",
    "admin.full.scrape": "Full Scrape",
    "admin.all.sites": "All Sites",
    "admin.all.description":
      "Scrape events from all supported sites simultaneously",
    "admin.all.button": "Scrape All Sites ({pages} pages each)",
    "admin.instructions.title": "Instructions",

    // Footer
    "footer.about": "About Us",
    "footer.about.text":
      "Diidemo.hr - Your ultimate platform for discovering amazing events near you across Croatia.",
    "footer.quicklinks": "Quick Links",
    "footer.contact": "Contact Us",
    "footer.email": "Email: info@diidemo.hr",
    "footer.phone": "Phone: +385 1 234 5678",
    "footer.address": "Address: Zagreb, Croatia",
    "footer.copyright": "© 2024 Diidemo.hr. All rights reserved.",

    // Common
    "common.events": "Events",
    "common.home": "Home",
    "common.about": "About",
    "common.contact": "Contact",
    "common.date": "Date",
    "common.location": "Location",
    "common.price": "Price",
    "common.details": "View Details",
    "common.free": "Free",
  },
  hr: {
    // Navigation
    "nav.home": "Početna",
    "nav.about": "O nama",
    "nav.venues": "Lokacije",
    "nav.popular": "Popularno",
    "nav.map": "Karta",
    "nav.admin": "Admin",

    // Homepage
    "home.title": "Otkrijte Događaje u Vašoj Blizini",
    "home.subtitle":
      "Pronađite koncerte, festivale, konferencije i zabave diljem Hrvatske s Diidemo.hr - vašom ultimativnom platformom za otkrivanje događaja.",
    "home.search.placeholder": "Pretraži događaje, lokacije ili gradove...",
    "home.features.updated": "Ažurirano Dnevno",
    "home.features.cities": "Svi Hrvatski Gradovi",
    "home.features.curated": "Odabrani Sadržaj",
    "home.map.title": "Pronađite Događaje na Karti",

    // Demo
    "demo.notice": "Demo Način",
    "demo.description":
      "Prikazuje 8 uzoraka hrvatskih događaja. Diidemo.hr backend API radi s probnim podacima.",
    "demo.map.title": "Demo Interaktivne Karte",
    "demo.map.description":
      "Karta hrvatskih događaja bi se pojavila ovdje s važećim Mapbox tokenom",
    "demo.map.button": "🗺️ Pogledaj Punu Interaktivnu Kartu",
    "demo.map.events":
      "Događaji: Zagreb, Split, Dubrovnik, Rijeka, Zadar, Pula, Makarska, Osijek",

    // Loading
    "loading.title": "Učitava Diidemo.hr",

    // Event Map
    "map.search.label": "Pretraži Događaje",
    "map.search.placeholder": "Pretraži po imenu ili opisu...",
    "map.categories.label": "Kategorije Događaja",
    "map.location.label": "Lokacija",
    "map.location.county": "Odaberi Županiju",
    "map.location.city": "Odaberi Grad",
    "map.date.label": "Raspon Datuma",
    "map.date.today": "Danas",
    "map.date.tomorrow": "Sutra",
    "map.date.weekend": "Vikend",
    "map.date.month": "Ovaj Mjesec",
    "map.date.custom": "Odaberi prilagođene datume",
    "map.price.label": "Raspon Cijena (EUR)",
    "map.clear.filters": "Ukloni Sve Filtere",
    "map.showing.events": "Prikazuje {count} od {total} događaja",
    "map.legend.title": "Tipovi Događaja",
    "map.loading": "Učitava događaje...",
    "map.retry": "Pokušaj ponovo",

    // Categories
    "category.concerts": "Koncerti",
    "category.music": "Glazba",
    "category.sports": "Sport i Fitness",
    "category.meetups": "Okupljanja",
    "category.conferences": "Konferencije",
    "category.parties": "Zabave",
    "category.festivals": "Festivali",
    "category.theater": "Kazalište",
    "category.culture": "Kultura",
    "category.other": "Ostalo",

    // Admin Panel
    "admin.title": "Admin Panel",
    "admin.subtitle":
      "Upravljanje skupljanjem događaja i operacijama baze podataka",
    "admin.config.title": "Konfiguracija Skupljanja",
    "admin.config.maxpages": "Maksimalni Broj Stranica",
    "admin.config.playwright": "Koristi Playwright (za dinamični sadržaj)",
    "admin.config.status": "Provjeri Status",
    "admin.entrio.title": "Entrio.hr",
    "admin.entrio.description": "Vodeća hrvatska platforma za prodaju ulaznica",
    "admin.croatia.title": "Croatia.hr",
    "admin.croatia.description": "Službeni hrvatski turistički portal događaja",
    "admin.quick.test": "Brzi Test",
    "admin.full.scrape": "Potpuno Skupljanje",
    "admin.all.sites": "Sve Stranice",
    "admin.all.description":
      "Skupi događaje sa svih podržanih stranica istovremeno",
    "admin.all.button": "Skupi Sve Stranice ({pages} stranica svaka)",
    "admin.instructions.title": "Upute",

    // Footer
    "footer.about": "O Nama",
    "footer.about.text":
      "Diidemo.hr - Vaša ultimativna platforma za otkrivanje nevjerojatnih događaja u vašoj blizini diljem Hrvatske.",
    "footer.quicklinks": "Brze Veze",
    "footer.contact": "Kontakt",
    "footer.email": "Email: info@diidemo.hr",
    "footer.phone": "Telefon: +385 1 234 5678",
    "footer.address": "Adresa: Zagreb, Hrvatska",
    "footer.copyright": "© 2024 Diidemo.hr. Sva prava pridržana.",

    // Common
    "common.events": "Događaji",
    "common.home": "Početna",
    "common.about": "O nama",
    "common.contact": "Kontakt",
    "common.date": "Datum",
    "common.location": "Lokacija",
    "common.price": "Cijena",
    "common.details": "Pogledaj Detalje",
    "common.free": "Besplatno",
  },
};

interface LanguageProviderProps {
  children: ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({
  children,
}) => {
  const [language, setLanguage] = useState<Language>("en");

  const t = (key: string): string => {
    return (
      translations[language][key as keyof (typeof translations)["en"]] || key
    );
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
