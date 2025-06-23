import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Search, Clock, TrendingUp, MapPin, Calendar, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchSuggestion {
  id: string;
  text: string;
  type: 'event' | 'location' | 'category' | 'venue';
  meta?: string;
  count?: number;
}

interface RecentSearch {
  id: string;
  text: string;
  timestamp: number;
}

interface EnhancedSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSuggestionSelect?: (suggestion: SearchSuggestion) => void;
  placeholder?: string;
  className?: string;
}

const EnhancedSearch: React.FC<EnhancedSearchProps> = ({
  value,
  onChange,
  onSuggestionSelect,
  placeholder = "Search events, venues, or locations...",
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);
  const [trendingSearches] = useState<SearchSuggestion[]>([
    { id: '1', text: 'Zagreb concerts', type: 'category', count: 45 },
    { id: '2', text: 'Split festivals', type: 'category', count: 32 },
    { id: '3', text: 'Dubrovnik events', type: 'location', count: 28 },
    { id: '4', text: 'Tech meetups', type: 'category', count: 23 },
    { id: '5', text: 'Rijeka parties', type: 'category', count: 19 },
  ]);
  const [loading, setLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setRecentSearches(parsed.slice(0, 5)); // Keep only last 5
      } catch (error) {
        console.error('Failed to parse recent searches:', error);
      }
    }
  }, []);

  // Save recent searches to localStorage
  const saveRecentSearch = useCallback((text: string) => {
    if (!text.trim()) return;
    
    const newSearch: RecentSearch = {
      id: Date.now().toString(),
      text: text.trim(),
      timestamp: Date.now(),
    };

    setRecentSearches(prev => {
      const filtered = prev.filter(s => s.text.toLowerCase() !== text.toLowerCase());
      const updated = [newSearch, ...filtered].slice(0, 5);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Mock search suggestions - replace with actual API call
  const fetchSuggestions = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Mock suggestions based on query
    const mockSuggestions: SearchSuggestion[] = [
      { id: '1', text: `${query} concerts`, type: 'event', meta: 'Zagreb' },
      { id: '2', text: `${query} festivals`, type: 'event', meta: 'Split' },
      { id: '3', text: `Events in ${query}`, type: 'location', meta: 'Croatia' },
      { id: '4', text: `${query} Arena`, type: 'venue', meta: 'Venue' },
      { id: '5', text: `${query} meetups`, type: 'category', meta: 'Technology' },
    ].filter(s => s.text.toLowerCase().includes(query.toLowerCase()));

    setSuggestions(mockSuggestions);
    setLoading(false);
  }, []);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchSuggestions(value);
    }, 300);

    return () => clearTimeout(timer);
  }, [value, fetchSuggestions]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    onChange(suggestion.text);
    saveRecentSearch(suggestion.text);
    setIsOpen(false);
    onSuggestionSelect?.(suggestion);
  };

  const handleRecentSearchClick = (search: RecentSearch) => {
    onChange(search.text);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveRecentSearch(value);
      setIsOpen(false);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('recentSearches');
  };

  const removeRecentSearch = (id: string) => {
    setRecentSearches(prev => {
      const updated = prev.filter(s => s.id !== id);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
      return updated;
    });
  };

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'location': return <MapPin className="h-4 w-4 text-blue-500" />;
      case 'venue': return <MapPin className="h-4 w-4 text-green-500" />;
      case 'category': return <Calendar className="h-4 w-4 text-purple-500" />;
      default: return <Search className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div ref={searchRef} className={cn("relative w-full", className)}>
      <div className="relative">
        <Input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          className="w-full pl-10 pr-4 py-3 text-base"
        />
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        {loading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-navy-blue"></div>
          </div>
        )}
      </div>

      {isOpen && (
        <Card className="absolute top-full left-0 right-0 mt-1 z-50 shadow-lg border">
          <CardContent className="p-0 max-h-96 overflow-y-auto">
            {/* Search Suggestions */}
            {suggestions.length > 0 && (
              <div className="p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Suggestions</h3>
                <div className="space-y-2">
                  {suggestions.map((suggestion) => (
                    <div
                      key={suggestion.id}
                      className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {getSuggestionIcon(suggestion.type)}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {suggestion.text}
                        </div>
                        {suggestion.meta && (
                          <div className="text-xs text-gray-500">{suggestion.meta}</div>
                        )}
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {suggestion.type}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Searches */}
            {recentSearches.length > 0 && suggestions.length === 0 && (
              <>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-gray-900">Recent Searches</h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearRecentSearches}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Clear all
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {recentSearches.map((search) => (
                      <div
                        key={search.id}
                        className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-50 cursor-pointer group"
                        onClick={() => handleRecentSearchClick(search)}
                      >
                        <Clock className="h-4 w-4 text-gray-400" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-gray-900 truncate">{search.text}</div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-0 group-hover:opacity-100 p-1 h-auto"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeRecentSearch(search.id);
                          }}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
                <Separator />
              </>
            )}

            {/* Trending Searches */}
            {suggestions.length === 0 && (
              <div className="p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Trending Searches
                </h3>
                <div className="space-y-2">
                  {trendingSearches.map((trending) => (
                    <div
                      key={trending.id}
                      className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleSuggestionClick(trending)}
                    >
                      <TrendingUp className="h-4 w-4 text-orange-500" />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-gray-900 truncate">{trending.text}</div>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {trending.count}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No results */}
            {value && suggestions.length === 0 && !loading && (
              <div className="p-4 text-center text-gray-500">
                <Search className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <div className="text-sm">No suggestions found for "{value}"</div>
                <div className="text-xs text-gray-400 mt-1">
                  Try searching for events, venues, or locations
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EnhancedSearch;