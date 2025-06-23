import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Heart, 
  MessageSquare, 
  Share2, 
  Calendar, 
  MapPin, 
  Users, 
  Camera,
  Send,
  MoreHorizontal,
  Flag,
  Bookmark,
  TrendingUp,
  Clock,
  ThumbsUp,
  Loader2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getCurrentUser } from '@/lib/auth';
import { toast } from '@/hooks/use-toast';
import { communityApi, CommunityPost as APICommunityPost } from '@/lib/api';

// Using CommunityPost interface from api.ts as APICommunityPost
// Keeping local interface for compatibility
interface CommunityPost {
  id: string;
  type: 'event_review' | 'event_photo' | 'event_recommendation' | 'general_discussion';
  userId: string;
  userName: string;
  userAvatar?: string;
  content: string;
  images?: string[];
  eventId?: string;
  eventTitle?: string;
  eventDate?: string;
  location?: string;
  likes: number;
  comments: number;
  shares: number;
  isLiked: boolean;
  isBookmarked: boolean;
  createdAt: string;
  tags?: string[];
}

interface Comment {
  id: string;
  postId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  content: string;
  likes: number;
  isLiked: boolean;
  createdAt: string;
  replies?: Comment[];
}

const mockPosts: CommunityPost[] = [
  {
    id: '1',
    type: 'event_review',
    userId: 'user1',
    userName: 'Ana Marić',
    userAvatar: '/avatars/ana.jpg',
    content: 'Just attended the Zagreb Jazz Festival and it was absolutely incredible! The atmosphere was electric, and the lineup exceeded all expectations. Highly recommend for all jazz lovers! 🎷✨',
    images: ['/community/jazz-festival-1.jpg', '/community/jazz-festival-2.jpg'],
    eventId: '1',
    eventTitle: 'Zagreb Jazz Festival',
    eventDate: '2025-07-15',
    location: 'Zagreb',
    likes: 24,
    comments: 8,
    shares: 3,
    isLiked: false,
    isBookmarked: false,
    createdAt: '2025-07-16T10:30:00Z',
    tags: ['jazz', 'music', 'festival', 'zagreb'],
  },
  {
    id: '2',
    type: 'event_recommendation',
    userId: 'user2',
    userName: 'Marko Kovač',
    userAvatar: '/avatars/marko.jpg',
    content: 'For all tech enthusiasts in Rijeka - don\'t miss the upcoming Tech Conference next month! Great speakers lined up and amazing networking opportunities. Early bird tickets are still available!',
    eventId: '4',
    eventTitle: 'Rijeka Tech Conference',
    eventDate: '2025-08-05',
    location: 'Rijeka',
    likes: 18,
    comments: 12,
    shares: 7,
    isLiked: true,
    isBookmarked: true,
    createdAt: '2025-07-14T14:20:00Z',
    tags: ['tech', 'conference', 'networking', 'rijeka'],
  },
  {
    id: '3',
    type: 'general_discussion',
    userId: 'user3',
    userName: 'Petra Novak',
    userAvatar: '/avatars/petra.jpg',
    content: 'What are everyone\'s plans for the summer festival season? I\'m torn between so many great options across Croatia. Would love to hear your recommendations!',
    likes: 15,
    comments: 23,
    shares: 2,
    isLiked: false,
    isBookmarked: false,
    createdAt: '2025-07-13T09:15:00Z',
    tags: ['summer', 'festivals', 'recommendations'],
  },
];

const mockComments: Comment[] = [
  {
    id: 'c1',
    postId: '1',
    userId: 'user4',
    userName: 'Ivo Petrić',
    content: 'Totally agree! The saxophonist was phenomenal. Already looking forward to next year!',
    likes: 5,
    isLiked: false,
    createdAt: '2025-07-16T11:00:00Z',
  },
  {
    id: 'c2',
    postId: '1',
    userId: 'user5',
    userName: 'Maja Tomić',
    content: 'Thanks for sharing! I was on the fence about going, but your review convinced me to get tickets for the next show.',
    likes: 3,
    isLiked: true,
    createdAt: '2025-07-16T12:30:00Z',
  },
];

const CommunityFeed: React.FC = () => {
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [comments, setComments] = useState<Comment[]>(mockComments);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newPost, setNewPost] = useState('');
  const [selectedTab, setSelectedTab] = useState('all');
  const [selectedPost, setSelectedPost] = useState<CommunityPost | null>(null);
  const [newComment, setNewComment] = useState('');
  const [isCreatePostOpen, setIsCreatePostOpen] = useState(false);
  
  const user = getCurrentUser();

  const fetchPosts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try to fetch real community posts first
      let apiPosts: APICommunityPost[] = [];
      
      try {
        apiPosts = await communityApi.getCommunityPosts({ limit: 20 });
      } catch {
        // Fallback: Generate posts from recent events
        console.log('Using event-based community posts fallback');
        apiPosts = await communityApi.generateMockPosts(10);
      }
      
      // Transform API posts to local format
      const transformedPosts: CommunityPost[] = apiPosts.map(post => ({
        id: post.id,
        type: post.type,
        userId: post.userId,
        userName: post.userName,
        userAvatar: post.userAvatar,
        content: post.content,
        images: post.images,
        eventId: post.eventId?.toString(),
        eventTitle: post.event?.title || post.event?.name,
        eventDate: post.event?.date,
        location: post.event?.location,
        likes: post.likes,
        comments: post.comments,
        shares: post.shares,
        isLiked: post.isLiked,
        isBookmarked: post.isBookmarked,
        createdAt: post.createdAt,
        tags: post.tags,
      }));
      
      setPosts(transformedPosts);
    } catch (err) {
      console.error('Failed to fetch community posts:', err);
      setError('Failed to load community posts');
      
      // Ultimate fallback: static mock posts
      setPosts(mockPosts);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const handleLikePost = async (postId: string) => {
    const post = posts.find(p => p.id === postId);
    if (!post) return;

    // Optimistic update
    setPosts(prev => prev.map(p => {
      if (p.id === postId) {
        return {
          ...p,
          isLiked: !p.isLiked,
          likes: p.isLiked ? p.likes - 1 : p.likes + 1,
        };
      }
      return p;
    }));

    try {
      await communityApi.togglePostLike(postId);
    } catch (error) {
      console.error('Failed to toggle post like:', error);
      
      // Revert optimistic update on error
      setPosts(prev => prev.map(p => {
        if (p.id === postId) {
          return {
            ...p,
            isLiked: post.isLiked,
            likes: post.likes,
          };
        }
        return p;
      }));
      
      toast({
        title: "Failed to update like",
        description: "Could not update post like. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleBookmarkPost = async (postId: string) => {
    const post = posts.find(p => p.id === postId);
    if (!post) return;

    // Optimistic update
    setPosts(prev => prev.map(p => {
      if (p.id === postId) {
        return {
          ...p,
          isBookmarked: !p.isBookmarked,
        };
      }
      return p;
    }));

    try {
      await communityApi.togglePostBookmark(postId);
      
      toast({
        title: !post.isBookmarked ? "Added to bookmarks" : "Removed from bookmarks",
        description: !post.isBookmarked ? "Post saved to your bookmarks" : "Post removed from your bookmarks",
      });
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
      
      // Revert optimistic update on error
      setPosts(prev => prev.map(p => {
        if (p.id === postId) {
          return {
            ...p,
            isBookmarked: post.isBookmarked,
          };
        }
        return p;
      }));
      
      toast({
        title: "Failed to update bookmark",
        description: "Could not update bookmark. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleSharePost = (postId: string) => {
    const post = posts.find(p => p.id === postId);
    if (post) {
      if (navigator.share) {
        navigator.share({
          title: `${post.userName}'s post on EventMap`,
          text: post.content,
          url: window.location.href,
        });
      } else {
        navigator.clipboard.writeText(window.location.href);
        toast({
          title: "Link copied",
          description: "Post link has been copied to clipboard",
        });
      }
      
      setPosts(prev => prev.map(p => 
        p.id === postId ? { ...p, shares: p.shares + 1 } : p
      ));
    }
  };

  const handleCreatePost = async () => {
    if (!user || !newPost.trim()) return;

    try {
      const createdPost = await communityApi.createPost({
        type: 'general_discussion',
        content: newPost,
      });
      
      // Transform to local format and add to posts
      const transformedPost: CommunityPost = {
        id: createdPost.id,
        type: createdPost.type,
        userId: createdPost.userId,
        userName: createdPost.userName,
        userAvatar: createdPost.userAvatar,
        content: createdPost.content,
        images: createdPost.images,
        eventId: createdPost.eventId?.toString(),
        eventTitle: createdPost.event?.title || createdPost.event?.name,
        eventDate: createdPost.event?.date,
        location: createdPost.event?.location,
        likes: createdPost.likes,
        comments: createdPost.comments,
        shares: createdPost.shares,
        isLiked: createdPost.isLiked,
        isBookmarked: createdPost.isBookmarked,
        createdAt: createdPost.createdAt,
        tags: createdPost.tags,
      };
      
      setPosts(prev => [transformedPost, ...prev]);
      setNewPost('');
      setIsCreatePostOpen(false);
      
      toast({
        title: "Post created",
        description: "Your post has been shared with the community",
      });
    } catch (error) {
      console.error('Failed to create post:', error);
      
      toast({
        title: "Failed to create post",
        description: "Could not create your post. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleAddComment = async (postId: string) => {
    if (!user || !newComment.trim()) return;

    try {
      await communityApi.addComment(postId, newComment);
      
      // Add comment locally (in real app, you'd fetch the created comment)
      const comment: Comment = {
        id: Date.now().toString(),
        postId,
        userId: user.id,
        userName: user.name || user.email,
        userAvatar: user.avatar,
        content: newComment,
        likes: 0,
        isLiked: false,
        createdAt: new Date().toISOString(),
      };

      setComments(prev => [...prev, comment]);
      setPosts(prev => prev.map(post => 
        post.id === postId ? { ...post, comments: post.comments + 1 } : post
      ));
      
      setNewComment('');
      toast({
        title: "Comment added",
        description: "Your comment has been posted",
      });
    } catch (error) {
      console.error('Failed to add comment:', error);
      
      toast({
        title: "Failed to add comment",
        description: "Could not post your comment. Please try again.",
        variant: "destructive",
      });
    }
  };

  const getPostTypeIcon = (type: string) => {
    switch (type) {
      case 'event_review':
        return <ThumbsUp className="h-4 w-4 text-green-500" />;
      case 'event_photo':
        return <Camera className="h-4 w-4 text-blue-500" />;
      case 'event_recommendation':
        return <TrendingUp className="h-4 w-4 text-orange-500" />;
      default:
        return <MessageSquare className="h-4 w-4 text-gray-500" />;
    }
  };

  const getFilteredPosts = () => {
    switch (selectedTab) {
      case 'reviews':
        return posts.filter(post => post.type === 'event_review');
      case 'recommendations':
        return posts.filter(post => post.type === 'event_recommendation');
      case 'photos':
        return posts.filter(post => post.type === 'event_photo');
      default:
        return posts;
    }
  };

  const getPostComments = (postId: string) => {
    return comments.filter(comment => comment.postId === postId);
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Join the Community
          </h3>
          <p className="text-gray-600 mb-4">
            Log in to connect with other event-goers, share experiences, and discover new events.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-navy-blue">Community</h2>
          <p className="text-gray-600">Connect with fellow event enthusiasts</p>
        </div>
        <div className="flex items-center gap-2">
          {error && (
            <Button variant="outline" size="sm" onClick={fetchPosts} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Retry
            </Button>
          )}
          <Dialog open={isCreatePostOpen} onOpenChange={setIsCreatePostOpen}>
            <DialogTrigger asChild>
              <Button>
                <Send className="h-4 w-4 mr-2" />
                Create Post
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Share with the Community</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <Textarea
                  placeholder="What's on your mind? Share your thoughts about events, ask for recommendations, or start a discussion..."
                  value={newPost}
                  onChange={(e) => setNewPost(e.target.value)}
                  rows={4}
                />
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsCreatePostOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreatePost} disabled={!newPost.trim()}>
                    Post
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">All Posts</TabsTrigger>
          <TabsTrigger value="reviews">Reviews</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="photos">Photos</TabsTrigger>
        </TabsList>

        <TabsContent value={selectedTab} className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span>Loading community posts...</span>
              </div>
            </div>
          ) : error ? (
            <div className="text-center py-16">
              <AlertCircle className="w-16 h-16 mx-auto text-red-400 mb-4" />
              <h3 className="text-2xl font-bold text-navy-blue mb-2">
                Failed to load posts
              </h3>
              <p className="text-lg text-gray-600 mb-6">
                {error}
              </p>
              <Button onClick={fetchPosts}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              {getFilteredPosts().map((post) => (
              <Card key={post.id} className="overflow-hidden">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar>
                        <AvatarImage src={post.userAvatar} />
                        <AvatarFallback>
                          {post.userName.split(' ').map(n => n[0]).join('').toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{post.userName}</span>
                          {getPostTypeIcon(post.type)}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Clock className="h-3 w-3" />
                          {formatDistanceToNow(new Date(post.createdAt), { addSuffix: true })}
                          {post.location && (
                            <>
                              <span>•</span>
                              <MapPin className="h-3 w-3" />
                              {post.location}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Event Info */}
                  {post.eventId && post.eventTitle && (
                    <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                      <Calendar className="h-4 w-4 text-blue-500" />
                      <span className="text-sm font-medium text-blue-900">
                        {post.eventTitle}
                      </span>
                      {post.eventDate && (
                        <span className="text-xs text-blue-600">
                          {new Date(post.eventDate).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Content */}
                  <p className="text-gray-800">{post.content}</p>

                  {/* Images */}
                  {post.images && post.images.length > 0 && (
                    <div className="grid grid-cols-2 gap-2">
                      {post.images.map((image, index) => (
                        <img
                          key={index}
                          src={image}
                          alt={`Post image ${index + 1}`}
                          className="w-full h-48 object-cover rounded-lg cursor-pointer hover:opacity-90"
                        />
                      ))}
                    </div>
                  )}

                  {/* Tags */}
                  {post.tags && post.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {post.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          #{tag}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex items-center gap-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleLikePost(post.id)}
                        className={`gap-2 ${post.isLiked ? 'text-red-500' : 'text-gray-500'}`}
                      >
                        <Heart className={`h-4 w-4 ${post.isLiked ? 'fill-current' : ''}`} />
                        {post.likes}
                      </Button>
                      
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="sm" className="gap-2 text-gray-500">
                            <MessageSquare className="h-4 w-4" />
                            {post.comments}
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                          <DialogHeader>
                            <DialogTitle>Comments</DialogTitle>
                          </DialogHeader>
                          <div className="space-y-4">
                            {/* Original Post */}
                            <div className="p-4 bg-gray-50 rounded-lg">
                              <div className="flex items-center gap-2 mb-2">
                                <Avatar className="h-8 w-8">
                                  <AvatarImage src={post.userAvatar} />
                                  <AvatarFallback className="text-xs">
                                    {post.userName.split(' ').map(n => n[0]).join('').toUpperCase()}
                                  </AvatarFallback>
                                </Avatar>
                                <span className="font-medium text-sm">{post.userName}</span>
                              </div>
                              <p className="text-sm">{post.content}</p>
                            </div>

                            {/* Comments */}
                            <div className="space-y-3">
                              {getPostComments(post.id).map((comment) => (
                                <div key={comment.id} className="flex gap-3">
                                  <Avatar className="h-8 w-8">
                                    <AvatarImage src={comment.userAvatar} />
                                    <AvatarFallback className="text-xs">
                                      {comment.userName.split(' ').map(n => n[0]).join('').toUpperCase()}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div className="flex-1">
                                    <div className="bg-gray-100 rounded-lg p-3">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="font-medium text-sm">{comment.userName}</span>
                                        <span className="text-xs text-gray-500">
                                          {formatDistanceToNow(new Date(comment.createdAt), { addSuffix: true })}
                                        </span>
                                      </div>
                                      <p className="text-sm">{comment.content}</p>
                                    </div>
                                    <div className="flex items-center gap-2 mt-1">
                                      <Button variant="ghost" size="sm" className="text-xs text-gray-500 h-auto p-1">
                                        <Heart className="h-3 w-3 mr-1" />
                                        {comment.likes}
                                      </Button>
                                      <Button variant="ghost" size="sm" className="text-xs text-gray-500 h-auto p-1">
                                        Reply
                                      </Button>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>

                            {/* Add Comment */}
                            <div className="flex gap-3 pt-4 border-t">
                              <Avatar className="h-8 w-8">
                                <AvatarImage src={user.avatar} />
                                <AvatarFallback className="text-xs">
                                  {user.name?.charAt(0)?.toUpperCase() || user.email.charAt(0).toUpperCase()}
                                </AvatarFallback>
                              </Avatar>
                              <div className="flex-1 flex gap-2">
                                <Input
                                  placeholder="Write a comment..."
                                  value={newComment}
                                  onChange={(e) => setNewComment(e.target.value)}
                                  onKeyPress={(e) => {
                                    if (e.key === 'Enter' && newComment.trim()) {
                                      handleAddComment(post.id);
                                    }
                                  }}
                                />
                                <Button
                                  size="sm"
                                  onClick={() => handleAddComment(post.id)}
                                  disabled={!newComment.trim()}
                                >
                                  <Send className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleSharePost(post.id)}
                        className="gap-2 text-gray-500"
                      >
                        <Share2 className="h-4 w-4" />
                        {post.shares}
                      </Button>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleBookmarkPost(post.id)}
                        className={`${post.isBookmarked ? 'text-blue-500' : 'text-gray-500'}`}
                      >
                        <Bookmark className={`h-4 w-4 ${post.isBookmarked ? 'fill-current' : ''}`} />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-gray-500">
                        <Flag className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

              {getFilteredPosts().length === 0 && (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      No posts yet
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Be the first to share something with the community!
                    </p>
                    <Button onClick={() => setIsCreatePostOpen(true)}>
                      Create First Post
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CommunityFeed;