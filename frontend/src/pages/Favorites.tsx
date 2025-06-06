import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar, MapPin, Heart, Bell, BellOff } from "lucide-react";
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

interface FavoriteEvent {
  id: number;
  title: string;
  date: string;
  time: string;
  venue: string;
  city: string;
  county: string;
  category: string;
  image: string;
  notifyEnabled: boolean;
}

// Mock data for favorite events
const mockFavorites: FavoriteEvent[] = [
  {
    id: 1,
    title: "Nina Badrić Concert",
    date: "2025-06-15",
    time: "20:00",
    venue: "Poljud Stadium",
    city: "Split",
    county: "Split-Dalmatia",
    category: "concert",
    image: "/event-images/concert.jpg",
    notifyEnabled: false,
  },
  {
    id: 4,
    title: "Adriatic Business Conference",
    date: "2025-09-05",
    time: "10:00",
    venue: "Rijeka Convention Center",
    city: "Rijeka",
    county: "Primorje-Gorski Kotar",
    category: "conference",
    image: "/event-images/conference.jpg",
    notifyEnabled: true,
  },
  {
    id: 5,
    title: "Zrće Beach Party",
    date: "2025-08-01",
    time: "23:00",
    venue: "Papaya Club",
    city: "Novalja",
    county: "Lika-Senj",
    category: "party",
    image: "/event-images/party.jpg",
    notifyEnabled: false,
  },
];

const Favorites = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [favoriteEvents, setFavoriteEvents] = useState<FavoriteEvent[]>([]);
  const [email, setEmail] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);

  useEffect(() => {
    // Check if user is logged in
    const loggedInStatus = localStorage.getItem("isLoggedIn") === "true";
    setIsLoggedIn(loggedInStatus);

    // Load favorite events from localStorage
    if (loggedInStatus) {
      const savedFavorites = localStorage.getItem("favoriteEvents");
      if (savedFavorites) {
        setFavoriteEvents(JSON.parse(savedFavorites));
      } else {
        // Use mock data for demonstration
        setFavoriteEvents(mockFavorites);
        localStorage.setItem("favoriteEvents", JSON.stringify(mockFavorites));
      }

      // Get saved email for notifications
      const savedEmail = localStorage.getItem("notificationEmail");
      if (savedEmail) {
        setEmail(savedEmail);
      }
    }

    // Listen for auth state changes
    const handleAuthChange = (e: CustomEvent) => {
      setIsLoggedIn(e.detail.isLoggedIn);
      if (!e.detail.isLoggedIn) {
        setFavoriteEvents([]);
      } else {
        const savedFavorites = localStorage.getItem("favoriteEvents");
        if (savedFavorites) {
          setFavoriteEvents(JSON.parse(savedFavorites));
        } else {
          setFavoriteEvents(mockFavorites);
          localStorage.setItem("favoriteEvents", JSON.stringify(mockFavorites));
        }
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
  }, []);

  const handleRemoveFavorite = (id: number) => {
    const updatedFavorites = favoriteEvents.filter((event) => event.id !== id);
    setFavoriteEvents(updatedFavorites);
    localStorage.setItem("favoriteEvents", JSON.stringify(updatedFavorites));

    toast({
      title: "Removed from favorites",
      description: "Event has been removed from your favorites",
    });
  };

  const openNotificationDialog = (id: number) => {
    setSelectedEventId(id);
    setIsDialogOpen(true);
  };

  const handleToggleNotification = (id: number) => {
    const event = favoriteEvents.find((e) => e.id === id);

    if (event?.notifyEnabled) {
      // If notifications are already enabled, just toggle off
      const updatedFavorites = favoriteEvents.map((event) =>
        event.id === id ? { ...event, notifyEnabled: false } : event,
      );
      setFavoriteEvents(updatedFavorites);
      localStorage.setItem("favoriteEvents", JSON.stringify(updatedFavorites));

      toast({
        title: "Notifications disabled",
        description: "You will no longer receive notifications for this event",
      });
    } else {
      // If notifications are disabled, open dialog to collect email
      openNotificationDialog(id);
    }
  };

  const handleSaveNotification = () => {
    if (!email) {
      toast({
        title: "Email required",
        description: "Please enter your email to receive notifications",
        variant: "destructive",
      });
      return;
    }

    // Save the email
    localStorage.setItem("notificationEmail", email);

    // Enable notification for the selected event
    if (selectedEventId) {
      const updatedFavorites = favoriteEvents.map((event) =>
        event.id === selectedEventId
          ? { ...event, notifyEnabled: true }
          : event,
      );
      setFavoriteEvents(updatedFavorites);
      localStorage.setItem("favoriteEvents", JSON.stringify(updatedFavorites));

      const event = favoriteEvents.find((e) => e.id === selectedEventId);

      toast({
        title: "Notifications enabled",
        description: `You will receive notifications for "${event?.title}"`,
      });
    }

    setIsDialogOpen(false);
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
          <h1 className="text-3xl font-bold text-navy-blue mb-2 font-sreda">
            Your Favorite Events
          </h1>
          <p className="text-lg text-gray-600">
            Manage your favorite events and notifications
          </p>
        </div>

        {favoriteEvents.length === 0 ? (
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
            {favoriteEvents.map((event) => (
              <Card key={event.id} className="overflow-hidden">
                <div className="relative h-48">
                  <img
                    src={event.image}
                    alt={event.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2">
                    <Button
                      variant="secondary"
                      size="icon"
                      className="bg-white/80 hover:bg-white text-navy-blue"
                      onClick={() => handleRemoveFavorite(event.id)}
                    >
                      <Heart className="h-4 w-4 fill-navy-blue" />
                    </Button>
                  </div>
                </div>

                <CardHeader>
                  <CardTitle>{event.title}</CardTitle>
                </CardHeader>

                <CardContent className="space-y-2">
                  <div className="flex items-center text-sm">
                    <Calendar className="mr-2 h-4 w-4" />
                    <span>
                      {new Date(event.date).toLocaleDateString()} at{" "}
                      {event.time}
                    </span>
                  </div>
                  <div className="flex items-center text-sm">
                    <MapPin className="mr-2 h-4 w-4" />
                    <span>
                      {event.venue}, {event.city}
                    </span>
                  </div>
                </CardContent>

                <CardFooter className="justify-between">
                  <Button variant="outline" asChild>
                    <a href={`#event-${event.id}`}>View Details</a>
                  </Button>

                  <Button
                    variant={event.notifyEnabled ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleToggleNotification(event.id)}
                  >
                    {event.notifyEnabled ? (
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
                    {favoriteEvents.map((event) => (
                      <TableRow key={event.id}>
                        <TableCell className="font-medium">
                          {event.title}
                        </TableCell>
                        <TableCell>
                          {new Date(event.date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>{event.venue}</TableCell>
                        <TableCell>
                          {event.notifyEnabled ? (
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
                            onClick={() => handleToggleNotification(event.id)}
                          >
                            {event.notifyEnabled ? "Disable" : "Enable"}
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
