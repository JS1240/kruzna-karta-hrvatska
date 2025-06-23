import React, { useState, useEffect } from "react";
import { CalendarIcon, ArrowRight, Loader2, RefreshCw, AlertCircle } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
} from "./ui/carousel";
import { newsApi, NewsArticle } from "@/lib/api";

interface NewsCardProps {
  article: NewsArticle;
}

const NewsCard = ({ article }: NewsCardProps) => {
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };
  return (
    <Card className="overflow-hidden border-none shadow-md h-full flex flex-col">
      <div className="h-48 w-full overflow-hidden">
        <img
          src={article.imageUrl}
          alt={article.title}
          className="h-full w-full object-cover transition-transform hover:scale-105"
          onError={(e) => {
            e.currentTarget.src = '/event-images/concert.jpg';
          }}
        />
      </div>
      <CardContent className="flex-grow flex flex-col p-4">
        <div className="flex items-center text-sm text-gray-500 mb-2">
          <CalendarIcon size={14} className="mr-1" />
          <span>{formatDate(article.date)}</span>
          {article.category && (
            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
              {article.category}
            </span>
          )}
        </div>
        <h3 className="text-xl font-bold text-navy-blue mb-2">{article.title}</h3>
        <p className="text-gray-600 mb-4 flex-grow">{article.description}</p>
        {article.link ? (
          <a
            href={article.link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-medium-blue font-medium flex items-center hover:text-navy-blue transition-colors"
          >
            Read more <ArrowRight size={16} className="ml-1" />
          </a>
        ) : article.eventId ? (
          <a
            href={`/events/${article.eventId}`}
            className="text-medium-blue font-medium flex items-center hover:text-navy-blue transition-colors"
          >
            View Event <ArrowRight size={16} className="ml-1" />
          </a>
        ) : (
          <span className="text-gray-400 font-medium flex items-center">
            No link available
          </span>
        )}
      </CardContent>
    </Card>
  );
};

const LatestNews = () => {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try to fetch real news first
      let articles: NewsArticle[] = [];
      
      try {
        articles = await newsApi.getLatestNews(5);
      } catch {
        // Fallback: Generate news from recent events
        console.log('Using event-based news fallback');
        articles = await newsApi.generateEventNews(5);
      }
      
      setNews(articles);
    } catch (err) {
      console.error('Failed to fetch news:', err);
      setError('Failed to load latest news');
      
      // Ultimate fallback: static news
      setNews([
        {
          id: 1,
          title: "New Festival Season Announced",
          date: new Date().toISOString(),
          description: "Croatia prepares for an exciting summer of music and entertainment.",
          imageUrl: "/event-images/concert.jpg",
          category: "festival",
        },
        {
          id: 2,
          title: "Cultural Events Return to Historic Venues",
          date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          description: "Historic venues across Croatia reopen for cultural performances.",
          imageUrl: "/event-images/party.jpg",
          category: "culture",
        },
        {
          id: 3,
          title: "Tech Conference Circuit Expands",
          date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          description: "Major tech events announce dates for upcoming Croatian conferences.",
          imageUrl: "/event-images/conference.jpg",
          category: "technology",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  return (
    <section className="mb-12 bg-white rounded-lg shadow-lg p-6 border border-light-blue">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold font-sreda text-navy-blue">
          Latest News
        </h2>
        {error && (
          <Button variant="outline" size="sm" onClick={fetchNews} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Loading latest news...</span>
          </div>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <AlertCircle className="h-12 w-12 mx-auto text-red-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Failed to load news
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchNews}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        </div>
      ) : news.length === 0 ? (
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <CalendarIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No news available
            </h3>
            <p className="text-gray-600">Check back later for the latest updates</p>
          </div>
        </div>
      ) : (
        <Carousel
          opts={{
            align: "start",
            loop: true,
          }}
          className="w-full"
        >
          <CarouselContent className="-ml-2 md:-ml-4">
            {news.map((article) => (
              <CarouselItem
                key={article.id}
                className="pl-2 md:pl-4 basis-full sm:basis-1/2 md:basis-1/3 lg:basis-1/3"
              >
                <div className="h-full">
                  <NewsCard article={article} />
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>
          <div className="flex justify-end gap-2 mt-4">
            <CarouselPrevious className="static h-8 w-8 translate-y-0" />
            <CarouselNext className="static h-8 w-8 translate-y-0" />
          </div>
        </Carousel>
      )}
    </section>
  );
};

export default LatestNews;
