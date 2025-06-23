import { useState, useEffect, useCallback } from 'react';
import { getCurrentUser } from '@/lib/auth';

export interface Notification {
  id: string;
  type: 'event_reminder' | 'new_event' | 'price_drop' | 'event_update' | 'system';
  title: string;
  message: string;
  data?: any;
  read: boolean;
  createdAt: string;
  scheduledFor?: string;
  actionUrl?: string;
}

interface NotificationSettings {
  email: boolean;
  push: boolean;
  eventReminders: boolean;
  newEvents: boolean;
  priceDrops: boolean;
  eventUpdates: boolean;
  newsletter: boolean;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  settings: NotificationSettings;
  permission: NotificationPermission;
  isSupported: boolean;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  deleteNotification: (id: string) => void;
  updateSettings: (newSettings: Partial<NotificationSettings>) => void;
  requestPermission: () => Promise<NotificationPermission>;
  scheduleReminder: (eventId: string, eventTitle: string, eventDate: string) => void;
  testNotification: () => void;
}

export const useNotifications = (): UseNotificationsReturn => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [settings, setSettings] = useState<NotificationSettings>({
    email: true,
    push: true,
    eventReminders: true,
    newEvents: false,
    priceDrops: true,
    eventUpdates: true,
    newsletter: false,
  });
  const [permission, setPermission] = useState<NotificationPermission>('default');

  const isSupported = 'Notification' in window && 'serviceWorker' in navigator;
  const user = getCurrentUser();

  // Load settings and notifications from localStorage
  useEffect(() => {
    if (!user) return;

    // Load settings
    const savedSettings = localStorage.getItem(`notification_settings_${user.id}`);
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (error) {
        console.error('Failed to parse notification settings:', error);
      }
    } else {
      // Use user preferences if available
      if (user.preferences?.notificationSettings) {
        setSettings(prev => ({
          ...prev,
          ...user.preferences.notificationSettings,
        }));
      }
    }

    // Load notifications
    const savedNotifications = localStorage.getItem(`notifications_${user.id}`);
    if (savedNotifications) {
      try {
        setNotifications(JSON.parse(savedNotifications));
      } catch (error) {
        console.error('Failed to parse notifications:', error);
      }
    } else {
      // Generate some mock notifications for demo
      generateMockNotifications();
    }

    // Get current permission
    if (isSupported) {
      setPermission(Notification.permission);
    }
  }, [user, isSupported]);

  const generateMockNotifications = () => {
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'event_reminder',
        title: 'Event Reminder',
        message: 'Nina Badrić Concert starts in 1 hour!',
        read: false,
        createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
        actionUrl: '/events/1',
        data: { eventId: '1' },
      },
      {
        id: '2',
        type: 'new_event',
        title: 'New Event in Your Area',
        message: 'A new concert has been added in Zagreb that matches your interests.',
        read: false,
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
        actionUrl: '/events/2',
        data: { eventId: '2', location: 'Zagreb' },
      },
      {
        id: '3',
        type: 'price_drop',
        title: 'Price Drop Alert',
        message: 'Tickets for Adriatic Business Conference are now 20% off!',
        read: true,
        createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
        actionUrl: '/events/4',
        data: { eventId: '4', oldPrice: 100, newPrice: 80 },
      },
      {
        id: '4',
        type: 'system',
        title: 'Welcome to EventMap Croatia!',
        message: 'Discover amazing events happening around you. Enable notifications to never miss out!',
        read: true,
        createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
      },
    ];
    setNotifications(mockNotifications);
  };

  // Save notifications to localStorage
  const saveNotifications = useCallback((newNotifications: Notification[]) => {
    if (!user) return;
    localStorage.setItem(`notifications_${user.id}`, JSON.stringify(newNotifications));
  }, [user]);

  // Save settings to localStorage
  const saveSettings = useCallback((newSettings: NotificationSettings) => {
    if (!user) return;
    localStorage.setItem(`notification_settings_${user.id}`, JSON.stringify(newSettings));
  }, [user]);

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev => {
      const updated = prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      );
      saveNotifications(updated);
      return updated;
    });
  }, [saveNotifications]);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => {
      const updated = prev.map(notification => ({ ...notification, read: true }));
      saveNotifications(updated);
      return updated;
    });
  }, [saveNotifications]);

  const deleteNotification = useCallback((id: string) => {
    setNotifications(prev => {
      const updated = prev.filter(notification => notification.id !== id);
      saveNotifications(updated);
      return updated;
    });
  }, [saveNotifications]);

  const updateSettings = useCallback((newSettings: Partial<NotificationSettings>) => {
    setSettings(prev => {
      const updated = { ...prev, ...newSettings };
      saveSettings(updated);
      return updated;
    });
  }, [saveSettings]);

  const requestPermission = useCallback(async (): Promise<NotificationPermission> => {
    if (!isSupported) {
      return 'denied';
    }

    try {
      const permission = await Notification.requestPermission();
      setPermission(permission);
      return permission;
    } catch (error) {
      console.error('Failed to request notification permission:', error);
      return 'denied';
    }
  }, [isSupported]);

  const showBrowserNotification = useCallback((title: string, options: NotificationOptions) => {
    if (!isSupported || permission !== 'granted') {
      return;
    }

    try {
      const notification = new Notification(title, {
        ...options,
        icon: '/icon-192x192.png',
        badge: '/icon-192x192.png',
        tag: 'eventmap-notification',
        requireInteraction: false,
        silent: false,
      });

      notification.onclick = () => {
        window.focus();
        if (options.data?.actionUrl) {
          window.location.href = options.data.actionUrl;
        }
        notification.close();
      };

      // Auto close after 5 seconds
      setTimeout(() => notification.close(), 5000);
    } catch (error) {
      console.error('Failed to show notification:', error);
    }
  }, [isSupported, permission]);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'createdAt'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
    };

    setNotifications(prev => {
      const updated = [newNotification, ...prev].slice(0, 50); // Keep only last 50
      saveNotifications(updated);
      return updated;
    });

    // Show browser notification if enabled
    if (settings.push && permission === 'granted') {
      showBrowserNotification(notification.title, {
        body: notification.message,
        data: {
          actionUrl: notification.actionUrl,
          ...notification.data,
        },
      });
    }
  }, [settings.push, permission, showBrowserNotification, saveNotifications]);

  const scheduleReminder = useCallback((eventId: string, eventTitle: string, eventDate: string) => {
    if (!settings.eventReminders) return;

    const eventDateTime = new Date(eventDate);
    const reminderTime = new Date(eventDateTime.getTime() - 60 * 60 * 1000); // 1 hour before
    const now = new Date();

    if (reminderTime <= now) {
      // Event is too soon, don't schedule
      return;
    }

    // Store reminder info for later processing
    const reminders = JSON.parse(localStorage.getItem('scheduled_reminders') || '[]');
    const reminder = {
      id: `reminder_${eventId}_${Date.now()}`,
      eventId,
      eventTitle,
      eventDate: eventDate,
      reminderTime: reminderTime.toISOString(),
      userId: user?.id,
    };

    reminders.push(reminder);
    localStorage.setItem('scheduled_reminders', JSON.stringify(reminders));

    // In a real app, you would schedule this with a service worker or push notification service
    console.log(`Reminder scheduled for ${eventTitle} at ${reminderTime}`);
  }, [settings.eventReminders, user]);

  const testNotification = useCallback(() => {
    if (permission !== 'granted') {
      requestPermission().then((perm) => {
        if (perm === 'granted') {
          showBrowserNotification('Test Notification', {
            body: 'This is a test notification from EventMap Croatia!',
            icon: '/icon-192x192.png',
          });
        }
      });
    } else {
      showBrowserNotification('Test Notification', {
        body: 'This is a test notification from EventMap Croatia!',
        icon: '/icon-192x192.png',
      });
    }
  }, [permission, requestPermission, showBrowserNotification]);

  // Check for scheduled reminders periodically
  useEffect(() => {
    const checkReminders = () => {
      const reminders = JSON.parse(localStorage.getItem('scheduled_reminders') || '[]');
      const now = new Date();
      const triggeredReminders: any[] = [];
      const remainingReminders: any[] = [];

      reminders.forEach((reminder: any) => {
        if (new Date(reminder.reminderTime) <= now && reminder.userId === user?.id) {
          triggeredReminders.push(reminder);
        } else {
          remainingReminders.push(reminder);
        }
      });

      // Trigger notifications for due reminders
      triggeredReminders.forEach((reminder) => {
        addNotification({
          type: 'event_reminder',
          title: 'Event Reminder',
          message: `${reminder.eventTitle} starts in 1 hour!`,
          read: false,
          actionUrl: `/events/${reminder.eventId}`,
          data: { eventId: reminder.eventId },
        });
      });

      // Update stored reminders
      if (triggeredReminders.length > 0) {
        localStorage.setItem('scheduled_reminders', JSON.stringify(remainingReminders));
      }
    };

    // Check every minute
    const interval = setInterval(checkReminders, 60 * 1000);
    return () => clearInterval(interval);
  }, [user, addNotification]);

  const unreadCount = notifications.filter(n => !n.read).length;

  return {
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
    scheduleReminder,
    testNotification,
  };
};