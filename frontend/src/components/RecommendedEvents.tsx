import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import EventCard from './EventCard';
import { useRecommendations, RecommendedEvent } from '@/hooks/useRecommendations';
import { TrendingUp, MapPin, Lightbulb, RefreshCw, Star, Calendar, Users } from 'lucide-react';
import { getCurrentUser } from '@/lib/auth';

interface RecommendedEventsProps {
  className?: string;
}

const RecommendedEvents: React.FC<RecommendedEventsProps> = ({ className = '' }) => {
  const {
    recommendations,
    trendingEvents,
    nearbyEvents,
    loading,
    refreshRecommendations,
    trackEventView,
    trackEventInteraction,
  } = useRecommendations();

  const user = getCurrentUser();

  if (!user) {
    return (
      <Card className={className}>
        <CardContent className="py-8 text-center">
          <Lightbulb className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Get Personalized Recommendations
          </h3>
          <p className="text-gray-600 mb-4">
            Log in to see events tailored just for you based on your interests and location.
          </p>
        </CardContent>
      </Card>
    );
  }

  const handleEventClick = (eventId: string) => {
    trackEventView(eventId);
    trackEventInteraction(eventId, 'click');
  };

  const handleFavoriteToggle = (eventId: string) => {
    trackEventInteraction(eventId, 'favorite');
  };

  const getReasonIcon = (type: string) => {
    switch (type) {
      case 'category':
        return <Star className="h-3 w-3" />;
      case 'location':
        return <MapPin className="h-3 w-3" />;
      case 'similar_events':
        return <Lightbulb className="h-3 w-3" />;
      case 'trending':
        return <TrendingUp className="h-3 w-3" />;
      case 'time_preference':
        return <Calendar className="h-3 w-3" />;
      default:
        return <Star className="h-3 w-3" />;
    }
  };

  const getReasonColor = (type: string) => {
    switch (type) {
      case 'category':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'location':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'similar_events':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'trending':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'time_preference':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <div className="h-6 bg-gray-200 rounded animate-pulse w-1/3"></div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((j) => (
                  <div key={j} className="h-64 bg-gray-200 rounded-lg animate-pulse"></div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Personalized Recommendations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-purple-500" />
              Recommended for You
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={refreshRecommendations}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recommendations.length === 0 ? (
            <div className="text-center py-8">
              <Lightbulb className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Building Your Recommendations
              </h3>
              <p className="text-gray-600">
                Browse some events to help us understand your preferences and get better recommendations.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {recommendations.map((event) => (
                <div key={event.id} className="relative">
                  {/* Recommendation Reason */}
                  <div className="mb-3">
                    <Badge 
                      variant="outline" 
                      className={`${getReasonColor(event.reason.type)} border text-xs`}
                    >
                      {getReasonIcon(event.reason.type)}
                      <span className="ml-1">{event.reason.description}</span>
                    </Badge>
                    <div className="text-xs text-gray-500 mt-1">
                      Match score: {event.score}%
                    </div>
                  </div>
                  
                  {/* Event Card */}
                  <EventCard
                    id={event.id}
                    title={event.title}
                    image={event.image}
                    date={`${event.date} at ${event.time}`}
                    location={`${event.venue}, ${event.city}`}
                    category={event.category}
                    price={event.price}
                    description={event.description}
                    isFavorite={false}
                    onFavoriteToggle={handleFavoriteToggle}
                    className="border-l-4 border-l-purple-500"
                  />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trending Events */}
      {trendingEvents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-orange-500" />
              Trending Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {trendingEvents.map((event) => (
                <div key={event.id} className="relative">
                  <div className="absolute top-2 left-2 z-10">
                    <Badge className="bg-orange-500 text-white">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      Trending
                    </Badge>
                  </div>
                  <EventCard
                    id={event.id}
                    title={event.title}
                    image={event.image}
                    date={`${event.date} at ${event.time}`}
                    location={`${event.venue}, ${event.city}`}
                    category={event.category}
                    price={event.price}
                    description={event.description}
                    isFavorite={false}
                    onFavoriteToggle={handleFavoriteToggle}
                  />
                  {event.attendeeCount && (
                    <div className="absolute bottom-2 right-2">
                      <Badge variant="accent-cream" className="bg-accent-cream/90 text-brand-black">
                        <Users className="h-3 w-3 mr-1" />
                        {event.attendeeCount.toLocaleString()}
                      </Badge>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Nearby Events */}
      {nearbyEvents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-blue-500" />
              Events Near You
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {nearbyEvents.map((event) => (
                <div key={event.id} className="relative">
                  <div className="absolute top-2 left-2 z-10">
                    <Badge variant="accent-cream" className="bg-accent-cream text-brand-black font-medium">
                      <MapPin className="h-3 w-3 mr-1" />
                      Nearby
                    </Badge>
                  </div>
                  <EventCard
                    id={event.id}
                    title={event.title}
                    image={event.image}
                    date={`${event.date} at ${event.time}`}
                    location={`${event.venue}, ${event.city}`}
                    category={event.category}
                    price={event.price}
                    description={event.description}
                    isFavorite={false}
                    onFavoriteToggle={handleFavoriteToggle}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendation Tips */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Lightbulb className="h-5 w-5 text-purple-500 mt-0.5" />
            <div>
              <h4 className="font-medium text-purple-900 mb-2">
                How we recommend events for you
              </h4>
              <ul className="text-sm text-purple-700 space-y-1">
                <li>• Events in categories you've shown interest in</li>
                <li>• Popular events in your preferred locations</li>
                <li>• Events similar to ones you've favorited before</li>
                <li>• Trending events with high ratings and attendance</li>
              </ul>
              <p className="text-xs text-purple-600 mt-3">
                The more you interact with events, the better our recommendations become!
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RecommendedEvents;