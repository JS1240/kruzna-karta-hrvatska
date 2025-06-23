import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";

export type Language = "en" | "hr";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(
  undefined,
);

interface Translations {
  [key: string]: string;
}

interface LanguageProviderProps {
  children: ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({
  children,
}) => {
  const getInitialLanguage = (): Language => {
    // Check localStorage first
    const stored = localStorage.getItem('language');
    if (stored === 'hr' || stored === 'en') {
      return stored as Language;
    }
    
    // Check browser language
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('hr')) {
      return 'hr';
    }
    
    // Default to Croatian
    return 'hr';
  };

  const [language, setLanguage] = useState<Language>(getInitialLanguage());
  const [translations, setTranslations] = useState<Translations>({});

  // Save language preference to localStorage
  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  useEffect(() => {
    const load = async () => {
      switch (language) {
        case "hr":
          setTranslations((await import("../i18n/hr.json")).default);
          break;
        case "en":
        default:
          setTranslations((await import("../i18n/en.json")).default);
      }
    };
    load();
  }, [language]);

  const t = (key: string): string => {
    return translations[key] || key;
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
