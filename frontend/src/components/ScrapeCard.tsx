import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, Download, Database } from 'lucide-react';

interface ScrapeResponse {
  status: string;
  message: string;
  scraped_events?: number;
  saved_events?: number;
}

interface ScrapeCardProps {
  title: string;
  description: string;
  siteKey: string;
  loading: Record<string, boolean>;
  results: Record<string, ScrapeResponse>;
  onQuickScrape: (key: string) => void;
  onFullScrape: (key: string) => void;
  getStatusIcon: (status: string) => JSX.Element;
  getStatusBadge: (status: string) => JSX.Element;
}

const ScrapeCard: React.FC<ScrapeCardProps> = ({
  title,
  description,
  siteKey,
  loading,
  results,
  onQuickScrape,
  onFullScrape,
  getStatusIcon,
  getStatusBadge,
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{title}</span>
          {results[siteKey] && getStatusBadge(results[siteKey].status)}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-600">{description}</p>
        <div className="flex space-x-2">
          <Button
            onClick={() => onQuickScrape(siteKey)}
            disabled={loading[`${siteKey}-quick`]}
            variant="outline"
            className="flex-1"
          >
            {loading[`${siteKey}-quick`] ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Quick Test
          </Button>
          <Button
            onClick={() => onFullScrape(siteKey)}
            disabled={loading[siteKey]}
            className="flex-1"
          >
            {loading[siteKey] ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Database className="h-4 w-4 mr-2" />
            )}
            Full Scrape
          </Button>
        </div>
        {results[`${siteKey}-quick`] && (
          <Alert>
            <div className="flex items-center space-x-2">
              {getStatusIcon(results[`${siteKey}-quick`].status)}
              <AlertDescription>
                <strong>Quick Test:</strong> {results[`${siteKey}-quick`].message}
                {results[`${siteKey}-quick`].scraped_events !== undefined && (
                  <span className="block mt-1">
                    Found {results[`${siteKey}-quick`].scraped_events} events, saved {results[`${siteKey}-quick`].saved_events} new ones
                  </span>
                )}
              </AlertDescription>
            </div>
          </Alert>
        )}
        {results[siteKey] && (
          <Alert>
            <div className="flex items-center space-x-2">
              {getStatusIcon(results[siteKey].status)}
              <AlertDescription>
                <strong>Full Scrape:</strong> {results[siteKey].message}
                {results[siteKey].scraped_events !== undefined && (
                  <span className="block mt-1">
                    Found {results[siteKey].scraped_events} events, saved {results[siteKey].saved_events} new ones
                  </span>
                )}
              </AlertDescription>
            </div>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default ScrapeCard;
