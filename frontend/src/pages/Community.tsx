import React from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import CommunityFeed from '@/components/CommunityFeed';
import PageTransition from '@/components/PageTransition';

const Community = () => {
  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream">
        <Header />
        <main className="flex-grow container mx-auto px-4 py-8">
          <CommunityFeed />
        </main>
        <Footer />
      </div>
    </PageTransition>
  );
};

export default Community;