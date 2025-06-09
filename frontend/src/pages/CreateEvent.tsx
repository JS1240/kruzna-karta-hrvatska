import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Plus, Save, Clock, MapPin, Calendar, Tag, DollarSign, X } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import PageTransition from '../components/PageTransition';
import { logger } from '../lib/logger';
import TicketTypeFields, { TicketType as TicketTypeData } from '../components/TicketTypeFields';


interface Category {
  id: number;
  name: string;
}

interface Venue {
  id: number;
  name: string;
  address: string;
}

const CreateEvent = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [currentTag, setCurrentTag] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    date: '',
    time: '',
    end_date: '',
    end_time: '',
    location: '',
    category_id: '',
    venue_id: '',
    image: '',
    link: '',
    age_restriction: '',
  });

  const [ticketTypes, setTicketTypes] = useState<TicketTypeData[]>([
    {
      name: 'General Admission',
      description: '',
      price: 0,
      currency: 'EUR',
      total_quantity: 100,
      min_purchase: 1,
      max_purchase: 10,
    }
  ]);

  useEffect(() => {
    fetchCategories();
    fetchVenues();
  }, []);

  const fetchCategories = async () => {
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
      const response = await fetch(`${apiBase}/categories`);
      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      logger.error('Error fetching categories:', error);
    }
  };

  const fetchVenues = async () => {
    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
      const response = await fetch(`${apiBase}/venues`);
      const data = await response.json();
      setVenues(data.venues || []);
    } catch (error) {
      logger.error('Error fetching venues:', error);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleTicketTypeChange = (index: number, field: keyof TicketTypeData, value: string | number) => {
    setTicketTypes(prev => prev.map((ticket, i) => 
      i === index ? { ...ticket, [field]: value } : ticket
    ));
  };

  const addTicketType = () => {
    setTicketTypes(prev => [...prev, {
      name: '',
      description: '',
      price: 0,
      currency: 'EUR',
      total_quantity: 100,
      min_purchase: 1,
      max_purchase: 10,
    }]);
  };

  const removeTicketType = (index: number) => {
    if (ticketTypes.length > 1) {
      setTicketTypes(prev => prev.filter((_, i) => i !== index));
    }
  };

  const addTag = () => {
    if (currentTag.trim() && !tags.includes(currentTag.trim())) {
      setTags(prev => [...prev, currentTag.trim()]);
      setCurrentTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(prev => prev.filter(tag => tag !== tagToRemove));
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) newErrors.title = 'Title is required';
    if (!formData.description.trim()) newErrors.description = 'Description is required';
    if (!formData.date) newErrors.date = 'Date is required';
    if (!formData.time) newErrors.time = 'Time is required';
    if (!formData.location.trim()) newErrors.location = 'Location is required';
    if (!formData.category_id) newErrors.category_id = 'Category is required';

    // Validate ticket types
    ticketTypes.forEach((ticket, index) => {
      if (!ticket.name.trim()) {
        newErrors[`ticket_${index}_name`] = 'Ticket name is required';
      }
      if (ticket.price < 0) {
        newErrors[`ticket_${index}_price`] = 'Price cannot be negative';
      }
      if (ticket.total_quantity < 1) {
        newErrors[`ticket_${index}_quantity`] = 'Quantity must be at least 1';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const eventData = {
        ...formData,
        category_id: parseInt(formData.category_id),
        venue_id: formData.venue_id ? parseInt(formData.venue_id) : null,
        tags: tags,
        ticket_types: ticketTypes,
      };

      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
      const response = await fetch(`${apiBase}/user-events/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(eventData),
      });

      const result = await response.json();

      if (response.ok) {
        navigate('/organizer/dashboard', { 
          state: { 
            message: 'Event created successfully! It will be reviewed by our team.',
            type: 'success' 
          }
        });
      } else {
        if (response.status === 403) {
          setErrors({ form: 'You need to be a venue owner or manager to create events. Please contact support to upgrade your account.' });
        } else {
          setErrors({ form: result.detail || 'Failed to create event. Please try again.' });
        }
      }
    } catch (error) {
      logger.error('Error creating event:', error);
      setErrors({ form: 'Network error. Please check your connection and try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream">
        <Header />
        
        <main className="flex-grow container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-navy-blue mb-2 font-sreda">
                Create New Event
              </h1>
              <p className="text-lg text-gray-600">
                Share your event with the world! Fill out the details below and we'll review it for publication.
              </p>
            </div>

            {errors.form && (
              <Alert className="mb-6 border-red-200 bg-red-50">
                <AlertDescription className="text-red-700">
                  {errors.form}
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Calendar className="h-5 w-5" />
                    <span>Basic Information</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="title">Event Title *</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      placeholder="Enter a compelling event title"
                      className={errors.title ? 'border-red-500' : ''}
                    />
                    {errors.title && (
                      <p className="text-sm text-red-500 mt-1">{errors.title}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="description">Description *</Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => handleInputChange('description', e.target.value)}
                      placeholder="Describe your event in detail. What can attendees expect?"
                      rows={4}
                      className={errors.description ? 'border-red-500' : ''}
                    />
                    {errors.description && (
                      <p className="text-sm text-red-500 mt-1">{errors.description}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="category">Category *</Label>
                      <Select 
                        value={formData.category_id} 
                        onValueChange={(value) => handleInputChange('category_id', value)}
                      >
                        <SelectTrigger className={errors.category_id ? 'border-red-500' : ''}>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map((category) => (
                            <SelectItem key={category.id} value={category.id.toString()}>
                              {category.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {errors.category_id && (
                        <p className="text-sm text-red-500 mt-1">{errors.category_id}</p>
                      )}
                    </div>

                    <div>
                      <Label htmlFor="venue">Venue (Optional)</Label>
                      <Select 
                        value={formData.venue_id} 
                        onValueChange={(value) => handleInputChange('venue_id', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select venue or leave empty" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">No specific venue</SelectItem>
                          {venues.map((venue) => (
                            <SelectItem key={venue.id} value={venue.id.toString()}>
                              {venue.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="image">Event Image URL (Optional)</Label>
                    <Input
                      id="image"
                      type="url"
                      value={formData.image}
                      onChange={(e) => handleInputChange('image', e.target.value)}
                      placeholder="https://example.com/event-image.jpg"
                    />
                  </div>

                  <div>
                    <Label htmlFor="link">External Link (Optional)</Label>
                    <Input
                      id="link"
                      type="url"
                      value={formData.link}
                      onChange={(e) => handleInputChange('link', e.target.value)}
                      placeholder="https://example.com/more-info"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Date & Time */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Clock className="h-5 w-5" />
                    <span>Date & Time</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="date">Start Date *</Label>
                      <Input
                        id="date"
                        type="date"
                        value={formData.date}
                        onChange={(e) => handleInputChange('date', e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                        className={errors.date ? 'border-red-500' : ''}
                      />
                      {errors.date && (
                        <p className="text-sm text-red-500 mt-1">{errors.date}</p>
                      )}
                    </div>

                    <div>
                      <Label htmlFor="time">Start Time *</Label>
                      <Input
                        id="time"
                        type="time"
                        value={formData.time}
                        onChange={(e) => handleInputChange('time', e.target.value)}
                        className={errors.time ? 'border-red-500' : ''}
                      />
                      {errors.time && (
                        <p className="text-sm text-red-500 mt-1">{errors.time}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="end_date">End Date (Optional)</Label>
                      <Input
                        id="end_date"
                        type="date"
                        value={formData.end_date}
                        onChange={(e) => handleInputChange('end_date', e.target.value)}
                        min={formData.date || new Date().toISOString().split('T')[0]}
                      />
                    </div>

                    <div>
                      <Label htmlFor="end_time">End Time (Optional)</Label>
                      <Input
                        id="end_time"
                        type="time"
                        value={formData.end_time}
                        onChange={(e) => handleInputChange('end_time', e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Location */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <MapPin className="h-5 w-5" />
                    <span>Location</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="location">Event Location *</Label>
                    <Input
                      id="location"
                      value={formData.location}
                      onChange={(e) => handleInputChange('location', e.target.value)}
                      placeholder="Enter the full address or location details"
                      className={errors.location ? 'border-red-500' : ''}
                    />
                    {errors.location && (
                      <p className="text-sm text-red-500 mt-1">{errors.location}</p>
                    )}
                  </div>

                  <div>
                    <Label htmlFor="age_restriction">Age Restriction (Optional)</Label>
                    <Select 
                      value={formData.age_restriction} 
                      onValueChange={(value) => handleInputChange('age_restriction', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select age restriction" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">No restriction</SelectItem>
                        <SelectItem value="18+">18+ only</SelectItem>
                        <SelectItem value="21+">21+ only</SelectItem>
                        <SelectItem value="All ages">All ages welcome</SelectItem>
                        <SelectItem value="Family friendly">Family friendly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              {/* Tags */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Tag className="h-5 w-5" />
                    <span>Tags</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex space-x-2">
                    <Input
                      value={currentTag}
                      onChange={(e) => setCurrentTag(e.target.value)}
                      placeholder="Add tags to help people find your event"
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    />
                    <Button type="button" onClick={addTag} variant="outline">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="flex items-center space-x-1">
                          <span>{tag}</span>
                          <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="ml-1 hover:text-red-500"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Ticket Types */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <DollarSign className="h-5 w-5" />
                    <span>Ticket Types</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {ticketTypes.map((ticket, index) => (
                    <TicketTypeFields
                      key={index}
                      ticket={ticket}
                      index={index}
                      errors={errors}
                      onChange={handleTicketTypeChange}
                      onRemove={() => removeTicketType(index)}
                      removable={ticketTypes.length > 1}
                    />
                  ))}

                  <Button
                    type="button"
                    variant="outline"
                    onClick={addTicketType}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Another Ticket Type
                  </Button>
                </CardContent>
              </Card>

              {/* Submit */}
              <div className="flex justify-end space-x-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/organizer/dashboard')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={loading}
                  className="min-w-[120px]"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Create Event
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </main>

        <Footer />
      </div>
    </PageTransition>
  );
};

export default CreateEvent;