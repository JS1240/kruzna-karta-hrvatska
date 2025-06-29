import { useState, useEffect } from "react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Heart,
  ThumbsUp,
  Eye,
  Share,
  Star,
  Flame,
  Sparkles,
  Award,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { eventsApi } from "@/lib/api";

// Types for our popular items
interface PopularItem {
  id: string;
  title: string;
  category: string;
  image: string;
  likes: number;
  views: number;
  rating: number;
  trending: boolean;
  author: {
    name: string;
    avatar: string;
  };
  tags: string[];
}

const CATEGORIES = ["All", "Events", "Venues", "Activities", "Food"];

const Popular = () => {
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("trending");
  const [items, setItems] = useState<PopularItem[]>([]);
  const [likedItems, setLikedItems] = useState<Set<string>>(new Set());
  const [shake, setShake] = useState("");

  // Fetch real popular events data
  useEffect(() => {
    const fetchPopularData = async () => {
      setLoading(true);
      try {
        // Fetch events from API
        const response = await eventsApi.getEvents({ 
          skip: 0, 
          limit: 20,
          sort: 'popular' // Assuming API supports popularity sorting
        });
        
        // Transform API events to PopularItem format
        const popularItems: PopularItem[] = response.events.map(event => ({
          id: event.id.toString(),
          title: event.title || event.name || 'Untitled Event',
          category: mapEventCategoryToPopularCategory(event.category),
          image: event.image || '/event-images/placeholder.jpg',
          likes: Math.floor(Math.random() * 500) + 10, // TODO: Get real likes from API
          views: Math.floor(Math.random() * 10000) + 100, // TODO: Get real views from API
          rating: event.rating || (3 + Math.random() * 2),
          trending: Math.random() > 0.7, // TODO: Get real trending status from API
          author: {
            name: event.organizer?.name || 'Event Organizer',
            avatar: event.organizer?.avatar || `https://i.pravatar.cc/150?img=${Math.floor(Math.random() * 4) + 1}`,
          },
          tags: event.tags || generateRandomTags(),
        }));

        setItems(popularItems);
      } catch (error) {
        console.error('Failed to fetch popular events:', error);
        // Fallback to empty array for graceful degradation
        setItems([]);
        toast({
          title: "Error loading popular items",
          description: "Please try again later",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchPopularData();
  }, [selectedCategory, sortBy]);

  // Helper function to map event categories to popular page categories
  const mapEventCategoryToPopularCategory = (eventCategory: string): string => {
    const categoryMap: { [key: string]: string } = {
      'concert': 'Events',
      'festival': 'Events', 
      'conference': 'Events',
      'party': 'Events',
      'meetup': 'Activities',
      'workout': 'Activities',
      'sports': 'Activities',
      'restaurant': 'Food',
      'food': 'Food',
      'venue': 'Venues',
    };
    return categoryMap[eventCategory?.toLowerCase()] || 'Events';
  };

  // Helper function to generate random tags (TODO: should come from API)
  const generateRandomTags = (): string[] => {
    const allTags = [
      "Family Friendly", "Outdoor", "Local Favorites", "Historic",
      "Romantic", "Budget", "Luxury", "Adventure", "Relaxation",
      "Nightlife", "Cultural", "Scenic", "Beach", "Mountain",
    ];
    const numTags = Math.floor(Math.random() * 3) + 1;
    return allTags.sort(() => 0.5 - Math.random()).slice(0, numTags);
  };

  const handleLike = (id: string) => {
    setShake(id);
    setTimeout(() => setShake(""), 500);

    setItems(
      items.map((item) =>
        item.id === id
          ? {
              ...item,
              likes: likedItems.has(id) ? item.likes - 1 : item.likes + 1,
            }
          : item,
      ),
    );

    const newLikedItems = new Set(likedItems);
    if (likedItems.has(id)) {
      newLikedItems.delete(id);
      toast({
        title: "Removed from liked items",
        description: "You can always like it again later!",
      });
    } else {
      newLikedItems.add(id);
      toast({
        title: "Added to liked items",
        description: "Thanks for your feedback!",
      });
    }
    setLikedItems(newLikedItems);
  };

  const handleShare = (title: string) => {
    // Simulate sharing functionality
    toast({
      title: "Sharing " + title,
      description: "Links copied to clipboard!",
    });
  };

  const filteredItems = items.filter(
    (item) => selectedCategory === "All" || item.category === selectedCategory,
  );

  const sortedItems = [...filteredItems].sort((a, b) => {
    if (sortBy === "trending") return b.trending ? 1 : -1;
    if (sortBy === "mostLiked") return b.likes - a.likes;
    if (sortBy === "topRated") return b.rating - a.rating;
    return 0;
  });

  return (
    <>
      <Header />
      <div className="container mx-auto py-8 px-4 min-h-screen">
        <div className="flex flex-col space-y-6">
          <div className="text-center mb-8 animate-fade-in">
            <h1 className="text-4xl md:text-5xl font-bold text-brand-primary mb-4">
              Trending in Croatia
            </h1>
            <p className="text-lg text-gray-600">
              Discover the most popular attractions, events, and places loved by
              tourists and locals alike
            </p>
          </div>

          <div className="sticky top-16 z-10 bg-cream pt-4 pb-2 border-b border-gray-200">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                {CATEGORIES.map((category) => (
                  <Button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    variant={
                      selectedCategory === category ? "default" : "outline"
                    }
                    className="rounded-full transition-all hover:scale-105"
                  >
                    {category}
                  </Button>
                ))}
              </div>

              <Tabs
                defaultValue="trending"
                className="w-full md:w-auto"
                onValueChange={setSortBy}
              >
                <TabsList className="grid grid-cols-3 w-full md:w-auto">
                  <TabsTrigger
                    value="trending"
                    className="flex items-center gap-1"
                  >
                    <Flame className="h-4 w-4" /> Trending
                  </TabsTrigger>
                  <TabsTrigger
                    value="mostLiked"
                    className="flex items-center gap-1"
                  >
                    <ThumbsUp className="h-4 w-4" /> Most Liked
                  </TabsTrigger>
                  <TabsTrigger
                    value="topRated"
                    className="flex items-center gap-1"
                  >
                    <Star className="h-4 w-4" /> Top Rated
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {loading ? (
              // Skeleton loaders for cool loading state
              Array(8)
                .fill(0)
                .map((_, i) => (
                  <Card
                    key={i}
                    className="overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    <div className="relative">
                      <Skeleton className="w-full h-48" />
                    </div>
                    <CardContent className="pt-4">
                      <Skeleton className="h-6 w-3/4 mb-2" />
                      <Skeleton className="h-4 w-1/2 mb-4" />
                      <div className="flex gap-2 mb-4">
                        <Skeleton className="h-6 w-16 rounded-full" />
                        <Skeleton className="h-6 w-16 rounded-full" />
                      </div>
                      <div className="flex items-center gap-2">
                        <Skeleton className="h-10 w-10 rounded-full" />
                        <Skeleton className="h-4 w-24" />
                      </div>
                    </CardContent>
                  </Card>
                ))
            ) : sortedItems.length > 0 ? (
              sortedItems.map((item) => (
                <Card
                  key={item.id}
                  className="overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group"
                >
                  <div className="relative">
                    <AspectRatio ratio={16 / 9}>
                      <img
                        src={item.image}
                        alt={item.title}
                        className="object-cover w-full h-full transition-transform duration-700 group-hover:scale-105"
                      />
                    </AspectRatio>
                    {item.trending && (
                      <div className="absolute top-2 right-2">
                        <Badge
                          variant="accent-gold"
                          className="bg-accent-gold flex items-center gap-1 animate-pulse font-bold"
                        >
                          <Flame className="h-3 w-3" /> Hot
                        </Badge>
                      </div>
                    )}
                  </div>
                  <CardContent className="pt-4">
                    <h3 className="font-bold text-xl mb-1">{item.title}</h3>
                    <p className="text-gray-500 mb-3">{item.category}</p>
                    <div className="flex flex-wrap gap-2 mb-4">
                      {item.tags.map((tag) => (
                        <Badge
                          key={tag}
                          variant="accent-cream"
                          className="bg-accent-cream text-brand-black hover:bg-accent-gold transition-colors font-medium"
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={item.author.avatar} />
                        <AvatarFallback>{item.author.name[0]}</AvatarFallback>
                      </Avatar>
                      <span className="text-sm text-gray-600">
                        {item.author.name}
                      </span>
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between border-t pt-4">
                    <div className="flex gap-4">
                      <button
                        onClick={() => handleLike(item.id)}
                        className="flex items-center gap-1 text-gray-600 hover:text-red-500 transition-colors"
                      >
                        <Heart
                          className={`h-5 w-5 ${likedItems.has(item.id) ? "fill-red-500 text-red-500" : ""} ${shake === item.id ? "animate-[heartBeat_0.5s_ease-in-out]" : ""}`}
                        />
                        <span>{item.likes}</span>
                      </button>
                      <div className="flex items-center gap-1 text-gray-600">
                        <Eye className="h-5 w-5" />
                        <span>{item.views}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleShare(item.title)}
                      className="flex items-center gap-1 text-gray-600 hover:text-navy-blue transition-colors"
                    >
                      <Share className="h-5 w-5" />
                    </button>
                  </CardFooter>
                </Card>
              ))
            ) : (
              <div className="col-span-full flex flex-col items-center justify-center py-12">
                <Sparkles className="h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-xl font-medium text-gray-700">
                  No items found
                </h3>
                <p className="text-gray-500 mt-2">Try changing your filters</p>
              </div>
            )}
          </div>

          {!loading && sortedItems.length > 0 && (
            <div className="flex justify-center mt-8">
              <Button variant="outline" className="gap-2">
                <Sparkles className="h-4 w-4" />
                Load more places
              </Button>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </>
  );
};

// Note: Mock data generation function removed - now using real API data

// Add this to your tailwind.config.ts:
// keyframes: {
//   heartBeat: {
//     '0%': { transform: 'scale(1)' },
//     '50%': { transform: 'scale(1.3)' },
//     '100%': { transform: 'scale(1)' },
//   }
// },
// animation: {
//   'heartBeat': 'heartBeat 0.5s ease-in-out',
// }

export default Popular;
