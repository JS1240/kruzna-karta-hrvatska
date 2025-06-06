import { useEffect } from "react";
import { useTheme } from "./ThemeProvider";

const FaviconSwitcher = () => {
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    const favicon = document.querySelector(
      "link[rel*='icon']",
    ) as HTMLLinkElement;

    if (favicon) {
      favicon.href =
        resolvedTheme === "dark" ? "/favicon-dark.svg" : "/favicon-updated.svg";
    }
  }, [resolvedTheme]);

  return null; // This component doesn't render anything
};

export default FaviconSwitcher;
