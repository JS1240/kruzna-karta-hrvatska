import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import EventCard from "@/components/EventCard";
import ShareButton from "@/components/ShareButton";
import { getCurrentUser } from "@/lib/auth";
import { favoritesApi, FavoriteEvent } from "@/lib/api";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar, MapPin, Heart, Bell, BellOff, Grid, List, Filter, SortAsc, Loader2, RefreshCw } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

// Helper function to format date
const formatEventDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long', 
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
};

const Favorites = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [favoriteEvents, setFavoriteEvents] = useState<FavoriteEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'dateAdded' | 'rating'>('date');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredEvents, setFilteredEvents] = useState<FavoriteEvent[]>([]);
  
  const user = getCurrentUser();

  const fetchFavorites = async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const favorites = await favoritesApi.getUserFavorites(user.id);
      setFavoriteEvents(favorites);
      
      // Get saved email for notifications
      const savedEmail = localStorage.getItem("notificationEmail");
      if (savedEmail) {
        setEmail(savedEmail);
      }
    } catch (err) {
      console.error('Failed to fetch favorites:', err);
      setError('Failed to load your favorite events');
      
      // Fallback: try to load from localStorage as backup
      const savedFavorites = localStorage.getItem("favoriteEvents");
      if (savedFavorites) {
        try {
          const parsed = JSON.parse(savedFavorites);
          setFavoriteEvents(parsed);
        } catch {
          setFavoriteEvents([]);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check if user is logged in
    const loggedInStatus = localStorage.getItem("isLoggedIn") === "true";
    setIsLoggedIn(loggedInStatus);

    if (loggedInStatus && user) {
      fetchFavorites();
    } else {
      setLoading(false);
    }

    // Listen for auth state changes
    const handleAuthChange = (e: CustomEvent) => {
      setIsLoggedIn(e.detail.isLoggedIn);
      if (!e.detail.isLoggedIn) {
        setFavoriteEvents([]);
        setLoading(false);
      } else if (user) {
        fetchFavorites();
      }
    };

    window.addEventListener(
      "authStateChanged",
      handleAuthChange as EventListener,
    );

    return () => {
      window.removeEventListener(
        "authStateChanged",
        handleAuthChange as EventListener,
      );
    };
  }, [user]);

  const handleRemoveFavorite = async (favoriteId: number) => {
    if (!user) return;

    const favorite = favoriteEvents.find(f => f.id === favoriteId);
    if (!favorite) return;

    try {
      // Optimistically remove from UI
      setFavoriteEvents(prev => prev.filter(f => f.id !== favoriteId));
      
      // Remove from backend
      await favoritesApi.removeFromFavorites(user.id, favorite.eventId);
      
      toast({
        title: "Removed from favorites",
        description: "Event has been removed from your favorites",
      });
    } catch (error) {
      console.error('Failed to remove favorite:', error);
      
      // Revert optimistic update on error
      setFavoriteEvents(prev => [...prev, favorite]);
      
      toast({
        title: "Failed to remove",
        description: "Could not remove event from favorites. Please try again.",
        variant: "destructive",
      });
    }
  };

  const openNotificationDialog = (id: number) => {
    setSelectedEventId(id);
    setIsDialogOpen(true);
  };

  const handleToggleNotification = async (favoriteId: number) => {
    if (!user) return;

    const favorite = favoriteEvents.find((f) => f.id === favoriteId);
    if (!favorite) return;

    try {
      if (favorite.notifyEnabled) {
        // Disable notifications
        await favoritesApi.updateFavorite(user.id, favorite.eventId, { 
          notifyEnabled: false 
        });
        
        setFavoriteEvents(prev => prev.map(f => 
          f.id === favoriteId ? { ...f, notifyEnabled: false } : f
        ));

        toast({
          title: "Notifications disabled",
          description: "You will no longer receive notifications for this event",
        });
      } else {
        // Enable notifications - open dialog to collect email
        openNotificationDialog(favoriteId);
      }
    } catch (error) {
      console.error('Failed to update notification settings:', error);
      toast({
        title: "Failed to update",
        description: "Could not update notification settings. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleSaveNotification = async () => {
    if (!email || !user || !selectedEventId) {
      toast({
        title: "Email required",
        description: "Please enter your email to receive notifications",
        variant: "destructive",
      });
      return;
    }

    const favorite = favoriteEvents.find(f => f.id === selectedEventId);
    if (!favorite) return;

    try {
      // Save the email
      localStorage.setItem("notificationEmail", email);

      // Enable notification for the selected event
      await favoritesApi.updateFavorite(user.id, favorite.eventId, { 
        notifyEnabled: true 
      });
      
      setFavoriteEvents(prev => prev.map(f => 
        f.id === selectedEventId ? { ...f, notifyEnabled: true } : f
      ));

      toast({
        title: "Notifications enabled",
        description: `You will receive notifications for "${favorite.event.title || favorite.event.name}"`,
      });
      
      setIsDialogOpen(false);
    } catch (error) {
      console.error('Failed to enable notifications:', error);
      toast({
        title: "Failed to enable notifications",
        description: "Could not enable notifications. Please try again.",
        variant: "destructive",
      });
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex flex-col bg-cream">
        <Header />

        <main className="flex-grow container mx-auto px-4 py-8">
          <div className="text-center py-16">
            <Heart className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h1 className="text-3xl font-bold text-navy-blue mb-2">
              Your Favorites
            </h1>
            <p className="text-lg text-gray-600 mb-6">
              Please log in to view and manage your favorite events
            </p>
            <Button onClick={() => window.history.back()}>Go Back</Button>
          </div>
        </main>

        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />

      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-navy-blue mb-2 font-sreda">
                Your Favorite Events
              </h1>
              <p className="text-lg text-gray-600">
                Manage your favorite events and notifications
              </p>
            </div>
            {error && (
              <Button variant="outline" onClick={fetchFavorites} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading your favorite events...</span>
            </div>
          </div>
        ) : error ? (
          <div className="text-center py-16">
            <Heart className="w-16 h-16 mx-auto text-red-400 mb-4" />
            <h2 className="text-2xl font-bold text-navy-blue mb-2">
              Failed to load favorites
            </h2>
            <p className="text-lg text-gray-600 mb-6">
              {error}
            </p>
            <Button onClick={fetchFavorites}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        ) : favoriteEvents.length === 0 ? (
          <div className="text-center py-16">
            <Heart className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h2 className="text-2xl font-bold text-navy-blue mb-2">
              No favorites yet
            </h2>
            <p className="text-lg text-gray-600 mb-6">
              Start exploring events and add them to your favorites
            </p>
            <Button asChild>
              <a href="/">Explore Events</a>
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {favoriteEvents.map((favorite) => (
              <Card key={favorite.id} className="overflow-hidden">
                <div className="relative h-48">
                  <img
                    src={favorite.event.image || '/event-images/concert.jpg'}
                    alt={favorite.event.title || favorite.event.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2">
                    <Button
                      variant="secondary"
                      size="icon"
                      className="bg-white/80 hover:bg-white text-navy-blue"
                      onClick={() => handleRemoveFavorite(favorite.id)}
                    >
                      <Heart className="h-4 w-4 fill-navy-blue" />
                    </Button>
                  </div>
                </div>

                <CardHeader>
                  <CardTitle>{favorite.event.title || favorite.event.name}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      Added {formatEventDate(favorite.dateAdded)}
                    </Badge>
                    {favorite.event.price && (
                      <Badge variant="secondary" className="text-xs">
                        {favorite.event.price}
                      </Badge>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-2">
                  <div className="flex items-center text-sm">
                    <Calendar className="mr-2 h-4 w-4" />
                    <span>
                      {formatEventDate(favorite.event.date)} {favorite.event.time && `at ${favorite.event.time}`}
                    </span>
                  </div>
                  <div className="flex items-center text-sm">
                    <MapPin className="mr-2 h-4 w-4" />
                    <span>{favorite.event.location}</span>
                  </div>
                  {favorite.event.description && (
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {favorite.event.description}
                    </p>
                  )}
                </CardContent>

                <CardFooter className="justify-between">
                  <Button variant="outline" asChild>
                    <a href={`/events/${favorite.eventId}`}>View Details</a>
                  </Button>

                  <Button
                    variant={favorite.notifyEnabled ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleToggleNotification(favorite.id)}
                  >
                    {favorite.notifyEnabled ? (
                      <>
                        <BellOff className="mr-1 h-4 w-4" />
                        Turn Off
                      </>
                    ) : (
                      <>
                        <Bell className="mr-1 h-4 w-4" />
                        Notify
                      </>
                    )}
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {favoriteEvents.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-navy-blue mb-4 font-sreda">
              Notification Settings
            </h2>
            <Card>
              <CardContent className="pt-6">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Event</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Venue</TableHead>
                      <TableHead>Notifications</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {favoriteEvents.map((favorite) => (
                      <TableRow key={favorite.id}>
                        <TableCell className="font-medium">
                          {favorite.event.title || favorite.event.name}
                        </TableCell>
                        <TableCell>
                          {formatEventDate(favorite.event.date)}
                        </TableCell>
                        <TableCell>{favorite.event.location}</TableCell>
                        <TableCell>
                          {favorite.notifyEnabled ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Enabled
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              Disabled
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleNotification(favorite.id)}
                          >
                            {favorite.notifyEnabled ? "Disable" : "Enable"}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Enable Event Notifications</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-gray-500 mb-4">
              Enter your email address to receive notifications about this
              event, including reminders and updates.
            </p>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  placeholder="your.email@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button onClick={handleSaveNotification}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Footer />
    </div>
  );
};

export default Favorites;
