import React, { useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  EventTabs,
  EventTabsList,
  EventTabsTrigger,
  EventTabsContent,
} from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  MapPin,
  Users,
  Music,
  Utensils,
  Star,
  Calendar,
  Mail,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { debugLog } from "@/lib/debug";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
  DialogFooter,
} from "@/components/ui/dialog";

interface Venue {
  id: number;
  name: string;
  city: string;
  county: string;
  address: string;
  category:
    | "hotel"
    | "concert-hall"
    | "conference-center"
    | "club"
    | "restaurant"
    | "outdoor";
  capacity: number;
  priceRange: 1 | 2 | 3 | 4 | 5; // 1 = $ to 5 = $$$$$
  amenities: string[];
  imageUrl: string;
  rating: number;
  description: string;
}

const Venues = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCounty, setSelectedCounty] = useState<string>("");
  const [selectedCapacity, setSelectedCapacity] = useState<number[]>([100]);
  const [activeTab, setActiveTab] = useState<string>("all");
  const [selectedVenue, setSelectedVenue] = useState<Venue | null>(null);
  const [contactDialog, setContactDialog] = useState(false);
  const [contactForm, setContactForm] = useState({
    name: "",
    email: "",
    phone: "",
    eventDate: "",
    message: "",
  });

  // Mock data for venues
  const venues: Venue[] = [
    {
      id: 1,
      name: "Lisinski Concert Hall",
      city: "Zagreb",
      county: "Zagreb",
      address: "Trg Stjepana Radića 4, 10000 Zagreb",
      category: "concert-hall",
      capacity: 1800,
      priceRange: 4,
      amenities: [
        "Stage",
        "Sound System",
        "Lighting",
        "Parking",
        "Wheelchair Access",
      ],
      imageUrl: "/event-images/concert.jpg",
      rating: 4.8,
      description:
        "Croatia's premier concert hall with excellent acoustics and modern facilities, perfect for classical concerts, operas, and large musical performances.",
    },
    {
      id: 2,
      name: "Westin Zagreb Hotel",
      city: "Zagreb",
      county: "Zagreb",
      address: "Krsnjavoga 1, 10000 Zagreb",
      category: "hotel",
      capacity: 500,
      priceRange: 5,
      amenities: [
        "Catering",
        "A/V Equipment",
        "Wifi",
        "Accommodation",
        "Parking",
      ],
      imageUrl: "/event-images/conference.jpg",
      rating: 4.5,
      description:
        "Five-star hotel with elegant ballrooms and conference spaces ideal for corporate events, weddings, and social gatherings.",
    },
    {
      id: 3,
      name: "Papaya Club",
      city: "Novalja",
      county: "Lika-Senj",
      address: "Zrće Beach, 53291 Novalja",
      category: "club",
      capacity: 4000,
      priceRange: 3,
      amenities: ["DJ Booth", "Sound System", "Lighting", "Bar", "VIP Areas"],
      imageUrl: "/event-images/party.jpg",
      rating: 4.6,
      description:
        "Iconic open-air club on Zrće Beach, known for hosting world-famous DJs and summer parties.",
    },
    {
      id: 4,
      name: "Šibenik Fortress",
      city: "Šibenik",
      county: "Šibenik-Knin",
      address: "Zagrađe 21, 22000 Šibenik",
      category: "outdoor",
      capacity: 1000,
      priceRange: 3,
      amenities: ["Historic Setting", "Open-air Stage", "Stunning Views"],
      imageUrl: "/event-images/concert.jpg",
      rating: 4.9,
      description:
        "Historic medieval fortress offering a unique venue for cultural events, concerts, and festivals with breathtaking views of the Adriatic.",
    },
    {
      id: 5,
      name: "Split Convention Centre",
      city: "Split",
      county: "Split-Dalmatia",
      address: "Poljička cesta 35, 21000 Split",
      category: "conference-center",
      capacity: 1200,
      priceRange: 4,
      amenities: [
        "Multiple Halls",
        "A/V Equipment",
        "Catering",
        "Translation Services",
      ],
      imageUrl: "/event-images/conference.jpg",
      rating: 4.3,
      description:
        "Modern convention center with versatile spaces for conferences, trade shows, and corporate events in the heart of Split.",
    },
    {
      id: 6,
      name: "Restaurant Dubravkin Put",
      city: "Zagreb",
      county: "Zagreb",
      address: "Dubravkin put 2, 10000 Zagreb",
      category: "restaurant",
      capacity: 150,
      priceRange: 4,
      amenities: [
        "Gourmet Catering",
        "Terrace",
        "Private Dining",
        "Wine Cellar",
      ],
      imageUrl: "/event-images/conference.jpg",
      rating: 4.7,
      description:
        "Upscale restaurant with elegant indoor space and garden terrace, perfect for intimate gatherings and private celebrations.",
    },
    {
      id: 7,
      name: "Hvar Public Theatre",
      city: "Hvar",
      county: "Split-Dalmatia",
      address: "Trg Sv. Stjepana, 21450 Hvar",
      category: "concert-hall",
      capacity: 300,
      priceRange: 3,
      amenities: ["Historic Building", "Stage", "Sound System"],
      imageUrl: "/event-images/concert.jpg",
      rating: 4.4,
      description:
        "One of Europe's oldest theaters dating from 1612, offering a unique historical venue for cultural events and performances.",
    },
  ];

  // Counties in Croatia
  const counties = [
    "Zagreb",
    "Split-Dalmatia",
    "Dubrovnik-Neretva",
    "Istria",
    "Primorje-Gorski Kotar",
    "Zadar",
    "Šibenik-Knin",
    "Lika-Senj",
  ];

  const handleTabChange = (value: string) => {
    setActiveTab(value);
  };

  const handleCapacityChange = (value: number[]) => {
    setSelectedCapacity(value);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    toast({
      title: "Search Results",
      description: `Showing venues matching "${searchQuery}"`,
    });
  };

  const handleVenueSelect = (venue: Venue) => {
    setSelectedVenue(venue);
  };

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    debugLog("Contact form submitted:", contactForm);

    toast({
      title: "Request Sent",
      description:
        "Your venue inquiry has been sent. The venue will contact you shortly.",
    });

    setContactDialog(false);
    setContactForm({
      name: "",
      email: "",
      phone: "",
      eventDate: "",
      message: "",
    });
  };

  // Filter venues based on search, county, capacity, and category
  const filteredVenues = venues.filter((venue) => {
    const matchesSearch =
      venue.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      venue.city.toLowerCase().includes(searchQuery.toLowerCase()) ||
      venue.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCounty = selectedCounty
      ? venue.county === selectedCounty
      : true;

    const matchesCapacity = venue.capacity >= selectedCapacity[0];

    const matchesCategory = activeTab === "all" || venue.category === activeTab;

    return matchesSearch && matchesCounty && matchesCapacity && matchesCategory;
  });

  // Helper function to render price range
  const renderPriceRange = (range: number) => {
    return "€".repeat(range);
  };

  // Helper function to render category icon
  const renderCategoryIcon = (category: string) => {
    switch (category) {
      case "hotel":
        return <MapPin className="w-5 h-5" />;
      case "concert-hall":
        return <Music className="w-5 h-5" />;
      case "conference-center":
        return <Users className="w-5 h-5" />;
      case "club":
        return <Music className="w-5 h-5" />;
      case "restaurant":
        return <Utensils className="w-5 h-5" />;
      case "outdoor":
        return <MapPin className="w-5 h-5" />;
      default:
        return <MapPin className="w-5 h-5" />;
    }
  };

  // Helper function to format category name
  const formatCategoryName = (category: string) => {
    return category
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />

      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-navy-blue mb-2 font-sreda">
            Explore Venues in Croatia
          </h1>
          <p className="text-lg text-gray-600">
            Discover perfect venues for your events - from historical theaters
            to modern conference centers
          </p>
        </div>

        {/* Search and filter section */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <form
              onSubmit={handleSearch}
              className="flex flex-col md:flex-row gap-4"
            >
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search venues by name, city or features..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <div className="w-full md:w-48">
                <Select
                  value={selectedCounty}
                  onValueChange={setSelectedCounty}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="County" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Counties</SelectItem>
                    {counties.map((county) => (
                      <SelectItem key={county} value={county}>
                        {county}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit">Search</Button>
            </form>

            <div className="mt-6">
              <Label className="mb-2 block">
                Minimum Capacity: {selectedCapacity[0]} people
              </Label>
              <Slider
                value={selectedCapacity}
                onValueChange={handleCapacityChange}
                max={5000}
                step={50}
                className="py-4"
              />
            </div>

            <div className="mt-4">
              <EventTabs value={activeTab} onValueChange={handleTabChange}>
                <EventTabsList className="w-full mb-6">
                  <EventTabsTrigger value="all">All Venues</EventTabsTrigger>
                  <EventTabsTrigger value="hotel">Hotels</EventTabsTrigger>
                  <EventTabsTrigger value="concert-hall">
                    Concert Halls
                  </EventTabsTrigger>
                  <EventTabsTrigger value="conference-center">
                    Conference Centers
                  </EventTabsTrigger>
                  <EventTabsTrigger value="club">Clubs</EventTabsTrigger>
                  <EventTabsTrigger value="restaurant">
                    Restaurants
                  </EventTabsTrigger>
                  <EventTabsTrigger value="outdoor">
                    Outdoor Venues
                  </EventTabsTrigger>
                </EventTabsList>
              </EventTabs>
            </div>
          </CardContent>
        </Card>

        {/* Venues grid */}
        {filteredVenues.length === 0 ? (
          <div className="text-center py-16">
            <MapPin className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h2 className="text-2xl font-bold text-navy-blue mb-2">
              No venues found
            </h2>
            <p className="text-lg text-gray-600 mb-6">
              Try adjusting your filters or search query
            </p>
            <Button
              onClick={() => {
                setSearchQuery("");
                setSelectedCounty("");
                setSelectedCapacity([100]);
                setActiveTab("all");
              }}
            >
              Reset Filters
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredVenues.map((venue) => (
              <Card
                key={venue.id}
                className="overflow-hidden h-full flex flex-col"
              >
                <div className="relative h-48">
                  <img
                    src={venue.imageUrl}
                    alt={venue.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2">
                    <Badge className="bg-navy-blue">
                      {renderCategoryIcon(venue.category)}
                      <span className="ml-1">
                        {formatCategoryName(venue.category)}
                      </span>
                    </Badge>
                  </div>
                </div>

                <CardHeader className="pb-2">
                  <CardTitle className="flex justify-between items-start">
                    <span>{venue.name}</span>
                    <div className="flex items-center text-yellow-500">
                      <Star className="fill-yellow-500 h-4 w-4" />
                      <span className="ml-1 text-sm">{venue.rating}</span>
                    </div>
                  </CardTitle>
                  <CardDescription>
                    <div className="flex items-center">
                      <MapPin className="h-4 w-4 mr-1" />
                      {venue.city}, {venue.county}
                    </div>
                  </CardDescription>
                </CardHeader>

                <CardContent className="pb-2 flex-grow">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Capacity:</span>
                      <span className="text-sm font-medium">
                        {venue.capacity} people
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">
                        Price Range:
                      </span>
                      <span className="text-sm font-medium">
                        {renderPriceRange(venue.priceRange)}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500 block mb-1">
                        Amenities:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {venue.amenities.slice(0, 3).map((amenity, index) => (
                          <Badge
                            key={index}
                            variant="outline"
                            className="text-xs"
                          >
                            {amenity}
                          </Badge>
                        ))}
                        {venue.amenities.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{venue.amenities.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>

                <CardFooter className="pt-2">
                  <div className="w-full flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => handleVenueSelect(venue)}
                    >
                      Details
                    </Button>
                    <Button
                      className="flex-1"
                      onClick={() => {
                        setSelectedVenue(venue);
                        setContactDialog(true);
                      }}
                    >
                      Contact
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {/* Venue details dialog */}
        {selectedVenue && (
          <Dialog
            open={!!selectedVenue}
            onOpenChange={(open) => !open && setSelectedVenue(null)}
          >
            <DialogContent className="sm:max-w-[700px]">
              <DialogHeader>
                <DialogTitle className="text-xl">
                  {selectedVenue.name}
                </DialogTitle>
              </DialogHeader>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
                <div>
                  <img
                    src={selectedVenue.imageUrl}
                    alt={selectedVenue.name}
                    className="w-full h-48 object-cover rounded-md"
                  />

                  <div className="mt-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <MapPin className="h-4 w-4 mr-1 text-navy-blue" />
                        <span>
                          {selectedVenue.city}, {selectedVenue.county}
                        </span>
                      </div>
                      <div className="flex items-center text-yellow-500">
                        <Star className="fill-yellow-500 h-4 w-4" />
                        <span className="ml-1">{selectedVenue.rating}</span>
                      </div>
                    </div>

                    <p className="text-sm text-gray-700">
                      {selectedVenue.address}
                    </p>

                    <div className="pt-2">
                      <h3 className="font-semibold mb-1">Venue Details</h3>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500">Type:</span>
                          <span className="ml-1 font-medium">
                            {formatCategoryName(selectedVenue.category)}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Capacity:</span>
                          <span className="ml-1 font-medium">
                            {selectedVenue.capacity} people
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Price Range:</span>
                          <span className="ml-1 font-medium">
                            {renderPriceRange(selectedVenue.priceRange)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Description</h3>
                  <p className="text-sm text-gray-700 mb-4">
                    {selectedVenue.description}
                  </p>

                  <h3 className="font-semibold mb-2">Amenities & Services</h3>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {selectedVenue.amenities.map((amenity, index) => (
                      <Badge key={index} variant="outline">
                        {amenity}
                      </Badge>
                    ))}
                  </div>

                  <h3 className="font-semibold mb-2">Perfect For</h3>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {selectedVenue.category === "concert-hall" && (
                      <>
                        <Badge variant="secondary">Concerts</Badge>
                        <Badge variant="secondary">Performances</Badge>
                        <Badge variant="secondary">Cultural Events</Badge>
                      </>
                    )}
                    {selectedVenue.category === "hotel" && (
                      <>
                        <Badge variant="secondary">Corporate Events</Badge>
                        <Badge variant="secondary">Weddings</Badge>
                        <Badge variant="secondary">Galas</Badge>
                      </>
                    )}
                    {selectedVenue.category === "conference-center" && (
                      <>
                        <Badge variant="secondary">Conferences</Badge>
                        <Badge variant="secondary">Trade Shows</Badge>
                        <Badge variant="secondary">Seminars</Badge>
                      </>
                    )}
                    {selectedVenue.category === "club" && (
                      <>
                        <Badge variant="secondary">Parties</Badge>
                        <Badge variant="secondary">DJ Events</Badge>
                        <Badge variant="secondary">Private Events</Badge>
                      </>
                    )}
                    {selectedVenue.category === "restaurant" && (
                      <>
                        <Badge variant="secondary">Private Dining</Badge>
                        <Badge variant="secondary">Celebrations</Badge>
                        <Badge variant="secondary">Business Meals</Badge>
                      </>
                    )}
                    {selectedVenue.category === "outdoor" && (
                      <>
                        <Badge variant="secondary">Festivals</Badge>
                        <Badge variant="secondary">Open-air Events</Badge>
                        <Badge variant="secondary">Cultural Events</Badge>
                      </>
                    )}
                  </div>

                  <Button
                    className="w-full mt-4"
                    onClick={() => {
                      setContactDialog(true);
                    }}
                  >
                    <Mail className="mr-2 h-4 w-4" />
                    Contact This Venue
                  </Button>
                </div>
              </div>

              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Close</Button>
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* Contact venue dialog */}
        <Dialog open={contactDialog} onOpenChange={setContactDialog}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Contact Venue</DialogTitle>
            </DialogHeader>

            <form onSubmit={handleContactSubmit}>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Your Name</Label>
                  <Input
                    id="name"
                    value={contactForm.name}
                    onChange={(e) =>
                      setContactForm({ ...contactForm, name: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={contactForm.email}
                    onChange={(e) =>
                      setContactForm({ ...contactForm, email: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    value={contactForm.phone}
                    onChange={(e) =>
                      setContactForm({ ...contactForm, phone: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="eventDate">Event Date (if known)</Label>
                  <Input
                    id="eventDate"
                    type="date"
                    value={contactForm.eventDate}
                    onChange={(e) =>
                      setContactForm({
                        ...contactForm,
                        eventDate: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="message">Message</Label>
                  <textarea
                    id="message"
                    rows={4}
                    className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="Describe your event and requirements..."
                    value={contactForm.message}
                    onChange={(e) =>
                      setContactForm({
                        ...contactForm,
                        message: e.target.value,
                      })
                    }
                    required
                  />
                </div>
              </div>

              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline" type="button">
                    Cancel
                  </Button>
                </DialogClose>
                <Button type="submit">Send Inquiry</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </main>

      <Footer />
    </div>
  );
};

export default Venues;
