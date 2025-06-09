import React from "react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Venue {
  id: number;
  name: string;
  city: string;
  county: string;
  address: string;
  category: string;
  capacity: number;
  priceRange: number;
  amenities: string[];
  imageUrl: string;
  rating: number;
  description: string;
}

interface Props {
  venue: Venue;
  onSelect: (v: Venue) => void;
  onContact: (v: Venue) => void;
}

const VenueCard: React.FC<Props> = ({ venue, onSelect, onContact }) => (
  <Card key={venue.id} className="overflow-hidden h-full flex flex-col">
    <div className="relative h-48">
      <img src={venue.imageUrl} alt={venue.name} className="w-full h-full object-cover" />
    </div>
    <CardHeader className="pb-2">
      <CardTitle className="text-lg">{venue.name}</CardTitle>
    </CardHeader>
    <CardContent className="flex-1 space-y-2">
      <p className="text-sm text-gray-600">
        {venue.city}, {venue.county}
      </p>
      <p className="text-sm text-gray-600">Capacity: {venue.capacity}</p>
      <div className="flex flex-wrap gap-1">
        {venue.amenities.slice(0, 3).map((a, i) => (
          <Badge key={i} variant="outline" className="text-xs">
            {a}
          </Badge>
        ))}
        {venue.amenities.length > 3 && (
          <Badge variant="outline" className="text-xs">
            +{venue.amenities.length - 3} more
          </Badge>
        )}
      </div>
    </CardContent>
    <CardFooter className="pt-2">
      <div className="w-full flex gap-2">
        <Button variant="outline" className="flex-1" onClick={() => onSelect(venue)}>
          Details
        </Button>
        <Button className="flex-1" onClick={() => onContact(venue)}>
          Contact
        </Button>
      </div>
    </CardFooter>
  </Card>
);

export default VenueCard;
