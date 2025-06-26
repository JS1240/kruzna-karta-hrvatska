import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { 
  Bell, 
  BellOff, 
  Settings, 
  Check, 
  CheckCheck, 
  Trash2, 
  Calendar, 
  MapPin, 
  TrendingDown, 
  AlertCircle,
  Mail,
  Smartphone,
  X
} from 'lucide-react';
import { useNotifications, Notification } from '@/hooks/useNotifications';
import { formatDistanceToNow } from 'date-fns';
import { toast } from '@/hooks/use-toast';

interface NotificationCenterProps {
  trigger?: React.ReactNode;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ trigger }) => {
  const {
    notifications,
    unreadCount,
    settings,
    permission,
    isSupported,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    updateSettings,
    requestPermission,
    testNotification,
  } = useNotifications();

  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('notifications');

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'event_reminder':
        return <Calendar className="h-4 w-4 text-blue-500" />;
      case 'new_event':
        return <MapPin className="h-4 w-4 text-green-500" />;
      case 'price_drop':
        return <TrendingDown className="h-4 w-4 text-orange-500" />;
      case 'event_update':
        return <AlertCircle className="h-4 w-4 text-purple-500" />;
      default:
        return <Bell className="h-4 w-4 text-gray-500" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'event_reminder':
        return 'border-l-blue-500';
      case 'new_event':
        return 'border-l-green-500';
      case 'price_drop':
        return 'border-l-orange-500';
      case 'event_update':
        return 'border-l-purple-500';
      default:
        return 'border-l-gray-500';
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    
    if (notification.actionUrl) {
      window.location.href = notification.actionUrl;
      setIsOpen(false);
    }
  };

  const handleRequestPermission = async () => {
    const result = await requestPermission();
    if (result === 'granted') {
      toast({
        title: "Notifications enabled",
        description: "You'll now receive push notifications for important updates",
      });
    } else {
      toast({
        title: "Notifications blocked",
        description: "You can enable notifications in your browser settings",
        variant: "destructive",
      });
    }
  };

  const recentNotifications = notifications.slice(0, 10);
  const unreadNotifications = notifications.filter(n => !n.read);

  const DefaultTrigger = () => (
    <Button
      variant="ghost"
      size="icon"
      className="relative"
    >
      <Bell className="h-5 w-5" />
      {unreadCount > 0 && (
        <Badge 
          variant="accent-gold" 
          className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center text-xs font-bold"
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </Badge>
      )}
    </Button>
  );

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        {trigger || <DefaultTrigger />}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0">
        <div className="p-0">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div className="border-b px-4 py-3">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">Notifications</h3>
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAllAsRead}
                    className="text-xs"
                  >
                    <CheckCheck className="h-3 w-3 mr-1" />
                    Mark all read
                  </Button>
                )}
              </div>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="notifications" className="text-xs">
                  All ({notifications.length})
                </TabsTrigger>
                <TabsTrigger value="settings" className="text-xs">
                  Settings
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="notifications" className="mt-0">
              <div className="max-h-96 overflow-y-auto">
                {recentNotifications.length === 0 ? (
                  <div className="p-6 text-center">
                    <Bell className="h-8 w-8 mx-auto text-gray-400 mb-3" />
                    <p className="text-sm text-gray-500">No notifications yet</p>
                    <p className="text-xs text-gray-400 mt-1">
                      We'll notify you about important events and updates
                    </p>
                  </div>
                ) : (
                  <div className="divide-y">
                    {recentNotifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`p-4 hover:bg-accent-cream/20 cursor-pointer border-l-2 ${getNotificationColor(notification.type)} ${
                          !notification.read ? 'bg-accent-cream/10' : ''
                        }`}
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className="flex items-start gap-3">
                          {getNotificationIcon(notification.type)}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className={`text-sm font-medium ${
                                  !notification.read ? 'text-gray-900' : 'text-gray-700'
                                }`}>
                                  {notification.title}
                                </p>
                                <p className="text-xs text-gray-600 mt-1">
                                  {notification.message}
                                </p>
                                <p className="text-xs text-gray-400 mt-2">
                                  {formatDistanceToNow(new Date(notification.createdAt), { addSuffix: true })}
                                </p>
                              </div>
                              <div className="flex items-center gap-1 ml-2">
                                {!notification.read && (
                                  <div className="w-2 h-2 bg-accent-gold rounded-full"></div>
                                )}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="p-1 h-auto opacity-0 group-hover:opacity-100"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    deleteNotification(notification.id);
                                  }}
                                >
                                  <X className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {notifications.length > 10 && (
                <div className="p-3 border-t">
                  <Button variant="ghost" className="w-full text-xs">
                    View all notifications
                  </Button>
                </div>
              )}
            </TabsContent>

            <TabsContent value="settings" className="mt-0">
              <div className="p-4 space-y-6">
                {/* Permission Status */}
                {isSupported && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">Browser Notifications</h4>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Smartphone className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">Push notifications</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {permission === 'granted' ? (
                          <Badge variant="success" className="text-xs">Enabled</Badge>
                        ) : permission === 'denied' ? (
                          <Badge variant="destructive" className="text-xs">Blocked</Badge>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRequestPermission}
                            className="text-xs bg-accent-cream hover:bg-accent-gold"
                          >
                            Enable
                          </Button>
                        )}
                      </div>
                    </div>
                    {permission === 'granted' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={testNotification}
                        className="w-full text-xs"
                      >
                        Test notification
                      </Button>
                    )}
                  </div>
                )}

                <Separator />

                {/* Notification Preferences */}
                <div className="space-y-4">
                  <h4 className="font-medium text-sm">Notification Preferences</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="event-reminders" className="text-sm">Event reminders</Label>
                        <p className="text-xs text-gray-500">Get notified 1 hour before events</p>
                      </div>
                      <Switch
                        id="event-reminders"
                        checked={settings.eventReminders}
                        onCheckedChange={(checked) => updateSettings({ eventReminders: checked })}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="new-events" className="text-sm">New events</Label>
                        <p className="text-xs text-gray-500">Events matching your interests</p>
                      </div>
                      <Switch
                        id="new-events"
                        checked={settings.newEvents}
                        onCheckedChange={(checked) => updateSettings({ newEvents: checked })}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="price-drops" className="text-sm">Price drops</Label>
                        <p className="text-xs text-gray-500">When ticket prices decrease</p>
                      </div>
                      <Switch
                        id="price-drops"
                        checked={settings.priceDrops}
                        onCheckedChange={(checked) => updateSettings({ priceDrops: checked })}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="event-updates" className="text-sm">Event updates</Label>
                        <p className="text-xs text-gray-500">Changes to events you're attending</p>
                      </div>
                      <Switch
                        id="event-updates"
                        checked={settings.eventUpdates}
                        onCheckedChange={(checked) => updateSettings({ eventUpdates: checked })}
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Email Preferences */}
                <div className="space-y-4">
                  <h4 className="font-medium text-sm flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Email Notifications
                  </h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="email-notifications" className="text-sm">Email notifications</Label>
                        <p className="text-xs text-gray-500">Receive notifications via email</p>
                      </div>
                      <Switch
                        id="email-notifications"
                        checked={settings.email}
                        onCheckedChange={(checked) => updateSettings({ email: checked })}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="newsletter" className="text-sm">Newsletter</Label>
                        <p className="text-xs text-gray-500">Weekly event recommendations</p>
                      </div>
                      <Switch
                        id="newsletter"
                        checked={settings.newsletter}
                        onCheckedChange={(checked) => updateSettings({ newsletter: checked })}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default NotificationCenter;