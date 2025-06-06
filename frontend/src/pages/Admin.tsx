import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import PageTransition from "@/components/PageTransition";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Loader2,
  Download,
  Database,
  Globe,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

interface ScrapeResponse {
  status: string;
  message: string;
  scraped_events?: number;
  saved_events?: number;
  task_id?: string;
  details?: Record<string, any>;
}

const Admin = () => {
  const [maxPages, setMaxPages] = useState(2);
  const [usePlaywright, setUsePlaywright] = useState(true);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, ScrapeResponse>>({});
  const [progress, setProgress] = useState(0);

  const apiBase =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

  const triggerScraping = async (endpoint: string, site: string) => {
    setLoading((prev) => ({ ...prev, [site]: true }));
    setResults((prev) => ({
      ...prev,
      [site]: { status: "loading", message: "Starting scraping..." },
    }));

    try {
      const response = await fetch(`${apiBase}/scraping/${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          max_pages: maxPages,
          use_playwright: usePlaywright,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setResults((prev) => ({ ...prev, [site]: result }));

      // Simulate progress for background tasks
      if (result.status === "accepted") {
        let progressValue = 0;
        const interval = setInterval(() => {
          progressValue += 10;
          setProgress(progressValue);
          if (progressValue >= 100) {
            clearInterval(interval);
            setResults((prev) => ({
              ...prev,
              [site]: {
                ...result,
                status: "success",
                message:
                  "Scraping completed in background. Check database for new events.",
              },
            }));
          }
        }, 1000);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      setResults((prev) => ({
        ...prev,
        [site]: {
          status: "error",
          message: errorMessage,
        },
      }));
    } finally {
      setLoading((prev) => ({ ...prev, [site]: false }));
    }
  };

  const quickScrape = async (endpoint: string, site: string) => {
    setLoading((prev) => ({ ...prev, [`${site}-quick`]: true }));
    setResults((prev) => ({
      ...prev,
      [`${site}-quick`]: { status: "loading", message: "Quick scraping..." },
    }));

    try {
      const response = await fetch(
        `${apiBase}/scraping/${endpoint}/quick?max_pages=1`,
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setResults((prev) => ({ ...prev, [`${site}-quick`]: result }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      setResults((prev) => ({
        ...prev,
        [`${site}-quick`]: {
          status: "error",
          message: errorMessage,
        },
      }));
    } finally {
      setLoading((prev) => ({ ...prev, [`${site}-quick`]: false }));
    }
  };

  const checkScrapingStatus = async () => {
    try {
      const response = await fetch(`${apiBase}/scraping/status`);
      const status = await response.json();
      console.log("Scraping Status:", status);
      alert(`Scraping system is ${status.status}. Check console for details.`);
    } catch (error) {
      console.error("Failed to check status:", error);
      alert("Failed to check scraping status");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
      case "accepted":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "loading":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return (
          <Badge variant="default" className="bg-green-500">
            Success
          </Badge>
        );
      case "accepted":
        return (
          <Badge variant="default" className="bg-blue-500">
            Running
          </Badge>
        );
      case "error":
        return <Badge variant="destructive">Error</Badge>;
      case "loading":
        return <Badge variant="secondary">Loading</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream">
        <Header />

        <main className="flex-grow container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-navy-blue mb-2 font-sreda">
                Admin Panel
              </h1>
              <p className="text-lg text-gray-600">
                Manage event scraping and database operations
              </p>
            </div>

            {/* Configuration Card */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="h-5 w-5" />
                  <span>Scraping Configuration</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="maxPages">Max Pages to Scrape</Label>
                    <Input
                      id="maxPages"
                      type="number"
                      min="1"
                      max="10"
                      value={maxPages}
                      onChange={(e) =>
                        setMaxPages(parseInt(e.target.value) || 1)
                      }
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="playwright"
                      checked={usePlaywright}
                      onCheckedChange={setUsePlaywright}
                    />
                    <Label htmlFor="playwright">
                      Use Playwright (for dynamic content)
                    </Label>
                  </div>
                  <div className="flex items-center">
                    <Button onClick={checkScrapingStatus} variant="outline">
                      <Globe className="h-4 w-4 mr-2" />
                      Check Status
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Scraping Controls */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Entrio.hr */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Entrio.hr</span>
                    {results["entrio"] &&
                      getStatusBadge(results["entrio"].status)}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-gray-600">
                    Croatia's leading event ticketing platform
                  </p>

                  <div className="flex space-x-2">
                    <Button
                      onClick={() => quickScrape("entrio", "entrio")}
                      disabled={loading["entrio-quick"]}
                      variant="outline"
                      className="flex-1"
                    >
                      {loading["entrio-quick"] ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Download className="h-4 w-4 mr-2" />
                      )}
                      Quick Test
                    </Button>

                    <Button
                      onClick={() => triggerScraping("entrio", "entrio")}
                      disabled={loading["entrio"]}
                      className="flex-1"
                    >
                      {loading["entrio"] ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Database className="h-4 w-4 mr-2" />
                      )}
                      Full Scrape
                    </Button>
                  </div>

                  {results["entrio-quick"] && (
                    <Alert>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(results["entrio-quick"].status)}
                        <AlertDescription>
                          <strong>Quick Test:</strong>{" "}
                          {results["entrio-quick"].message}
                          {results["entrio-quick"].scraped_events !==
                            undefined && (
                            <span className="block mt-1">
                              Found {results["entrio-quick"].scraped_events}{" "}
                              events, saved{" "}
                              {results["entrio-quick"].saved_events} new ones
                            </span>
                          )}
                        </AlertDescription>
                      </div>
                    </Alert>
                  )}

                  {results["entrio"] && (
                    <Alert>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(results["entrio"].status)}
                        <AlertDescription>
                          <strong>Full Scrape:</strong>{" "}
                          {results["entrio"].message}
                          {results["entrio"].scraped_events !== undefined && (
                            <span className="block mt-1">
                              Found {results["entrio"].scraped_events} events,
                              saved {results["entrio"].saved_events} new ones
                            </span>
                          )}
                        </AlertDescription>
                      </div>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* Croatia.hr */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Croatia.hr</span>
                    {results["croatia"] &&
                      getStatusBadge(results["croatia"].status)}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-gray-600">
                    Official Croatian tourism events portal
                  </p>

                  <div className="flex space-x-2">
                    <Button
                      onClick={() => quickScrape("croatia", "croatia")}
                      disabled={loading["croatia-quick"]}
                      variant="outline"
                      className="flex-1"
                    >
                      {loading["croatia-quick"] ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Download className="h-4 w-4 mr-2" />
                      )}
                      Quick Test
                    </Button>

                    <Button
                      onClick={() => triggerScraping("croatia", "croatia")}
                      disabled={loading["croatia"]}
                      className="flex-1"
                    >
                      {loading["croatia"] ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Database className="h-4 w-4 mr-2" />
                      )}
                      Full Scrape
                    </Button>
                  </div>

                  {results["croatia-quick"] && (
                    <Alert>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(results["croatia-quick"].status)}
                        <AlertDescription>
                          <strong>Quick Test:</strong>{" "}
                          {results["croatia-quick"].message}
                          {results["croatia-quick"].scraped_events !==
                            undefined && (
                            <span className="block mt-1">
                              Found {results["croatia-quick"].scraped_events}{" "}
                              events, saved{" "}
                              {results["croatia-quick"].saved_events} new ones
                            </span>
                          )}
                        </AlertDescription>
                      </div>
                    </Alert>
                  )}

                  {results["croatia"] && (
                    <Alert>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(results["croatia"].status)}
                        <AlertDescription>
                          <strong>Full Scrape:</strong>{" "}
                          {results["croatia"].message}
                          {results["croatia"].scraped_events !== undefined && (
                            <span className="block mt-1">
                              Found {results["croatia"].scraped_events} events,
                              saved {results["croatia"].saved_events} new ones
                            </span>
                          )}
                        </AlertDescription>
                      </div>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Combined Scraping */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>All Sites</span>
                  {results["all"] && getStatusBadge(results["all"].status)}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-gray-600">
                  Scrape events from all supported sites simultaneously
                </p>

                <Button
                  onClick={() => triggerScraping("all", "all")}
                  disabled={loading["all"]}
                  className="w-full"
                  size="lg"
                >
                  {loading["all"] ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Database className="h-4 w-4 mr-2" />
                  )}
                  Scrape All Sites ({maxPages} pages each)
                </Button>

                {loading["all"] && progress > 0 && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{progress}%</span>
                    </div>
                    <Progress value={progress} />
                  </div>
                )}

                {results["all"] && (
                  <Alert>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(results["all"].status)}
                      <AlertDescription>
                        <strong>Multi-site Scrape:</strong>{" "}
                        {results["all"].message}
                        {results["all"].scraped_events !== undefined && (
                          <span className="block mt-1">
                            Total: {results["all"].scraped_events} events found,
                            {results["all"].saved_events} new events saved
                          </span>
                        )}
                        {results["all"].details && (
                          <div className="mt-2 space-y-1 text-xs">
                            {Object.entries(results["all"].details).map(
                              ([site, result]: [string, any]) => (
                                <div key={site}>
                                  <strong>{site}:</strong> {result.message}
                                </div>
                              ),
                            )}
                          </div>
                        )}
                      </AlertDescription>
                    </div>
                  </Alert>
                )}
              </CardContent>
            </Card>

            <Separator className="my-8" />

            {/* Instructions */}
            <Card>
              <CardHeader>
                <CardTitle>Instructions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-semibold mb-2">Quick Test</h4>
                    <p className="text-gray-600">
                      Scrapes 1 page immediately to test the scraper and see
                      sample results. Good for testing changes or verifying the
                      scraper is working.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Full Scrape</h4>
                    <p className="text-gray-600">
                      Scrapes the configured number of pages. For more than 2
                      pages, the task runs in the background to avoid timeouts.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Playwright Mode</h4>
                    <p className="text-gray-600">
                      Uses browser automation to handle JavaScript-heavy sites
                      like Croatia.hr. Slower but more reliable for dynamic
                      content.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Page Limit</h4>
                    <p className="text-gray-600">
                      Controls how many pages to scrape per site. Start with 1-2
                      pages for testing, increase for production scraping.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>

        <Footer />
      </div>
    </PageTransition>
  );
};

export default Admin;
