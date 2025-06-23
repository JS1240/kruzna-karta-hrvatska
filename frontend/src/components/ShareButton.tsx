import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { toast } from '@/hooks/use-toast';
import { Share2, Link, Facebook, Twitter, MessageSquare, Mail, Copy } from 'lucide-react';

interface ShareButtonProps {
  title: string;
  description?: string;
  url?: string;
  className?: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

const ShareButton: React.FC<ShareButtonProps> = ({
  title,
  description = '',
  url = window.location.href,
  className = '',
  variant = 'outline',
  size = 'sm',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const shareData = {
    title,
    text: description,
    url,
  };

  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share(shareData);
        toast({
          title: "Shared successfully",
          description: "Event has been shared",
        });
      } catch (error) {
        if ((error as Error).name !== 'AbortError') {
          console.error('Error sharing:', error);
          toast({
            title: "Share failed",
            description: "Unable to share the event",
            variant: "destructive",
          });
        }
      }
    } else {
      // Fallback to dropdown menu
      setIsOpen(true);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(url);
      toast({
        title: "Link copied",
        description: "Event link has been copied to clipboard",
      });
    } catch (error) {
      console.error('Failed to copy:', error);
      toast({
        title: "Copy failed",
        description: "Unable to copy link to clipboard",
        variant: "destructive",
      });
    }
    setIsOpen(false);
  };

  const shareToFacebook = () => {
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    window.open(facebookUrl, '_blank', 'width=600,height=400');
    setIsOpen(false);
  };

  const shareToTwitter = () => {
    const twitterUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;
    window.open(twitterUrl, '_blank', 'width=600,height=400');
    setIsOpen(false);
  };

  const shareToWhatsApp = () => {
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(`${title} - ${url}`)}`;
    window.open(whatsappUrl, '_blank');
    setIsOpen(false);
  };

  const shareToEmail = () => {
    const emailUrl = `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(`${description}\n\n${url}`)}`;
    window.location.href = emailUrl;
    setIsOpen(false);
  };

  // If native sharing is available, use it directly
  if (navigator.share) {
    return (
      <Button
        variant={variant}
        size={size}
        className={className}
        onClick={handleNativeShare}
      >
        <Share2 className="h-4 w-4 mr-2" />
        Share
      </Button>
    );
  }

  // Fallback to dropdown menu for browsers without native sharing
  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          className={className}
        >
          <Share2 className="h-4 w-4 mr-2" />
          Share
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem onClick={copyToClipboard}>
          <Copy className="h-4 w-4 mr-2" />
          Copy Link
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={shareToFacebook}>
          <Facebook className="h-4 w-4 mr-2 text-blue-600" />
          Facebook
        </DropdownMenuItem>
        <DropdownMenuItem onClick={shareToTwitter}>
          <Twitter className="h-4 w-4 mr-2 text-blue-400" />
          Twitter
        </DropdownMenuItem>
        <DropdownMenuItem onClick={shareToWhatsApp}>
          <MessageSquare className="h-4 w-4 mr-2 text-green-600" />
          WhatsApp
        </DropdownMenuItem>
        <DropdownMenuItem onClick={shareToEmail}>
          <Mail className="h-4 w-4 mr-2 text-gray-600" />
          Email
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ShareButton;