import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { X, Download, Smartphone, Wifi, WifiOff } from 'lucide-react';
import { usePWA } from '@/hooks/usePWA';
import { cn } from '@/lib/utils';

const PWAInstallPrompt: React.FC = () => {
  const { isInstallable, isInstalled, isOnline, promptInstall, dismissInstall } = usePWA();
  const [isDismissed, setIsDismissed] = useState(false);
  const [showOfflineNotice, setShowOfflineNotice] = useState(false);

  // Check if user has previously dismissed the prompt
  useEffect(() => {
    const dismissed = localStorage.getItem('pwa-prompt-dismissed');
    if (dismissed === 'true') {
      setIsDismissed(true);
    }
  }, []);

  // Show offline notice when going offline
  useEffect(() => {
    if (!isOnline) {
      setShowOfflineNotice(true);
      const timer = setTimeout(() => setShowOfflineNotice(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [isOnline]);

  const handleInstall = async () => {
    try {
      await promptInstall();
    } catch (error) {
      console.error('Failed to install PWA:', error);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem('pwa-prompt-dismissed', 'true');
    dismissInstall();
  };

  // Don't show if already installed, dismissed, or not installable
  if (isInstalled || isDismissed || !isInstallable) {
    return (
      <>
        {/* Offline Notice */}
        {showOfflineNotice && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
            <Card className="bg-orange-50 border-orange-200">
              <CardContent className="p-3">
                <div className="flex items-center gap-2 text-orange-800">
                  <WifiOff className="h-4 w-4" />
                  <span className="text-sm font-medium">You're offline</span>
                  <span className="text-xs">Some features may be limited</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Online Status Indicator for PWA users */}
        {isInstalled && (
          <div className="fixed bottom-4 right-4 z-50">
            <Badge 
              variant={isOnline ? "default" : "destructive"}
              className={cn(
                "flex items-center gap-1",
                isOnline ? "bg-green-100 text-green-800 border-green-200" : ""
              )}
            >
              {isOnline ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
              {isOnline ? "Online" : "Offline"}
            </Badge>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-80 z-50">
      <Card className="shadow-lg border-2 border-navy-blue/20 bg-white/95 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-navy-blue/10 rounded-lg">
                <Smartphone className="h-5 w-5 text-navy-blue" />
              </div>
              <div>
                <CardTitle className="text-lg">Install EventMap</CardTitle>
                <CardDescription className="text-sm">
                  Get the full app experience
                </CardDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className="p-1 h-auto text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="pt-0">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="text-xs">
                <Download className="h-3 w-3 mr-1" />
                Offline access
              </Badge>
              <Badge variant="secondary" className="text-xs">
                📱 Native feel
              </Badge>
              <Badge variant="secondary" className="text-xs">
                🔔 Push notifications
              </Badge>
            </div>
            
            <div className="flex gap-2">
              <Button 
                onClick={handleInstall}
                className="flex-1 bg-navy-blue hover:bg-navy-blue/90 text-white"
                size="sm"
              >
                <Download className="h-4 w-4 mr-2" />
                Install App
              </Button>
              <Button 
                variant="outline" 
                onClick={handleDismiss}
                size="sm"
              >
                Not now
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PWAInstallPrompt;