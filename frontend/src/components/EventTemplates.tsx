import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Music, 
  Users, 
  Calendar, 
  MapPin, 
  Briefcase, 
  Dumbbell, 
  Theater, 
  Palette,
  Search,
  Clock,
  Euro,
  FileText,
  Star,
  Copy,
  Check
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface EventTemplate {
  id: string;
  name: string;
  category: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  popularity: number;
  fields: {
    title: string;
    description: string;
    duration: string;
    suggestedPrice: string;
    capacity: string;
    requirements: string[];
    tags: string[];
  };
  customFields: Array<{
    name: string;
    type: 'text' | 'number' | 'select' | 'textarea';
    label: string;
    options?: string[];
    required?: boolean;
  }>;
}

const eventTemplates: EventTemplate[] = [
  {
    id: 'concert',
    name: 'Music Concert',
    category: 'Music & Entertainment',
    icon: Music,
    description: 'Perfect for live music performances, from intimate acoustic sets to large-scale concerts',
    popularity: 95,
    fields: {
      title: 'Live Music Concert',
      description: 'Join us for an unforgettable evening of live music featuring talented artists. Experience great sound, atmosphere, and memorable performances.',
      duration: '3 hours',
      suggestedPrice: '150-300 HRK',
      capacity: '100-5000',
      requirements: ['Sound system', 'Stage setup', 'Lighting', 'Security'],
      tags: ['music', 'live', 'entertainment', 'concert'],
    },
    customFields: [
      { name: 'genre', type: 'select', label: 'Music Genre', options: ['Rock', 'Pop', 'Jazz', 'Classical', 'Electronic', 'Folk'], required: true },
      { name: 'bands', type: 'textarea', label: 'Performing Artists', required: true },
      { name: 'ageRestriction', type: 'select', label: 'Age Restriction', options: ['All ages', '16+', '18+', '21+'] },
    ],
  },
  {
    id: 'conference',
    name: 'Business Conference',
    category: 'Business & Professional',
    icon: Briefcase,
    description: 'Ideal for professional gatherings, seminars, and business networking events',
    popularity: 88,
    fields: {
      title: 'Professional Conference',
      description: 'Connect with industry leaders, gain valuable insights, and expand your professional network at our comprehensive conference.',
      duration: '8 hours',
      suggestedPrice: '200-500 HRK',
      capacity: '50-1000',
      requirements: ['AV equipment', 'WiFi', 'Catering', 'Registration desk'],
      tags: ['business', 'professional', 'networking', 'conference'],
    },
    customFields: [
      { name: 'industry', type: 'select', label: 'Industry Focus', options: ['Technology', 'Healthcare', 'Finance', 'Marketing', 'Education', 'Other'], required: true },
      { name: 'speakers', type: 'textarea', label: 'Keynote Speakers', required: true },
      { name: 'agenda', type: 'textarea', label: 'Event Agenda' },
      { name: 'certificationCredits', type: 'number', label: 'CE Credits Available' },
    ],
  },
  {
    id: 'workshop',
    name: 'Workshop/Training',
    category: 'Education & Learning',
    icon: Users,
    description: 'Great for hands-on learning experiences, skill-building workshops, and educational sessions',
    popularity: 82,
    fields: {
      title: 'Interactive Workshop',
      description: 'Learn new skills and gain practical experience in our hands-on workshop. Small groups ensure personalized attention and maximum learning.',
      duration: '4 hours',
      suggestedPrice: '100-250 HRK',
      capacity: '10-50',
      requirements: ['Workshop materials', 'Tables/chairs', 'WiFi', 'Flipchart'],
      tags: ['workshop', 'learning', 'skills', 'training'],
    },
    customFields: [
      { name: 'skillLevel', type: 'select', label: 'Skill Level', options: ['Beginner', 'Intermediate', 'Advanced', 'All levels'], required: true },
      { name: 'materials', type: 'textarea', label: 'Materials Provided' },
      { name: 'prerequisites', type: 'textarea', label: 'Prerequisites' },
      { name: 'certificate', type: 'select', label: 'Certificate Provided', options: ['Yes', 'No'] },
    ],
  },
  {
    id: 'party',
    name: 'Party/Celebration',
    category: 'Social & Entertainment',
    icon: Calendar,
    description: 'Perfect for celebrations, social gatherings, and entertainment events',
    popularity: 79,
    fields: {
      title: 'Celebration Party',
      description: 'Join us for an amazing celebration! Great music, fantastic atmosphere, and unforgettable memories await.',
      duration: '5 hours',
      suggestedPrice: '50-150 HRK',
      capacity: '50-500',
      requirements: ['DJ/Music system', 'Bar setup', 'Decorations', 'Security'],
      tags: ['party', 'celebration', 'social', 'entertainment'],
    },
    customFields: [
      { name: 'theme', type: 'text', label: 'Party Theme' },
      { name: 'dressCode', type: 'select', label: 'Dress Code', options: ['Casual', 'Smart casual', 'Formal', 'Costume/Theme'] },
      { name: 'ageGroup', type: 'select', label: 'Target Age Group', options: ['18-25', '25-35', '35-45', '45+', 'All ages'] },
    ],
  },
  {
    id: 'fitness',
    name: 'Fitness/Sports',
    category: 'Health & Fitness',
    icon: Dumbbell,
    description: 'Ideal for fitness classes, sports events, and wellness activities',
    popularity: 76,
    fields: {
      title: 'Fitness Session',
      description: 'Get active and stay healthy with our energizing fitness session. All fitness levels welcome. Bring water and comfortable workout clothes.',
      duration: '1.5 hours',
      suggestedPrice: '30-80 HRK',
      capacity: '10-30',
      requirements: ['Exercise space', 'Sound system', 'Equipment storage', 'Changing rooms'],
      tags: ['fitness', 'health', 'workout', 'sports'],
    },
    customFields: [
      { name: 'activityType', type: 'select', label: 'Activity Type', options: ['Yoga', 'Pilates', 'Zumba', 'CrossFit', 'Running', 'Cycling', 'Other'], required: true },
      { name: 'fitnessLevel', type: 'select', label: 'Fitness Level', options: ['Beginner', 'Intermediate', 'Advanced', 'All levels'], required: true },
      { name: 'equipment', type: 'textarea', label: 'Equipment Provided' },
    ],
  },
  {
    id: 'art-exhibition',
    name: 'Art Exhibition',
    category: 'Arts & Culture',
    icon: Palette,
    description: 'Perfect for art shows, gallery openings, and cultural exhibitions',
    popularity: 71,
    fields: {
      title: 'Art Exhibition',
      description: 'Discover incredible artworks from talented artists. Immerse yourself in creativity and artistic expression at our curated exhibition.',
      duration: '4 hours',
      suggestedPrice: 'Free-100 HRK',
      capacity: '20-200',
      requirements: ['Gallery space', 'Lighting', 'Security', 'Guest book'],
      tags: ['art', 'exhibition', 'culture', 'gallery'],
    },
    customFields: [
      { name: 'artType', type: 'select', label: 'Art Type', options: ['Painting', 'Sculpture', 'Photography', 'Mixed Media', 'Digital Art', 'Other'], required: true },
      { name: 'artists', type: 'textarea', label: 'Featured Artists', required: true },
      { name: 'artworkCount', type: 'number', label: 'Number of Artworks' },
    ],
  },
  {
    id: 'theater',
    name: 'Theater Performance',
    category: 'Arts & Culture',
    icon: Theater,
    description: 'Great for theatrical performances, plays, and dramatic presentations',
    popularity: 68,
    fields: {
      title: 'Theater Performance',
      description: 'Experience the magic of live theater with our captivating performance. Professional actors bring stories to life on stage.',
      duration: '2.5 hours',
      suggestedPrice: '100-250 HRK',
      capacity: '50-300',
      requirements: ['Stage', 'Lighting system', 'Sound system', 'Dressing rooms'],
      tags: ['theater', 'performance', 'drama', 'entertainment'],
    },
    customFields: [
      { name: 'playTitle', type: 'text', label: 'Play Title', required: true },
      { name: 'genre', type: 'select', label: 'Genre', options: ['Drama', 'Comedy', 'Musical', 'Tragedy', 'Romance', 'Other'], required: true },
      { name: 'cast', type: 'textarea', label: 'Main Cast' },
      { name: 'language', type: 'select', label: 'Language', options: ['Croatian', 'English', 'Other'] },
    ],
  },
];

interface EventTemplatesProps {
  onTemplateSelect?: (template: EventTemplate, customData: Record<string, any>) => void;
}

const EventTemplates: React.FC<EventTemplatesProps> = ({ onTemplateSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTemplate, setSelectedTemplate] = useState<EventTemplate | null>(null);
  const [customData, setCustomData] = useState<Record<string, any>>({});
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const categories = ['all', ...new Set(eventTemplates.map(t => t.category))];

  const filteredTemplates = eventTemplates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleTemplateClick = (template: EventTemplate) => {
    setSelectedTemplate(template);
    setCustomData({});
    setIsDialogOpen(true);
  };

  const handleCustomFieldChange = (fieldName: string, value: any) => {
    setCustomData(prev => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  const handleUseTemplate = () => {
    if (selectedTemplate) {
      // Validate required fields
      const missingFields = selectedTemplate.customFields
        .filter(field => field.required && !customData[field.name])
        .map(field => field.label);

      if (missingFields.length > 0) {
        toast({
          title: "Missing required fields",
          description: `Please fill in: ${missingFields.join(', ')}`,
          variant: "destructive",
        });
        return;
      }

      onTemplateSelect?.(selectedTemplate, customData);
      setIsDialogOpen(false);
      toast({
        title: "Template applied",
        description: `${selectedTemplate.name} template has been applied to your event.`,
      });
    }
  };

  const copyTemplateData = () => {
    if (selectedTemplate) {
      const templateData = {
        ...selectedTemplate.fields,
        ...customData,
      };
      navigator.clipboard.writeText(JSON.stringify(templateData, null, 2));
      toast({
        title: "Template copied",
        description: "Template data has been copied to clipboard.",
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-navy-blue mb-2">Event Templates</h2>
        <p className="text-gray-600">
          Choose from professionally designed templates to create your event quickly and efficiently
        </p>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category === 'all' ? 'All Categories' : category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => {
          const IconComponent = template.icon;
          return (
            <Card 
              key={template.id} 
              className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:-translate-y-1"
              onClick={() => handleTemplateClick(template)}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-navy-blue/10 rounded-lg">
                      <IconComponent className="h-6 w-6 text-navy-blue" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <Badge variant="secondary" className="text-xs">
                        {template.category}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    <span className="text-sm font-medium">{template.popularity}%</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 text-sm mb-4">{template.description}</p>
                
                <div className="space-y-2 text-xs text-gray-500">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3" />
                    <span>Duration: {template.fields.duration}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Euro className="h-3 w-3" />
                    <span>Price: {template.fields.suggestedPrice}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-3 w-3" />
                    <span>Capacity: {template.fields.capacity}</span>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="flex flex-wrap gap-1">
                    {template.fields.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {template.fields.tags.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{template.fields.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
          <p className="text-gray-600">
            Try adjusting your search or filter criteria to find relevant templates.
          </p>
        </div>
      )}

      {/* Template Customization Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {selectedTemplate && (
                <>
                  <selectedTemplate.icon className="h-6 w-6 text-navy-blue" />
                  Customize {selectedTemplate.name} Template
                </>
              )}
            </DialogTitle>
          </DialogHeader>

          {selectedTemplate && (
            <div className="space-y-6">
              {/* Template Preview */}
              <Card className="bg-gray-50">
                <CardContent className="pt-6">
                  <h4 className="font-medium mb-2">Template Preview</h4>
                  <div className="space-y-2 text-sm">
                    <p><strong>Title:</strong> {selectedTemplate.fields.title}</p>
                    <p><strong>Description:</strong> {selectedTemplate.fields.description}</p>
                    <p><strong>Duration:</strong> {selectedTemplate.fields.duration}</p>
                    <p><strong>Suggested Price:</strong> {selectedTemplate.fields.suggestedPrice}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Custom Fields */}
              {selectedTemplate.customFields.length > 0 && (
                <div>
                  <h4 className="font-medium mb-4">Customize Your Event</h4>
                  <div className="space-y-4">
                    {selectedTemplate.customFields.map((field) => (
                      <div key={field.name}>
                        <Label htmlFor={field.name}>
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </Label>
                        
                        {field.type === 'text' && (
                          <Input
                            id={field.name}
                            value={customData[field.name] || ''}
                            onChange={(e) => handleCustomFieldChange(field.name, e.target.value)}
                            placeholder={field.label}
                          />
                        )}
                        
                        {field.type === 'number' && (
                          <Input
                            id={field.name}
                            type="number"
                            value={customData[field.name] || ''}
                            onChange={(e) => handleCustomFieldChange(field.name, e.target.value)}
                            placeholder={field.label}
                          />
                        )}
                        
                        {field.type === 'textarea' && (
                          <Textarea
                            id={field.name}
                            value={customData[field.name] || ''}
                            onChange={(e) => handleCustomFieldChange(field.name, e.target.value)}
                            placeholder={field.label}
                            rows={3}
                          />
                        )}
                        
                        {field.type === 'select' && field.options && (
                          <Select
                            value={customData[field.name] || ''}
                            onValueChange={(value) => handleCustomFieldChange(field.name, value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
                            </SelectTrigger>
                            <SelectContent>
                              {field.options.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Requirements */}
              <div>
                <h4 className="font-medium mb-2">Event Requirements</h4>
                <div className="grid grid-cols-2 gap-2">
                  {selectedTemplate.fields.requirements.map((req) => (
                    <div key={req} className="flex items-center gap-2 text-sm text-gray-600">
                      <Check className="h-3 w-3 text-green-500" />
                      {req}
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t">
                <Button onClick={handleUseTemplate} className="flex-1">
                  Use This Template
                </Button>
                <Button variant="outline" onClick={copyTemplateData}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EventTemplates;