import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { toast } from '@/hooks/use-toast';
import { User, getCurrentUser, updateUserProfile } from '@/lib/auth';
import { User as UserIcon, Bell, Globe, Palette, Heart, Settings } from 'lucide-react';

const UserProfile: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    preferences: {
      favoriteCategories: [] as string[],
      notificationSettings: {
        email: true,
        push: true,
        eventReminders: true,
        newsletter: false,
      },
      language: 'en' as 'en' | 'hr',
      theme: 'system' as 'light' | 'dark' | 'system',
    },
  });

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
      setFormData({
        name: currentUser.name || '',
        email: currentUser.email,
        preferences: currentUser.preferences || {
          favoriteCategories: [],
          notificationSettings: {
            email: true,
            push: true,
            eventReminders: true,
            newsletter: false,
          },
          language: 'en',
          theme: 'system',
        },
      });
    }
  }, []);

  const handleSave = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const updatedUser = await updateUserProfile({
        name: formData.name,
        preferences: formData.preferences,
      });
      
      setUser(updatedUser);
      toast({
        title: "Profile updated",
        description: "Your profile has been successfully updated.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryToggle = (category: string) => {
    const categories = formData.preferences.favoriteCategories;
    const newCategories = categories.includes(category)
      ? categories.filter(c => c !== category)
      : [...categories, category];
    
    setFormData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        favoriteCategories: newCategories,
      },
    }));
  };

  const eventCategories = [
    { id: 'concert', label: 'Concerts', color: 'bg-pink-500' },
    { id: 'festival', label: 'Festivals', color: 'bg-purple-500' },
    { id: 'party', label: 'Parties', color: 'bg-orange-500' },
    { id: 'conference', label: 'Conferences', color: 'bg-blue-500' },
    { id: 'workout', label: 'Workouts', color: 'bg-green-500' },
    { id: 'meetup', label: 'Meetups', color: 'bg-teal-500' },
    { id: 'theater', label: 'Theater', color: 'bg-red-500' },
    { id: 'exhibition', label: 'Exhibitions', color: 'bg-indigo-500' },
  ];

  if (!user) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-gray-500">Please log in to view your profile.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Avatar className="h-20 w-20">
          <AvatarImage src={user.avatar} />
          <AvatarFallback className="bg-navy-blue text-white text-xl">
            {user.name?.charAt(0)?.toUpperCase() || user.email.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div>
          <h1 className="text-2xl font-bold text-navy-blue">{user.name || user.email}</h1>
          <p className="text-gray-600">{user.email}</p>
          {user.emailVerified && (
            <Badge variant="secondary" className="mt-1">
              ✓ Verified
            </Badge>
          )}
        </div>
      </div>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <UserIcon className="h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <Heart className="h-4 w-4" />
            Preferences
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter your name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    value={formData.email}
                    disabled
                    className="bg-gray-50"
                  />
                </div>
              </div>
              <p className="text-sm text-gray-500">
                Member since: {user.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'N/A'}
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Favorite Event Categories</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {eventCategories.map((category) => (
                  <div
                    key={category.id}
                    className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                      formData.preferences.favoriteCategories.includes(category.id)
                        ? 'border-navy-blue bg-navy-blue/10'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleCategoryToggle(category.id)}
                  >
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${category.color}`} />
                      <span className="text-sm font-medium">{category.label}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-gray-500">Receive notifications via email</p>
                </div>
                <Switch
                  checked={formData.preferences.notificationSettings.email}
                  onCheckedChange={(checked) =>
                    setFormData(prev => ({
                      ...prev,
                      preferences: {
                        ...prev.preferences,
                        notificationSettings: {
                          ...prev.preferences.notificationSettings,
                          email: checked,
                        },
                      },
                    }))
                  }
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <Label>Push Notifications</Label>
                  <p className="text-sm text-gray-500">Receive browser push notifications</p>
                </div>
                <Switch
                  checked={formData.preferences.notificationSettings.push}
                  onCheckedChange={(checked) =>
                    setFormData(prev => ({
                      ...prev,
                      preferences: {
                        ...prev.preferences,
                        notificationSettings: {
                          ...prev.preferences.notificationSettings,
                          push: checked,
                        },
                      },
                    }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Event Reminders</Label>
                  <p className="text-sm text-gray-500">Get reminded about upcoming events you're interested in</p>
                </div>
                <Switch
                  checked={formData.preferences.notificationSettings.eventReminders}
                  onCheckedChange={(checked) =>
                    setFormData(prev => ({
                      ...prev,
                      preferences: {
                        ...prev.preferences,
                        notificationSettings: {
                          ...prev.preferences.notificationSettings,
                          eventReminders: checked,
                        },
                      },
                    }))
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Newsletter</Label>
                  <p className="text-sm text-gray-500">Receive our weekly event newsletter</p>
                </div>
                <Switch
                  checked={formData.preferences.notificationSettings.newsletter}
                  onCheckedChange={(checked) =>
                    setFormData(prev => ({
                      ...prev,
                      preferences: {
                        ...prev.preferences,
                        notificationSettings: {
                          ...prev.preferences.notificationSettings,
                          newsletter: checked,
                        },
                      },
                    }))
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>App Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Language</Label>
                <Select
                  value={formData.preferences.language}
                  onValueChange={(value: 'en' | 'hr') =>
                    setFormData(prev => ({
                      ...prev,
                      preferences: {
                        ...prev.preferences,
                        language: value,
                      },
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">🇺🇸 English</SelectItem>
                    <SelectItem value="hr">🇭🇷 Croatian</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Theme</Label>
                <Select
                  value={formData.preferences.theme}
                  onValueChange={(value: 'light' | 'dark' | 'system') =>
                    setFormData(prev => ({
                      ...prev,
                      preferences: {
                        ...prev.preferences,
                        theme: value,
                      },
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">☀️ Light</SelectItem>
                    <SelectItem value="dark">🌙 Dark</SelectItem>
                    <SelectItem value="system">⚙️ System</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={loading} className="bg-navy-blue hover:bg-navy-blue/90">
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </div>
  );
};

export default UserProfile;