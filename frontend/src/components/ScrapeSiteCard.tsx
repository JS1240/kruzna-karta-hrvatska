import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Download, Database } from "lucide-react";

interface ScrapeResponse {
  status: string;
  message: string;
  scraped_events?: number;
  saved_events?: number;
}

interface Props {
  title: string;
  description: string;
  loadingQuick: boolean;
  loadingFull: boolean;
  resultQuick?: ScrapeResponse;
  resultFull?: ScrapeResponse;
  onQuick: () => void;
  onFull: () => void;
  getStatusIcon: (status: string) => JSX.Element;
  getStatusBadge: (status: string) => JSX.Element;
}

const ScrapeSiteCard: React.FC<Props> = ({
  title,
  description,
  loadingQuick,
  loadingFull,
  resultQuick,
  resultFull,
  onQuick,
  onFull,
  getStatusIcon,
  getStatusBadge,
}) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center justify-between">
        <span>{title}</span>
        {resultFull && getStatusBadge(resultFull.status)}
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      <p className="text-sm text-gray-600">{description}</p>

      <div className="flex space-x-2">
        <Button
          onClick={onQuick}
          disabled={loadingQuick}
          variant="outline"
          className="flex-1"
        >
          {loadingQuick ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          Quick Test
        </Button>

        <Button onClick={onFull} disabled={loadingFull} className="flex-1">
          {loadingFull ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Database className="h-4 w-4 mr-2" />
          )}
          Full Scrape
        </Button>
      </div>

      {resultQuick && (
        <Alert>
          <div className="flex items-center space-x-2">
            {getStatusIcon(resultQuick.status)}
            <AlertDescription>
              <strong>Quick Test:</strong> {resultQuick.message}
              {resultQuick.scraped_events !== undefined && (
                <span className="block mt-1">
                  Found {resultQuick.scraped_events} events, saved {resultQuick.saved_events} new ones
                </span>
              )}
            </AlertDescription>
          </div>
        </Alert>
      )}

      {resultFull && (
        <Alert>
          <div className="flex items-center space-x-2">
            {getStatusIcon(resultFull.status)}
            <AlertDescription>
              <strong>Full Scrape:</strong> {resultFull.message}
              {resultFull.scraped_events !== undefined && (
                <span className="block mt-1">
                  Found {resultFull.scraped_events} events, saved {resultFull.saved_events} new ones
                </span>
              )}
            </AlertDescription>
          </div>
        </Alert>
      )}
    </CardContent>
  </Card>
);

export default ScrapeSiteCard;
