import React from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import UserProfile from '@/components/UserProfile';

const Profile = () => {
  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8">
        <UserProfile />
      </main>
      <Footer />
    </div>
  );
};

export default Profile;