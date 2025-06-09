import React from 'react';
import { Card, CardHeader, CardContent, CardTitle } from './ui/card';
import { DollarSign, TrendingUp, Target, Activity } from 'lucide-react';
import { Stats, ConversionMetrics } from '../pages/OrganizerDashboard';

interface Props {
  stats: Stats;
  conversionMetrics: ConversionMetrics | null;
  formatCurrency: (amount: number) => string;
}

const RevenueOverviewCards: React.FC<Props> = ({ stats, conversionMetrics, formatCurrency }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatCurrency(stats.bookings.total_revenue)}</div>
          <p className="text-xs text-muted-foreground">From {stats.bookings.total_bookings} bookings</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Your Revenue</CardTitle>
          <TrendingUp className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{formatCurrency(stats.bookings.organizer_revenue)}</div>
          <p className="text-xs text-muted-foreground">After 5% platform fee</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {conversionMetrics ? `${conversionMetrics.overall_conversion_rate}%` : '0%'}
          </div>
          <p className="text-xs text-muted-foreground">Views to bookings</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Events</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.events.approved}</div>
          <p className="text-xs text-muted-foreground">{stats.events.pending} pending review</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default RevenueOverviewCards;
