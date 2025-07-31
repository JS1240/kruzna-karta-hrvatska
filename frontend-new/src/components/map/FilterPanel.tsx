import React, { useState } from 'react';
import { Filter, X, Search, Calendar, MapPin, Tag, Star } from 'lucide-react';
import { FilterState } from '@/types/event';
import { useCategories } from '@/hooks/useEvents';
import clsx from 'clsx';

interface FilterPanelProps {
  filters: FilterState;
  onFilterChange: (key: keyof FilterState, value: unknown) => void;
  onClearFilters: () => void;
  className?: string;
  isOpen?: boolean;
  onToggle?: () => void;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
  className,
  isOpen = true,
  onToggle,
}) => {
  const { data: categories = [], isLoading: categoriesLoading } = useCategories();
  const [searchTerm, setSearchTerm] = useState(filters.search || '');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange('search', searchTerm.trim() || undefined);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const hasActiveFilters = Object.keys(filters).length > 0;
  const activeFilterCount = Object.keys(filters).length;

  const cities = [
    'Zagreb', 'Split', 'Rijeka', 'Osijek', 'Zadar', 'Slavonski Brod',
    'Pula', 'Sesvete', 'Karlovac', 'Varaždin', 'Šibenik', 'Sisak',
    'Velika Gorica', 'Vukovar', 'Dubrovnik', 'Bjelovar', 'Koprivnica',
    'Požega', 'Čakovec', 'Vinkovci'
  ];

  return (
    <div className={clsx('bg-white rounded-xl shadow-sm border border-gray-200', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="text-sm text-gray-500 hover:text-red-600 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Clear all
            </button>
          )}
          <button
            onClick={onToggle}
            className="text-gray-500 hover:text-gray-700 md:hidden"
          >
            {isOpen ? <X className="w-5 h-5" /> : <Filter className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Filter Content - Horizontal Layout */}
      <div className={clsx('p-4', !isOpen && 'hidden md:block')}>
        {/* Top Row - Search and Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {/* Search */}
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Search className="w-4 h-4 inline mr-1" />
              Search Events
            </label>
            <form onSubmit={handleSearchSubmit}>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={handleSearchChange}
                  placeholder="Search by title, description..."
                  className="input flex-1"
                />
                <button
                  type="submit"
                  className="btn btn-primary px-4"
                >
                  Search
                </button>
              </div>
            </form>
          </div>

          {/* Featured Events Toggle */}
          <div className="flex items-end">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={filters.featured || false}
                onChange={(e) => onFilterChange('featured', e.target.checked || undefined)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div className="flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-500" />
                <span className="text-sm font-medium text-gray-700">
                  Featured Only
                </span>
              </div>
            </label>
          </div>
        </div>

        {/* Bottom Row - Other Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Tag className="w-4 h-4 inline mr-1" />
              Category
            </label>
            <select
              value={filters.category || ''}
              onChange={(e) => onFilterChange('category', e.target.value ? Number(e.target.value) : undefined)}
              className="input w-full"
              disabled={categoriesLoading}
            >
              <option value="">All Categories</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          {/* Location Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <MapPin className="w-4 h-4 inline mr-1" />
              Location
            </label>
            <select
              value={filters.location || ''}
              onChange={(e) => onFilterChange('location', e.target.value || undefined)}
              className="input w-full"
            >
              <option value="">All Cities</option>
              {cities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </div>

          {/* Date From */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-1" />
              Date From
            </label>
            <input
              type="date"
              value={filters.dateFrom || ''}
              onChange={(e) => onFilterChange('dateFrom', e.target.value || undefined)}
              className="input w-full"
            />
          </div>

          {/* Date To */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date To
            </label>
            <input
              type="date"
              value={filters.dateTo || ''}
              onChange={(e) => onFilterChange('dateTo', e.target.value || undefined)}
              className="input w-full"
            />
          </div>

          {/* Price Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Price Range (EUR)
            </label>
            <div className="flex gap-1">
              <input
                type="number"
                min="0"
                step="5"
                value={filters.priceMin || ''}
                onChange={(e) => onFilterChange('priceMin', e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Min"
                className="input w-full text-sm"
              />
              <input
                type="number"
                min="0"
                step="5"
                value={filters.priceMax || ''}
                onChange={(e) => onFilterChange('priceMax', e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Max"
                className="input w-full text-sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;