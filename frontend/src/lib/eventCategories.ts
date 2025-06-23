import {
  Music,
  Mic,
  Crown,
  Briefcase,
  Theater,
  PartyPopper,
  Users,
  Trophy,
  Palette,
  Calendar,
  MoreHorizontal,
} from "lucide-react";

export interface CategoryConfig {
  icon: React.ComponentType<any>;
  color: string;
  label: string;
  description?: string;
}

export const categoryConfig: Record<string, CategoryConfig> = {
  concert: { 
    icon: Mic, 
    color: "#e11d48", 
    label: "Concerts",
    description: "Live music performances and concerts"
  },
  music: { 
    icon: Music, 
    color: "#db2777", 
    label: "Music",
    description: "General music events and performances"
  },
  festival: { 
    icon: Crown, 
    color: "#c026d3", 
    label: "Festivals",
    description: "Large-scale festivals and celebrations"
  },
  conference: { 
    icon: Briefcase, 
    color: "#dc2626", 
    label: "Conferences",
    description: "Business conferences and professional events"
  },
  theater: { 
    icon: Theater, 
    color: "#0891b2", 
    label: "Theater",
    description: "Theater performances and dramatic arts"
  },
  culture: { 
    icon: Palette, 
    color: "#7c3aed", 
    label: "Culture",
    description: "Cultural events and artistic exhibitions"
  },
  party: { 
    icon: PartyPopper, 
    color: "#ea580c", 
    label: "Parties",
    description: "Party events and nightlife"
  },
  meetup: { 
    icon: Users, 
    color: "#8b5cf6", 
    label: "Meetups",
    description: "Social gatherings and networking events"
  },
  workout: { 
    icon: Trophy, 
    color: "#059669", 
    label: "Sports & Fitness",
    description: "Sports events and fitness activities"
  },
  sports: { 
    icon: Trophy, 
    color: "#10b981", 
    label: "Sports",
    description: "Sporting events and competitions"
  },
  other: { 
    icon: MoreHorizontal, 
    color: "#6b7280", 
    label: "Other",
    description: "Miscellaneous events and activities"
  },
};

// Export category keys for type safety
export type EventCategory = keyof typeof categoryConfig;

// Helper function to get category config with fallback
export const getCategoryConfig = (category: string): CategoryConfig => {
  return categoryConfig[category] || categoryConfig.other;
};

// Get all available categories
export const getAllCategories = (): EventCategory[] => {
  return Object.keys(categoryConfig) as EventCategory[];
};

// Color palette for easy reference
export const categoryColors = {
  primary: "#e11d48",
  secondary: "#db2777", 
  accent: "#c026d3",
  business: "#dc2626",
  culture: "#0891b2",
  arts: "#7c3aed",
  social: "#ea580c",
  community: "#8b5cf6",
  sports: "#059669",
  fitness: "#10b981",
  neutral: "#6b7280",
} as const;