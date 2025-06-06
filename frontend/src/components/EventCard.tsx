import React from "react";
import { useNavigate } from "react-router-dom";

interface EventCardProps {
  id: string;
  title: string;
  image: string;
  date: string;
  location: string;
}

const EventCard: React.FC<EventCardProps> = ({
  id,
  title,
  image,
  date,
  location,
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/events/${id}`);
  };

  return (
    <div
      className="flex-shrink-0 w-64 mx-4 bg-cream rounded-lg shadow p-4 flex flex-col items-center justify-center cursor-pointer transition-transform duration-200 hover:scale-105 hover:shadow-xl"
      onClick={handleClick}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${title}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") handleClick();
      }}
    >
      <img
        src={image}
        alt={title}
        className="w-full h-32 object-cover rounded mb-2"
      />
      <div className="font-bold text-lg text-navy-blue mb-1 text-center truncate w-full">
        {title}
      </div>
      <div className="text-sm text-gray-600 mb-1">{date}</div>
      <div className="text-xs text-blue_green-700">{location}</div>
    </div>
  );
};

export default EventCard;
