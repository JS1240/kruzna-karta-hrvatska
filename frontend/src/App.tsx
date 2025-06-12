import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { LanguageProvider } from "./contexts/LanguageContext";
import { ThemeProvider } from "./components/ThemeProvider";
import FaviconSwitcher from "./components/FaviconSwitcher";
import AppContent from "./components/AppContent";
import BackToTopButton from "./components/BackToTopButton";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider defaultTheme="light" storageKey="diidemo-theme">
      <LanguageProvider>
        <TooltipProvider>
          <FaviconSwitcher />
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <AppContent />
            <BackToTopButton />
          </BrowserRouter>
        </TooltipProvider>
      </LanguageProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
