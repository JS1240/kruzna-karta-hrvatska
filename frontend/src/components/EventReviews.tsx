import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Star, ThumbsUp, ThumbsDown, Flag, Filter, SortDesc } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/hooks/use-toast';
import { getCurrentUser } from '@/lib/auth';

interface Review {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  rating: number;
  title: string;
  comment: string;
  date: string;
  verified: boolean;
  helpful: number;
  notHelpful: number;
  userVote?: 'helpful' | 'not_helpful';
  images?: string[];
}

interface EventReviewsProps {
  eventId: string;
  eventTitle?: string;
}

const EventReviews: React.FC<EventReviewsProps> = ({ eventId, eventTitle }) => {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [newReview, setNewReview] = useState({
    rating: 0,
    title: '',
    comment: '',
  });
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'rating_high' | 'rating_low' | 'helpful'>('newest');
  const [filterRating, setFilterRating] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const currentUser = getCurrentUser();

  // Fetch reviews data from API
  useEffect(() => {
    const fetchReviews = async () => {
      try {
        // TODO: Replace with actual API call to fetch event reviews
        // const response = await reviewsApi.getEventReviews(eventId);
        // setReviews(response.reviews);
        
        // For now, show empty state - no more mock data
        setReviews([]);
      } catch (error) {
        console.error('Failed to fetch reviews:', error);
        setReviews([]);
      }
    };

    fetchReviews();
  }, [eventId]);

  const averageRating = reviews.length > 0 
    ? reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length 
    : 0;

  const ratingCounts = [5, 4, 3, 2, 1].map(rating => 
    reviews.filter(review => review.rating === rating).length
  );

  const handleSubmitReview = async () => {
    if (!currentUser) {
      toast({
        title: "Login required",
        description: "Please log in to submit a review",
        variant: "destructive",
      });
      return;
    }

    if (newReview.rating === 0 || !newReview.title.trim() || !newReview.comment.trim()) {
      toast({
        title: "Missing information",
        description: "Please provide a rating, title, and comment",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    
    try {
      // TODO: Replace with actual API call
      const review: Review = {
        id: Date.now().toString(),
        userId: currentUser.id,
        userName: currentUser.name || currentUser.email,
        userAvatar: currentUser.avatar,
        rating: newReview.rating,
        title: newReview.title,
        comment: newReview.comment,
        date: new Date().toISOString().split('T')[0],
        verified: false,
        helpful: 0,
        notHelpful: 0,
      };

      setReviews(prev => [review, ...prev]);
      setNewReview({ rating: 0, title: '', comment: '' });
      setShowForm(false);
      
      toast({
        title: "Review submitted",
        description: "Thank you for your feedback!",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to submit review. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVote = (reviewId: string, voteType: 'helpful' | 'not_helpful') => {
    if (!currentUser) {
      toast({
        title: "Login required",
        description: "Please log in to vote on reviews",
        variant: "destructive",
      });
      return;
    }

    setReviews(prev => prev.map(review => {
      if (review.id === reviewId) {
        const currentVote = review.userVote;
        let newHelpful = review.helpful;
        let newNotHelpful = review.notHelpful;
        let newUserVote: 'helpful' | 'not_helpful' | undefined = voteType;

        // Remove previous vote
        if (currentVote === 'helpful') newHelpful--;
        if (currentVote === 'not_helpful') newNotHelpful--;

        // Add new vote or remove if same
        if (currentVote === voteType) {
          newUserVote = undefined;
        } else {
          if (voteType === 'helpful') newHelpful++;
          if (voteType === 'not_helpful') newNotHelpful++;
        }

        return {
          ...review,
          helpful: newHelpful,
          notHelpful: newNotHelpful,
          userVote: newUserVote,
        };
      }
      return review;
    }));
  };

  const getSortedAndFilteredReviews = () => {
    let filtered = [...reviews];

    // Apply rating filter
    if (filterRating !== null) {
      filtered = filtered.filter(review => review.rating === filterRating);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.date).getTime() - new Date(a.date).getTime();
        case 'oldest':
          return new Date(a.date).getTime() - new Date(b.date).getTime();
        case 'rating_high':
          return b.rating - a.rating;
        case 'rating_low':
          return a.rating - b.rating;
        case 'helpful':
          return b.helpful - a.helpful;
        default:
          return 0;
      }
    });

    return filtered;
  };

  const renderStars = (rating: number, interactive = false, onStarClick?: (rating: number) => void) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 ${
              star <= rating 
                ? 'fill-yellow-400 text-yellow-400' 
                : 'text-gray-300'
            } ${interactive ? 'cursor-pointer hover:text-yellow-400' : ''}`}
            onClick={() => interactive && onStarClick?.(star)}
          />
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Reviews Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Reviews & Ratings</span>
            <Badge variant="secondary">{reviews.length} reviews</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Overall Rating */}
            <div className="text-center">
              <div className="text-4xl font-bold text-navy-blue mb-2">
                {averageRating.toFixed(1)}
              </div>
              {renderStars(Math.round(averageRating))}
              <p className="text-sm text-gray-600 mt-2">
                Based on {reviews.length} reviews
              </p>
            </div>

            {/* Rating Breakdown */}
            <div className="space-y-2">
              {[5, 4, 3, 2, 1].map((rating, index) => (
                <div key={rating} className="flex items-center gap-2">
                  <span className="text-sm w-8">{rating}★</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-yellow-400"
                      style={{ 
                        width: `${reviews.length > 0 ? (ratingCounts[index] / reviews.length) * 100 : 0}%` 
                      }}
                    />
                  </div>
                  <span className="text-sm text-gray-600 w-8">{ratingCounts[index]}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Write Review Section */}
      {currentUser && (
        <Card>
          <CardHeader>
            <CardTitle>Write a Review</CardTitle>
          </CardHeader>
          <CardContent>
            {!showForm ? (
              <Button onClick={() => setShowForm(true)} className="w-full">
                Share Your Experience
              </Button>
            ) : (
              <div className="space-y-4">
                <div>
                  <Label>Rating</Label>
                  <div className="mt-1">
                    {renderStars(newReview.rating, true, (rating) => 
                      setNewReview(prev => ({ ...prev, rating }))
                    )}
                  </div>
                </div>

                <div>
                  <Label htmlFor="review-title">Review Title</Label>
                  <Input
                    id="review-title"
                    placeholder="Summarize your experience"
                    value={newReview.title}
                    onChange={(e) => setNewReview(prev => ({ ...prev, title: e.target.value }))}
                  />
                </div>

                <div>
                  <Label htmlFor="review-comment">Your Review</Label>
                  <Textarea
                    id="review-comment"
                    placeholder="Tell others about your experience..."
                    rows={4}
                    value={newReview.comment}
                    onChange={(e) => setNewReview(prev => ({ ...prev, comment: e.target.value }))}
                  />
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={handleSubmitReview} 
                    disabled={isSubmitting}
                    className="flex-1"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit Review'}
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => setShowForm(false)}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Filters and Sorting */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <Select value={filterRating?.toString() || 'all'} onValueChange={(value) => 
            setFilterRating(value === 'all' ? null : parseInt(value))
          }>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Rating" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All ratings</SelectItem>
              <SelectItem value="5">5 stars</SelectItem>
              <SelectItem value="4">4 stars</SelectItem>
              <SelectItem value="3">3 stars</SelectItem>
              <SelectItem value="2">2 stars</SelectItem>
              <SelectItem value="1">1 star</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <SortDesc className="h-4 w-4" />
          <Select value={sortBy} onValueChange={(value: typeof sortBy) => setSortBy(value)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest first</SelectItem>
              <SelectItem value="oldest">Oldest first</SelectItem>
              <SelectItem value="rating_high">Highest rated</SelectItem>
              <SelectItem value="rating_low">Lowest rated</SelectItem>
              <SelectItem value="helpful">Most helpful</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Reviews List */}
      <div className="space-y-4">
        {getSortedAndFilteredReviews().map((review) => (
          <Card key={review.id}>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={review.userAvatar} />
                  <AvatarFallback>
                    {review.userName.split(' ').map(n => n[0]).join('').toUpperCase()}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{review.userName}</span>
                        {review.verified && (
                          <Badge variant="secondary" className="text-xs">
                            ✓ Verified
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {renderStars(review.rating)}
                        <span className="text-sm text-gray-500">
                          {new Date(review.date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-navy-blue mb-1">{review.title}</h4>
                    <p className="text-gray-700">{review.comment}</p>
                  </div>

                  {review.images && review.images.length > 0 && (
                    <div className="flex gap-2">
                      {review.images.map((image, index) => (
                        <img
                          key={index}
                          src={image}
                          alt={`Review image ${index + 1}`}
                          className="w-16 h-16 object-cover rounded-md cursor-pointer hover:opacity-80"
                        />
                      ))}
                    </div>
                  )}

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleVote(review.id, 'helpful')}
                        className={`gap-1 ${review.userVote === 'helpful' ? 'text-green-600' : ''}`}
                      >
                        <ThumbsUp className="h-4 w-4" />
                        Helpful ({review.helpful})
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleVote(review.id, 'not_helpful')}
                        className={`gap-1 ${review.userVote === 'not_helpful' ? 'text-red-600' : ''}`}
                      >
                        <ThumbsDown className="h-4 w-4" />
                        ({review.notHelpful})
                      </Button>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Flag className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {getSortedAndFilteredReviews().length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-gray-500">
              {reviews.length === 0 
                ? 'No reviews yet. Be the first to share your experience!' 
                : 'No reviews match your current filters.'
              }
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EventReviews;